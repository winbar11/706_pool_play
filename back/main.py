from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging

from database.db import init_db
from routers import auth, teams, leaderboard, admin, golfers
from scheduler.scheduler import refresh_scores

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Run end-of-round score refresh — schedule for ~7pm ET each tournament day
    scheduler.add_job(refresh_scores, "cron", day_of_week="thu,fri,sat,sun",
                        hour=19, minute=0, timezone="America/New_York", id="score_refresh")
    scheduler.start()
    logger.info("Scheduler started. Score refresh runs nightly at 7pm ET Thu-Sun.")
    yield
    scheduler.shutdown()

app = FastAPI(title="Masters Pool", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://706poolplay.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(golfers.router, prefix="/api/golfers", tags=["golfers"])

@app.get("/api/health")
def health():
    return {"status": "ok"}