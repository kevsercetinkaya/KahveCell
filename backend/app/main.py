from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app import models as _models
from app.api.v1.router import api_router
from app.db.session import Base, engine
from app.seed_data import seed_demo_data


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    yield


app = FastAPI(title="KahveCell API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=PlainTextResponse, tags=["Health"])
def read_home() -> str:
    return "çalışıyor"


app.include_router(api_router, prefix="/api/v1")