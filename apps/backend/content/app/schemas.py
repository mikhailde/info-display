from pydantic import BaseModel, Field
from datetime import datetime

class ContentBase(BaseModel):
    message: str = Field(..., description="Текст сообщения", examples=["Пример сообщения"])

class ContentCreate(ContentBase):
    pass

class Content(ContentBase):
    id: int = Field(..., description="ID сообщения", examples=[1])
    created_at: datetime = Field(..., description="Время создания", examples=["2023-11-20T16:21:28.523Z"])

    class Config:
        from_attributes = True
