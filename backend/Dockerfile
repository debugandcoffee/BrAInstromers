FROM python:3.12-slim

WORKDIR /app/backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

COPY entrypoint.sh .
COPY ingestion.sh .

RUN chmod +x entrypoint.sh
RUN chmod +x ingestion.sh
CMD ["./entrypoint.sh"]
