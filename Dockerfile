FROM python:3.12-alpine

RUN apk add --no-cache tzdata

ENV PYTHONUNBUFFERED=1

WORKDIR /opt/pop3connector

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./

CMD ["python", "-u", "app.py"]