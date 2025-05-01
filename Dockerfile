FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flet requests jsonschema

EXPOSE 8550

CMD ["python", "main.py"]
