import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from api.forms import router as forms_router
from api.processes import router as processes_router
from api.simulation import router as simulation_router
from api.statistics import router as statistics_router
from services.sla_checker import sla_check_loop

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(sla_check_loop())
    yield
    task.cancel()


app = FastAPI(title="FlowForge", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware_hook(request: Request, call_next):
    response: Response = await call_next(request)
    return response


app.include_router(forms_router)
app.include_router(processes_router)
app.include_router(simulation_router)
app.include_router(statistics_router)


@app.get("/")
def root():
    return {"message": "FlowForge API is running"}
