# Project overview

The service is a Python FastAPI application. `api/` holds the HTTP routes,
`core/` the domain logic, and `db/` the SQLAlchemy models. Tests live under
`tests/` and mirror the package layout.

Build with `make build`, run with `make dev`, and format with `ruff format`.
