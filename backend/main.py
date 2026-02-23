"""
Creative Master Backend Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creative Master Backend starting...")
    yield
    print("Creative Master Backend shutting down...")


app = FastAPI(
    title="Creative Master API",
    description="AI-powered creative inspiration management system",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Creative Master API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
