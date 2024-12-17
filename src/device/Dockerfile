FROM python:alpine

WORKDIR /app

COPY requirements.txt .
RUN apk add --no-cache netcat-openbsd
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
