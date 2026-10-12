FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --create-home app && mkdir /app/data && chown app:app /app/data
USER app
EXPOSE 8000
ENTRYPOINT ["creditflow"]
