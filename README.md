# Wedding RSVP – Multi-Container App (FastAPI + PostgreSQL + Docker Compose)

A small multi-container application. Guests submit an RSVP (name, surname, whether
they attend, how many people come). The backend stores it in PostgreSQL and can
read it back. Schema changes are managed with Alembic migrations.

## Architecture

```
   host                         Docker network "app-net"
┌──────────┐  :8000   ┌────────────────────┐        ┌──────────────────┐
│ browser /│ ───────► │  backend (FastAPI) │ ─────► │  db (PostgreSQL) │
│ curl     │          │  uvicorn, SQLAlchemy│  5432 │  16              │
└──────────┘          └────────────────────┘        └────────┬─────────┘
   psql :5433 ─────────────────────────────────────────────►│
                                                    named volume "pgdata"
```

| Service   | Image / build        | Host port | Purpose                              |
|-----------|----------------------|-----------|--------------------------------------|
| `backend` | built from `Dockerfile` | 8000   | REST API; runs migrations on start   |
| `db`      | `postgres:16`        | 5433      | Relational database (data in `pgdata`) |

Key points:

- **Startup order:** `db` has a `pg_isready` healthcheck; `backend` uses
  `depends_on: condition: service_healthy`, so the API starts only when the DB accepts connections.
- **Networking:** both services share the `app-net` network; the backend reaches the DB by
  its service name (`DB_HOST=db`, port 5432). Port 5433 on the host is only for inspecting the DB with `psql`.
- **Persistence:** DB files live in the named volume `pgdata`, so data survives
  `docker compose down` and container re-creation.
- **Migrations:** the backend container runs `alembic upgrade head` before starting uvicorn, creating the tables automatically.

## Project structure

```
.
├── docker-compose.yaml        # services, network, volume
├── Dockerfile                 # backend image
├── .env.example               # template for configuration (committed)
├── .env                       # real configuration (NOT committed)
├── .dockerignore / .gitignore
├── requirements.txt
├── main.py                    # FastAPI app
├── routers/registration.py    # API endpoints (CRUD)
├── API.md                     # API documentation
├── postman/                   # exported Postman collection
├── orm/
│   ├── database.py            # engine, session, Base (config from env vars)
│   └── models.py              # SQLAlchemy models
├── pydantic_models/
│   ├── request/               # input validation
│   └── response/              # output schemas
├── alembic.ini
└── alembic/                   # migration environment
    └── versions/              # migration scripts
```

## Configuration and secrets

All configuration is read from environment variables. No credentials are in the
source code, and `.env` is excluded by both `.gitignore` and `.dockerignore`.

| Variable            | Description                          | Example (`.env.example`) |
|---------------------|--------------------------------------|--------------------------|
| `POSTGRES_USER`     | DB user (created on first DB start)  | `wedding_user`           |
| `POSTGRES_PASSWORD` | DB password                          | `change_me`              |
| `POSTGRES_DB`       | DB name                              | `wedding`                |
| `DB_HOST`           | DB hostname seen by the backend      | `db`                     |
| `DB_PORT`           | DB port seen by the backend          | `5432`                   |

> **Important:** Postgres reads `POSTGRES_USER` / `POSTGRES_PASSWORD` only when the
> `pgdata` volume is first created. If you change them later, run
> `docker compose down -v` (this **deletes all DB data**) to re-initialize.

## Getting started

Requirements: Docker with Docker Compose v2.

```bash
git clone <repo-url>
cd Assignment1
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
# edit .env and set a real POSTGRES_PASSWORD
docker compose up --build
```

The whole stack starts with that single command. When you see uvicorn
report it is running:

- API: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs

Stop with `Ctrl+C` or `docker compose down` (data is kept).

## API

Full reference: [API.md](API.md). Postman collection: [postman/Wedding_RSVP.postman_collection.json](postman/Wedding_RSVP.postman_collection.json)
(import it in Postman and run the requests in order).

| Method | Path                    | Description                | Success |
|--------|-------------------------|----------------------------|---------|
| GET    | `/`                     | Health check               | 200     |
| GET    | `/registration/`        | List all RSVPs             | 200     |
| GET    | `/registration/{id}`    | Get one RSVP               | 200     |
| POST   | `/registration/`        | Create an RSVP             | 201     |
| PUT    | `/registration/{id}`    | Update an RSVP             | 200     |
| DELETE | `/registration/{id}`    | Delete an RSVP             | 204     |

Validation rules: `name` and `surname` are 1-100 characters; `amount_of_people` is
0-10; if `attending` is `true` then `amount_of_people` must be at least 1; if
`attending` is `false` it is stored as 0. Unknown ids return 404.

```bash
curl -X POST http://localhost:8000/registration/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Aigerim", "surname": "Sadykova", "attending": true, "amount_of_people": 2}'
curl http://localhost:8000/registration/
```

## Verifying data persistence

```bash
docker compose up -d --build
curl -X POST http://localhost:8000/registration/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","surname":"User","attending":true,"amount_of_people":1}'

docker compose down            # removes containers, keeps the volume
docker compose up -d           # brand-new containers
curl http://localhost:8000/registration/1   # the record is still there
```

Do **not** use `docker compose down -v` for this test: `-v` deletes the volume.

## Inspecting the database

```bash
# Without any host port (uses the container's own psql)
docker compose exec db psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT * FROM registrations;"

# From the host (if you have psql installed), via the published port 5433
psql -h localhost -p 5433 -U <POSTGRES_USER> -d <POSTGRES_DB>
```

If you get `password authentication failed`, either you hit a different local
Postgres on port 5432 (use 5433), or the volume was created with older credentials
(see the note under *Configuration*).

## Database migrations (Alembic)

Alembic is configured in `alembic/env.py` to use the same environment variables and
the models in `orm/models.py`. Migrations run automatically on container start.

To change the schema:

1. Edit `orm/models.py`.
2. Generate a migration (the DB must be running; `./alembic/versions` is mounted
   into the container so the new file appears on your machine):
   ```bash
   docker compose up -d db
   docker compose run --rm backend alembic revision --autogenerate -m "describe change"
   ```
3. Review the generated file in `alembic/versions/`, then commit it.
4. Apply it: `docker compose up --build` (or `docker compose run --rm backend alembic upgrade head`).

Roll back one step: `docker compose run --rm backend alembic downgrade -1`.

## Useful commands

```bash
docker compose ps                  # service status and ports
docker compose logs -f backend     # follow backend logs
docker compose down                # stop, keep data
docker compose down -v             # stop AND delete the database volume
docker compose build --no-cache    # rebuild the backend image
```

## Docker requirements checklist

- [x] Backend with API endpoints that read **and** write to the database
- [x] PostgreSQL service
- [x] `docker-compose.yaml` with `backend` and `db`, ports, network, `depends_on` with healthcheck
- [x] Custom `Dockerfile` for the backend
- [x] Configuration via environment variables / `.env`; `.env.example` provided; no secrets in Git
- [x] Named volume `pgdata` for persistent data
- [x] `.dockerignore` and `.gitignore`
- [x] Entire app starts with `docker compose up`

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `port is already allocated` on 8000 or 5433 | Another process uses it; stop it or change the left side of the `ports` mapping |
| `password authentication failed` | See *Inspecting the database* |
| `relation "registrations" does not exist` | The migration did not run; check `docker compose logs backend` and that `alembic/versions/` contains the migration |
| Backend exits at start with `KeyError` | A variable is missing from `.env`; compare with `.env.example` |
