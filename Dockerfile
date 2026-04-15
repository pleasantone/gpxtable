FROM python:3-slim

# SERVE_MODE=gunicorn  — production (default)
# SERVE_MODE=dev       — Flask development server
ARG SERVE_MODE=gunicorn
ENV SERVE_MODE=${SERVE_MODE}

EXPOSE 8000
WORKDIR /app
COPY . .

RUN if [ "$SERVE_MODE" = "gunicorn" ]; then \
        pip install --no-cache-dir ".[gunicorn]"; \
    else \
        pip install --no-cache-dir ".[web]"; \
    fi

# exec replaces the shell so signals (SIGTERM/SIGINT) reach the server directly
CMD if [ "$SERVE_MODE" = "gunicorn" ]; then \
        exec gunicorn -w 4 --timeout 60 -b :8000 "src.gpxtable.wsgi:create_app()"; \
    else \
        exec python -m flask --app "src.gpxtable.wsgi:create_app()" run --host 0.0.0.0 --port 8000; \
    fi
