"""
cProfile Runner for AI Service Desk
Runs cProfile profiling sessions on FastAPI application operations and outputs
detailed call statistics, CPU bottlenecks, and binary .prof stats files for visualization.
"""

import argparse
import asyncio
import cProfile
import io
import os
import pstats
import sys
from typing import Any, Callable, Dict, List

from httpx import ASGITransport, AsyncClient
from main import app
from app.db.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.deps import get_db

RESULTS_DIR = "cprofile_results"
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

class CProfiler:
    """
    Utility class for executing functions inside a cProfile profiling context,
    printing sorted stats summaries, and exporting .prof files.
    """

    def __init__(self, name: str, output_dir: str = RESULTS_DIR):
        self.name = name
        self.output_dir = output_dir
        self.profiler = cProfile.Profile()
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Executes a synchronous function under cProfile."""
        self.profiler.enable()
        try:
            return func(*args, **kwargs)
        finally:
            self.profiler.disable()

    async def run_async(self, async_func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Executes an asynchronous function under cProfile."""
        self.profiler.enable()
        try:
            return await async_func(*args, **kwargs)
        finally:
            self.profiler.disable()

    def print_and_save(self, sort_by: str = "cumulative", top_n: int = 20):
        """Prints formatted pstats and dumps binary .prof / txt output."""
        prof_file = os.path.join(self.output_dir, f"{self.name}.prof")
        txt_file = os.path.join(self.output_dir, f"{self.name}.txt")

        # Save binary profile data for snakeviz / pstats
        self.profiler.dump_stats(prof_file)

        # Build human-readable stats output
        stream = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats(sort_by)
        stats.print_stats(top_n)

        output_str = stream.getvalue()

        # Save text summary
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"==================================================\n")
            f.write(f" cProfile Execution Report: {self.name}\n")
            f.write(f" Sorted By: {sort_by} (Top {top_n} Calls)\n")
            f.write(f" Saved Binary: {prof_file}\n")
            f.write(f"==================================================\n\n")
            f.write(output_str)

        print(f"\n==================================================")
        print(f" cProfile Execution Report: {self.name}")
        print(f" Binary Profile: {prof_file}")
        print(f" Summary Text  : {txt_file}")
        print(f"==================================================")
        print(output_str[:1500])  # Print first snippet to terminal
        print(f"==================================================\n")


async def setup_test_environment():
    """Initializes in-memory database and yields AsyncClient."""
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return client, engine


# ----------------------------------------------------------------------
# Profiling Workload Functions
# ----------------------------------------------------------------------

async def profile_create_operations(client: AsyncClient, sort_by: str):
    """Profiles single and batch ticket creation using cProfile."""
    profiler = CProfiler("profile_create_tickets")

    async def _workload():
        # Single create
        await client.post("/tickets", json={"title": "cProfile Ticket 1", "priority": "high"})

        # Batch create
        for i in range(30):
            await client.post("/tickets", json={"title": f"cProfile Batch #{i}", "priority": "medium"})

    await profiler.run_async(_workload)
    profiler.print_and_save(sort_by=sort_by)


async def profile_read_operations(client: AsyncClient, sort_by: str):
    """Profiles reading single ticket, list all, and filtered list using cProfile."""
    # Seed data
    res = await client.post("/tickets", json={"title": "Target Read Ticket", "priority": "low"})
    ticket_id = res.json()["id"]

    for i in range(20):
        await client.post("/tickets", json={"title": f"Seed Read Ticket #{i}", "priority": "high" if i % 2 == 0 else "low"})

    profiler = CProfiler("profile_read_tickets")

    async def _workload():
        # Read by ID
        await client.get(f"/tickets/{ticket_id}")
        # List all
        await client.get("/tickets")
        # Filtered list
        await client.get("/tickets?priority=high")

    await profiler.run_async(_workload)
    profiler.print_and_save(sort_by=sort_by)


async def profile_update_operations(client: AsyncClient, sort_by: str):
    """Profiles single and batch ticket updating using cProfile."""
    created_ids = []
    for i in range(25):
        r = await client.post("/tickets", json={"title": f"Update Ticket #{i}", "priority": "low"})
        created_ids.append(r.json()["id"])

    profiler = CProfiler("profile_update_tickets")

    async def _workload():
        for tid in created_ids:
            await client.patch(f"/tickets/{tid}", json={"status": "in_progress", "title": "Updated via cProfile"})

    await profiler.run_async(_workload)
    profiler.print_and_save(sort_by=sort_by)


async def profile_delete_operations(client: AsyncClient, sort_by: str):
    """Profiles ticket deletion using cProfile."""
    created_ids = []
    for i in range(25):
        r = await client.post("/tickets", json={"title": f"Delete Ticket #{i}", "priority": "high"})
        created_ids.append(r.json()["id"])

    profiler = CProfiler("profile_delete_tickets")

    async def _workload():
        for tid in created_ids:
            await client.delete(f"/tickets/{tid}")

    await profiler.run_async(_workload)
    profiler.print_and_save(sort_by=sort_by)


async def run_all_profiles(sort_by: str = "cumulative"):
    """Runs all cProfile profiling tasks sequentially."""
    print(f"Starting cProfile profiling session (Results -> ./{RESULTS_DIR}/)...")
    client, engine = await setup_test_environment()
    try:
        print("\n[1/4] Profiling CREATE Operations...")
        await profile_create_operations(client, sort_by)

        print("\n[2/4] Profiling READ Operations...")
        await profile_read_operations(client, sort_by)

        print("\n[3/4] Profiling UPDATE Operations...")
        await profile_update_operations(client, sort_by)

        print("\n[4/4] Profiling DELETE Operations...")
        await profile_delete_operations(client, sort_by)

        print("\n[SUCCESS] cProfile profiling complete! Check the 'cprofile_results/' directory for .prof binary & .txt reports.")
    finally:
        await client.aclose()
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Run cProfile profiling for AI Service Desk API")
    parser.add_argument(
        "--op",
        choices=["all", "create", "read", "update", "delete"],
        default="all",
        help="Operation to profile (default: all)"
    )
    parser.add_argument(
        "--sort",
        choices=["cumulative", "time", "calls", "name"],
        default="cumulative",
        help="Sorting criteria for pstats (default: cumulative)"
    )

    args = parser.parse_args()

    async def _main():
        client, engine = await setup_test_environment()
        try:
            if args.op == "create":
                await profile_create_operations(client, args.sort)
            elif args.op == "read":
                await profile_read_operations(client, args.sort)
            elif args.op == "update":
                await profile_update_operations(client, args.sort)
            elif args.op == "delete":
                await profile_delete_operations(client, args.sort)
            else:
                await run_all_profiles(args.sort)
        finally:
            await client.aclose()
            await engine.dispose()

    asyncio.run(_main())


if __name__ == "__main__":
    main()
