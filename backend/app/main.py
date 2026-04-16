from fastapi import FastAPI
from app.routes.query import router

app = FastAPI()

app.include_router(router)