from fastapi import Depends, Path,APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi.exceptions import HTTPException
from ..models import Posts
from ..database import SessionLocal 
from starlette import status
from .auth import get_current_user

from pydantic import BaseModel,Field


router = APIRouter( 
    prefix="/admin",
    tags = ['admin']
    )






def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()



db_dependency = Annotated[
    Session,
    Depends(get_db)
]

user_dependency = Annotated[dict,Depends(get_current_user)]

@router.get('/todo',status_code=status.HTTP_200_OK)
async def read_all(user:user_dependency,db:db_dependency):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(
            status_code = 401,
            detail = 'Authentication Failed'
        )
    
    return db.query(
        Posts
    ).all()

@router.delete("/post/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_post\
(user:user_dependency,db:db_dependency,post_id:int = Path(gt=0)):
    print("hello")
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(
            status_code=401,
            detail='Authentication Failed',

        )
    
    post_model = db.query(Posts.id == post_id).first()

    if post_model is None:
        raise HTTPException(
            status_code=404,detail='Post not found'
        )
    
    db.query(Posts).filter(Posts.id == post_id).delete()
    db.commit()