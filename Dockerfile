FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install flask

EXPOSE 8899

CMD ["python3", "api_server.py"]
