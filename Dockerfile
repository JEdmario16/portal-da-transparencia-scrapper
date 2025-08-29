FROM mcr.microsoft.com/playwright/python:v1.51.0-noble
WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction 

COPY . .

CMD ["sh", "fastapi.sh"]
