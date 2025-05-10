from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from ..database import Base
from ..main import app 
from ..routers.posts import get_db,get_current_user
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from ..models import Posts

SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db" 

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # ✅ Correct: Using a boolean value
    poolclass=StaticPool
)


TestingSessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    
    finally:
        db.close()

def override_get_current_user():
    return {
        'username' : 'mkpgtr',
        'id' : 1,
        'user_role' : 'admin'
    }

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


client = TestClient(app)

@pytest.fixture
def test_post():
    post = Posts(
        title = "Mastering FastAPI workflow.",
        description = "Understanding how FastAPI works.",
        priority = 5,
        author_id = 1,
        is_published = False
    )

    db = TestingSessionLocal()
    db.add(post)
    db.commit()
    yield db
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM posts;"))
        connection.commit()

def test_read_all_authenticated(test_post):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{'title' : "Mastering FastAPI workflow.",'description':"Understanding how FastAPI works.",'id':1,'priority':5,'author_id' : 1,'is_published':False}]

def test_read_one_authenticated(test_post):
    response = client.get("/post/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'title' : "Mastering FastAPI workflow.",'description':"Understanding how FastAPI works.",'id':1,'priority':5,'author_id' : 1,'is_published':False}

def test_read_one_authenticated(test_post):
    response = client.get("/post/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail':'Post not found'}



def test_create_todo(test_post):
    request_data  = {
        'title' : "New post",
        "description" : "New todo description",
        "priority" : 5,
        "is_published" : False,
        "author_id" : 1
    }

    respose = client.post('/post/',json=request_data)
    assert respose.status_code == 201

    db = TestingSessionLocal()
    model = db.query(Posts).filter(Posts.id == 2).first()
    assert model.title ==request_data.get('title')
    assert model.description ==request_data.get('description')
    assert model.author_id ==request_data.get('author_id')
    assert model.priority ==request_data.get('priority')
    assert model.is_published ==request_data.get('is_published')