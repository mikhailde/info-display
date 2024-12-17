from pydantic import BaseModel, Field

class WeatherResponse(BaseModel):
    temperature: int = Field(..., description="Температура воздуха")
    condition: str = Field(..., description="Описание погодных условий")
    icon: str = Field(..., description="Ссылка на иконку погоды")

class WeatherData(WeatherResponse):
    updated_at: str = Field(..., description="Время обновления данных")
