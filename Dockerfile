FROM python:3.13-alpine

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev curl

WORKDIR /app

COPY ./requirements.txt ./
RUN pip install --upgrade pip  --no-cache-dir
RUN pip install -r requirements.txt  --no-cache-dir
# Only for production
RUN pip install gunicorn  --no-cache-dir

COPY ./src ./

RUN adduser -u 5678 --disabled-password --gecos "" appuser 
RUN chown -R appuser /app
USER appuser

HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "marcus.main:api", "--bind", "0.0.0.0:8000"]



