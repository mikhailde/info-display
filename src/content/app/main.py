import logging

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session

import models, schemas
from database import engine, SessionLocal

# Используем встроенный логгер Uvicorn, если он доступен
logger = logging.getLogger("uvicorn.error") if "uvicorn" in logging.root.manager.loggerDict else logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Content Management Service",
    description="Сервис для управления статическим контентом",
    version="0.1.0",
)

router = APIRouter(prefix="/api/v1")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/content/", response_model=schemas.Content, status_code=status.HTTP_201_CREATED)
async def create_content(content: schemas.ContentCreate, db: Session = Depends(get_db)):
    """Создает новый контент."""
    logger.info(f"Received request to create content: {content}")
    db_content = models.Content(message=content.message)
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    logger.info(f"Content created successfully: {db_content}")
    return db_content

@router.get("/content", response_model=schemas.Content) # убрал слэш на конце
async def read_latest_content(db: Session = Depends(get_db)):
    """Возвращает последний созданный контент."""
    logger.info("Received request to read latest content")
    content = db.query(models.Content).order_by(models.Content.id.desc()).first()
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    logger.info(f"Latest content retrieved successfully: {content}")
    return content

app.include_router(router)
