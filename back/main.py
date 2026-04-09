from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging

from database.db import init_db, get_conn
from routers import auth, teams, leaderboard, admin, golfers
from scheduler.scheduler import refresh_scores

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Refresh scores every 15 minutes, 8am–8pm ET on tournament days
    scheduler.add_job(refresh_scores, "cron", day_of_week="thu,fri,sat,sun",
                        hour="8-19", minute="0,15,30,45", timezone="America/New_York",
                        id="score_refresh")
    scheduler.add_job(refresh_scores, "cron", day_of_week="thu,fri,sat,sun",
                        hour="20", minute="0", timezone="America/New_York",
                        id="score_refresh_8pm")
    scheduler.start()
    logger.info("Scheduler started. Score refresh runs every 15 min, 8am-8pm ET Thu-Sun.")
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

@app.get("/api/settings")
def get_settings():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM tournament_settings")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {row["key"]: row["value"] for row in rows}