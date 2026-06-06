from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from api.forms import router as forms_router
from api.processes import router as processes_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FlowForge", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware_hook(request: Request, call_next):
    # Placeholder for future permission/auth implementation.
    # Insert authentication and authorization logic here.
    response: Response = await call_next(request)
    return response


app.include_router(forms_router)
app.include_router(processes_router)


@app.get("/")
def root():
    return {"message": "FlowForge API is running"}
