"""Dev runner — start the Fanar API in test mode: in-memory event store + audit, local reference
data, and a dev principal (maker/checker) since no IdP is configured. No Postgres/Keycloak needed.

    python run_dev.py       # http://127.0.0.1:8000   (Swagger UI at /docs)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
os.environ.setdefault("FANAR_ENV", "test")           # in-memory stores
os.environ.setdefault("FANAR_COOKIE_SECURE", "false")  # dev: cookies over http

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fanar.api.app:app", host="127.0.0.1", port=8000, reload=False)
