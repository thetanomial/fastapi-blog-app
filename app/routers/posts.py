from fastapi import Depends, Path,APIRouter, Request
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi.exceptions import HTTPException
from ..models import Posts
from ..database import SessionLocal 
from starlette import status
from .auth import get_current_user
from starlette.responses import RedirectResponse
from pydantic import BaseModel,Field
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(
    prefix="/posts",
    tags = ['posts']
)



def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

class PostRequest(BaseModel):
    title : str = Field(
        min_length=3,
        
    )
    description : str = Field(
        min_length=3,
        max_length=100
    )
    priority : int = Field(
        gt = 0,
        lt = 6
    )
    is_published : bool


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page",status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key='access_token')
    return redirect_response

### pages ### 

@router.get("/post-page")
async def render_post_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()

        posts = db.query(Posts).filter(Posts.author_id == user.get("id")).all()

        return templates.TemplateResponse("post.html", {"request": request, "posts": posts, "user": user})

    except Exception as e:
        print(e)
        return redirect_to_login()


@router.get('/add-post-page')
async def render_add_post_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()
        
        return templates.TemplateResponse("add-post.html",{"request":request,"user":user})
    except:
        return redirect_to_login()

@router.get('/edit-post-page/{post_id}')
async def render_edit_post_page(request: Request, db: db_dependency,post_id: int = Path(gt=0)):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        print(user)

        if user is None:
            return redirect_to_login()
        
        post_model = db.query(Posts).filter(Posts.id == post_id).filter(Posts.author_id == user.get('id')).first()
        
        return templates.TemplateResponse("edit-post.html",{"request":request,"user":user,'post':post_model})
    except:
        return redirect_to_login()



### endpoints ###



@router.get("/",status_code=status.HTTP_200_OK)
async def read_all(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(
            status_code=401,detail ='Authentication Failed'
        )
    return db.query(Posts).filter(
        Posts.author_id == user.get('id')
    ).all()

@router.get("/post/{post_id}",status_code=status.HTTP_200_OK)
async def read_todo(user:user_dependency,db:db_dependency,post_id:int = Path(
    gt = 0
)):
    
    if user is None:
        raise HTTPException(
            status_code=401,detail ='Authentication Failed'
        )
    
    print(user)
    
    post_model = db.query(Posts).filter(
        Posts.id == post_id,
        
    ).filter(Posts.author_id == user.get('id')).first()

    

    if post_model is not None:
        return post_model 
    raise HTTPException(
        status_code = 404,
        detail = 'Post not found'
    )



@router.post("/post",status_code=status.HTTP_201_CREATED)
async def create_post(user:user_dependency,db:db_dependency,post_request:PostRequest):
    if user is None:
        raise HTTPException(
            status_code=401,
            detail = 'Authorization Failed.'
        )
    post_model = Posts(
        **post_request.dict(),
        author_id = user.get('id')
    )
    db.add(post_model)
    db.commit()


@router.put("/post/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_post(
    user:user_dependency,
    db: db_dependency,
    post_request: PostRequest,
    post_id: int = Path(gt=0)
):
    
    if user is None:
        raise HTTPException(
            status_code=401,detail ='Authentication Failed'
        )


    post_model = db.query(Posts).filter(
        Posts.id == post_id
    )\
    .filter(Posts.author_id == user.get('id')).first()

    if post_model is None:
        raise HTTPException(
            status_code=404,
            detail = "Post not found"
        )
    
    post_model.title = post_request.title
    post_model.description = post_request.description
    post_model.priority = post_request.priority
    post_model.is_published = post_request.is_published

    db.add(post_model)
    db.commit()
    

@router.delete("/post/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(user:user_dependency,db:db_dependency,post_id:int = Path(gt = 0)):
    if user is None:
        raise HTTPException(
            status_code=401,detail ='Authentication Failed'
        )

    post_model = db.query(
        Posts
    ).filter(
        Posts.id == post_id,
        Posts.author_id == user.get('id') 
    ).first()

    print(post_model)

    if post_model is None:
        raise HTTPException(
            status_code=404,
            detail = 'Post not found'
        )

    db.query(Posts).filter(Posts.id == post_id).filter(Posts.author_id == user.get('id')).delete()
    db.commit()