from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import os

from database import init_db
from routers import auth, saferoute, dashboard, blockchain, websockets, ai

app = FastAPI(title="EcoChain AI")

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
app.include_router(websockets.router)
app.include_router(ai.router)

@app.on_event("startup")
async def startup_event():
    await init_db()
    # Start the live traffic simulator background task
    asyncio.create_task(websockets.live_traffic_simulator())
    print("\nEcoChain AI Server running on http://localhost:3000")
    print("Admin credentials: admin@ecochain.ai / Admin@123")
    print("Blockchain ledger: active")
    print("Running on Python, FastAPI, MongoDB, Redis, and Scikit-learn\n")

# Serve static files from 'public' directory
app.mount("/css", StaticFiles(directory="public/css"), name="css")
app.mount("/js", StaticFiles(directory="public/js"), name="js")
app.mount("/img", StaticFiles(directory="public/img"), name="img")

# Route handlers for frontend HTML files
@app.get("/")
async def serve_index():
    return FileResponse("public/index.html")

@app.get("/login")
async def serve_login():
    return FileResponse("public/login.html")

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("public/dashboard.html")

@app.get("/saferoute")
async def serve_saferoute():
    return FileResponse("public/saferoute.html")

@app.get("/optimizer")
async def serve_optimizer():
    return FileResponse("public/optimizer.html")

@app.get("/wallet")
async def serve_wallet():
    return FileResponse("public/wallet.html")

@app.get("/leaderboard")
async def serve_leaderboard():
    return FileResponse("public/leaderboard.html")

@app.get("/admin")
async def serve_admin():
    return FileResponse("public/admin.html")
