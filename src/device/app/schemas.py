from pydantic import BaseModel, Field

class ContentResponse(BaseModel):
    message: str = Field(..., description="Текст сообщения")
    created_at: str = Field(..., description="Время создания сообщения")
