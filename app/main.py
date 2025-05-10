from fastapi import FastAPI, Depends, Path,Request
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi.exceptions import HTTPException

from .models import Base 
from .database import engine, SessionLocal 
from starlette import status

from pydantic import BaseModel,Field
from .routers import auth,posts, admin, users
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.get("/healthy")
def health_check():
    return {'status':'healthy'}

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static",StaticFiles(directory="app/static"),name='static')

@app.get("/")
def test(request:Request):
    return templates.TemplateResponse("home.html",{'request':request})

app.include_router(
    auth.router
)

app.include_router(
    posts.router
)
app.include_router(
    admin.router
)
app.include_router(
    users.router
)
