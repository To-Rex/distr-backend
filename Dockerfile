FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN apt update && apt install -y postgresql-client

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]