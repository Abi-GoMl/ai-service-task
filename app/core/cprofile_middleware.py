import cProfile
import io
import os
import pstats
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

PROFILE_OUTPUT_DIR = "cprofile_results"

class CProfileMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware for profiling incoming HTTP requests using cProfile.
    Triggered when:
      - Request query parameter 'profile=true' is passed, OR
      - Request header 'X-Profile: true' is present, OR
      - Environment variable 'ENABLE_CPROFILE' is set to 'true'.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        profile_enabled = (
            request.query_params.get("profile", "").lower() == "true"
            or request.headers.get("X-Profile", "").lower() == "true"
            or os.getenv("ENABLE_CPROFILE", "").lower() == "true"
        )

        if not profile_enabled:
            return await call_next(request)

        profiler = cProfile.Profile()
        profiler.enable()

        start_time = time.perf_counter()
        response = await call_next(request)
        end_time = time.perf_counter()

        profiler.disable()

        # Ensure output directory exists
        os.makedirs(PROFILE_OUTPUT_DIR, exist_ok=True)

        # Generate unique filename for profile dump
        endpoint_clean = request.url.path.strip("/").replace("/", "_") or "root"
        timestamp = int(time.time() * 1000)
        prof_filename = os.path.join(
            PROFILE_OUTPUT_DIR, f"req_{endpoint_clean}_{timestamp}.prof"
        )

        # Save raw cProfile stats binary file
        profiler.dump_stats(prof_filename)

        # Generate text summary
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats(pstats.SortKey.CUMULATIVE)
        stats.print_stats(15)
        summary = stream.getvalue()

        # Write human readable summary to log file
        txt_filename = os.path.join(
            PROFILE_OUTPUT_DIR, f"req_{endpoint_clean}_{timestamp}.txt"
        )
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(f"cProfile Results for {request.method} {request.url.path}\n")
            f.write(f"Total Execution Time: {(end_time - start_time) * 1000:.2f} ms\n\n")
            f.write(summary)

        # Add profile filepath to response headers for developer visibility
        response.headers["X-CProfile-File"] = prof_filename
        response.headers["X-CProfile-Duration-Ms"] = f"{(end_time - start_time) * 1000:.2f}"

        return response
