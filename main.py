from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Request, status
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from slowapi.errors import RateLimitExceeded

from src.utils.healthchecker import router as healthchecker_router
from src.routes.v1.contacts import router as contacts_router
from src.routes.v1.auth import router as auth_router
from src.routes.v1.users import router as users_router
from src.database.db import sessionmanager

scheduler = AsyncIOScheduler()


async def cleanup_expired_tokens():
    async with sessionmanager.session() as db:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)
        stmt = text(
            "DELETE FROM refresh_tokens WHERE expired_at < now OR revoked_at IS NOT NULL AND revoked_at < :cutoff"
        )
        await db.execute(stmt, {"now": now, "cutoff": cutoff})
        await db.commit()
        print(f"Expire tokens cleaned up [{now.strftime('%Y-%m-%d %H:%M:%S')}]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(cleanup_expired_tokens, trigger="interval", hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="Contacts app v1.0",
    description="Contacts app v1.0",
    version="1.0",
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, ext: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Too many requests. Try late"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

routes = [healthchecker_router, contacts_router, auth_router, users_router]
for router in routes:
    app.include_router(router=router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
