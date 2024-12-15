import logging

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import models, schemas
from database import engine, SessionLocal

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/v1/content/", response_model=schemas.Content)
def create_content(content: schemas.ContentCreate, db: Session = Depends(get_db)):
    logger.info(f"Received request to create content: {content}")
    db_content = models.Content(message=content.message)
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    logger.info(f"Content created successfully: {db_content}")
    return db_content

@app.get("/api/v1/content/", response_model=schemas.Content)
def read_content(db: Session = Depends(get_db)):
    logger.info("Received request to read latest content")
    content = db.query(models.Content).order_by(models.Content.id.desc()).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    logger.info(f"Latest content retrieved successfully: {content}")
    return content
