from contextlib import asynccontextmanager
from time import perf_counter
 
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
 
from app.api.tickets import router as ticket_router
from app.core.exceptions import TicketNotFoundError
from app.db.database import init_db
 
from sqlalchemy import text
from app.db.database import AsyncSessionLocal
from fastapi.responses import JSONResponse
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
 
 
app = FastAPI(
    title="AI Service Desk",
    version="1.0.0",
    lifespan=lifespan,
)
 
 
@app.middleware("http")
async def add_response_time(
    request: Request,
    call_next,
):
    start_time = perf_counter()
 
    response = await call_next(request)
 
    end_time = perf_counter()
 
    elapsed_ms = (end_time - start_time) * 1000
 
    response.headers["X-Response-Time"] = (
        f"{elapsed_ms:.2f}ms"
    )
 
    return response
 
 
@app.exception_handler(TicketNotFoundError)
async def ticket_not_found_handler(
    request: Request,
    exc: TicketNotFoundError,
):
    return JSONResponse(
        status_code=404,
        content={
            "error": "ticket_not_found",
            "id": exc.ticket_id,
        },
    )
 
 
app.include_router(ticket_router)
 
 
@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Service Desk"
    }
 
 
 