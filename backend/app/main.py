from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .database.connection import init_db
from .routes import auth, saferoute, dashboard, blockchain, ai
from .websocket import handler

app = FastAPI(title="EcoChain AI", description="Decentralized Sustainable Transport Optimization")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(saferoute.router)
app.include_router(dashboard.router)
app.include_router(blockchain.router)
app.include_router(ai.router)
app.include_router(handler.router)

@app.on_event("startup")
async def startup_event():
    await init_db()
    asyncio.create_task(handler.live_traffic_simulator())
    print("\nEcoChain AI Professional Backend Active")
    print("API Documentation: http://localhost:3001/docs\n")

# Serve static files from 'public' directory
# Note: Assumes running uvicorn from the project root
app.mount("/css", StaticFiles(directory="public/css"), name="css")
app.mount("/js", StaticFiles(directory="public/js"), name="js")
app.mount("/img", StaticFiles(directory="public/img"), name="img")

@app.get("/")
async def serve_index(): return FileResponse("public/index.html")

@app.get("/login")
async def serve_login(): return FileResponse("public/login.html")

@app.get("/dashboard")
async def serve_dashboard(): return FileResponse("public/dashboard.html")

@app.get("/saferoute")
async def serve_saferoute(): return FileResponse("public/saferoute.html")

@app.get("/optimizer")
async def serve_optimizer(): return FileResponse("public/optimizer.html")

@app.get("/wallet")
async def serve_wallet(): return FileResponse("public/wallet.html")

@app.get("/leaderboard")
async def serve_leaderboard(): return FileResponse("public/leaderboard.html")

@app.get("/admin")
async def serve_admin(): return FileResponse("public/admin.html")
