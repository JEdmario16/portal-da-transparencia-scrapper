# etapa 1: COnstrução das dependências
from python:3.12-slim as base 
 
LABEL maintainer="Jose Edmario"


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1


WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-interaction 

# etapa 2: Copia o código fonte
COPY . .
RUN playwright install-deps
RUN playwright install chromium

# etapa 3: Executa o código
CMD ["sh", "fastapi.sh"]