FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY . .

RUN uv pip install --system --no-cache -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
