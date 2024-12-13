from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import models, schemas  # Импортируем из текущей директории
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Content Management Service",
    description="Сервис управления статическим контентом",
    version="0.1.0",
)

@app.post(
    "/api/v1/content",
    response_model=schemas.Content,
    status_code=status.HTTP_201_CREATED,
    tags=["Content"],
)
def create_content(content: schemas.ContentCreate, db: Session = Depends(get_db)):
    """
    Создание нового сообщения.

    - **message**: Текст сообщения.
    """
    try:
        db_content = models.Content(**content.model_dump())
        db.add(db_content)
        db.commit()
        db.refresh(db_content)
        return db_content
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Такое сообщение уже существует",
        )

@app.get("/api/v1/content", response_model=schemas.Content, tags=["Content"])
def read_content(db: Session = Depends(get_db)):
    """
    Получение последнего созданного сообщения.
    """
    content = db.query(models.Content).order_by(models.Content.created_at.desc()).first()
    if content:
        return content
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Сообщение не найдено"
    )