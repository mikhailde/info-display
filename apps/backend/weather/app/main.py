from fastapi import FastAPI

app = FastAPI(
    title="Weather Service",
    description="Сервис получения данных о погоде",
    version="0.1.0",
)

@app.get("/")
async def root():
    return {"message": "Weather Service is running"}