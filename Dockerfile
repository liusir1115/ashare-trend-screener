FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY frontend ./frontend
COPY strategy.example.toml ./
COPY strategy.plan_a.toml ./

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "ashare_strategy.server"]

