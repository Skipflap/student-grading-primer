# Backend + Database: Step-by-Step Guide

This guide walks through how the backend Flask app runs and connects to the PostgreSQL database, and how to verify everything works.

---

## 1. How the backend connects to the database

### 1.1 Connection is driven by environment variables

The backend **never hardcodes** database credentials. Instead, `backend/db.py` reads them from the environment at runtime:

```python
# backend/db.py (do not modify)
def _connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],      # e.g. "db" (the service name in Docker)
        database=os.environ["DB_NAME"],  # e.g. "marksdb"
        user=os.environ["DB_USER"],      # e.g. "marksuser"
        password=os.environ["DB_PASSWORD"],
    )
```

So for the backend to connect, **four environment variables must be set**: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.

### 1.2 Where those variables come from in Docker

In `docker-compose.yml`, the `backend` service is configured with an `environment` block. Docker Compose injects these as environment variables into the backend container when it starts:

```yaml
backend:
  build: ./backend
  environment:
    DB_HOST: db          # "db" is the name of the database service in this compose file
    DB_NAME: marksdb     # must match POSTGRES_DB in the db service
    DB_USER: marksuser   # must match POSTGRES_USER
    DB_PASSWORD: markspass  # must match POSTGRES_PASSWORD
  depends_on:
    - db
  ports:
    - "5000:5000"
```

- **`DB_HOST: db`** — In Docker Compose, services talk to each other by **service name**. The Postgres container is named `db`, so the backend uses hostname `db` to reach it (Docker’s internal DNS).
- **`DB_NAME`, `DB_USER`, `DB_PASSWORD`** — These must match the `POSTGRES_*` variables defined under the `db` service so the backend can log in and use the same database.

### 1.3 Why `depends_on: - db` matters

`depends_on` ensures Docker starts the `db` container before the `backend` container. That way, when the backend starts and tries to connect, Postgres is already listening. It does **not** wait for Postgres to be “ready” to accept connections (for that you’d need a health check); in practice the short delay is usually enough.

---

## 2. How the backend is built and run

### 2.1 Backend Dockerfile (`backend/Dockerfile`)

- **Base image**: `python:3.11-slim` — gives you Python and pip.
- **Working directory**: `/app` — all commands and the app run here.
- **Dependencies**: `requirements.txt` is copied and installed (`flask`, `psycopg2-binary`, `flask_cors`).
- **App code**: `app.py` and `db.py` are copied into the image.
- **Port**: `EXPOSE 5000` — documents that the app listens on 5000.
- **Command**: `CMD ["python", "app.py"]` — running the container starts the Flask app.

So when you run the backend container, it executes `python app.py`, which binds to `0.0.0.0:5000` (all interfaces inside the container). Mapping `5000:5000` in compose exposes that port on your host as `http://localhost:5000`.

### 2.2 Database initialisation (`db/init.sql`)

The `db` service mounts `./db/init.sql` into the Postgres image’s init directory:

```yaml
volumes:
  - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
  - postgres_data:/var/lib/postgresql/data
```

- **Init script**: When the Postgres container runs for the **first time** with an empty data volume, it runs any `.sql` files in `/docker-entrypoint-initdb.d/`. So `init.sql` creates the `students` table and inserts the initial rows.
- **Persistence**: The named volume `postgres_data` is mapped to `/var/lib/postgresql/data`, so database data survives container restarts and rebuilds.

---

## 3. Step-by-step: Get the backend up and running

### Step 1: Ensure Docker is running

Make sure Docker Desktop (or your Docker engine) is running.

### Step 2: From the project root, build and start all services

```bash
docker compose up --build
```

- **`up`** — Creates and starts the `db`, `backend`, and `frontend` containers (and `automark` only when using the debug profile).
- **`--build`** — Rebuilds images so any changes to `backend/` or `frontend/` are included.

On first run you should see the db run the init script, for example:

```text
db-1  | /usr/local/bin/docker-entrypoint.sh: running /docker-entrypoint-initdb.d/init.sql
```

### Step 3: Check that the backend is running and connected

1. **Health check (no database involved)**  
   Open in a browser or with `curl`:
   ```text
   http://localhost:5000/
   ```
   You should see: `{"status":"ok"}`.

2. **Students from the database (proves connection)**  
   Open:
   ```text
   http://localhost:5000/students
   ```
   You should see JSON for the four students from `init.sql` (Alice, Bob, Charlie, Dana). If you do, the backend is successfully connecting to the database and calling `db.get_all_students()`.

### Step 4: Optional — run the automark sanity check

With the stack still running (or after starting it), in another terminal:

```bash
docker compose --profile debug up --build automark
```

You should see **`SANITY CHECK PASSED`** once the backend and DB wiring are correct.

---

## 4. Quick reference: request flow

1. You hit `http://localhost:5000/students`.
2. Docker routes port 5000 on your machine to the backend container’s port 5000.
3. Flask receives the request and runs `get_students()` in `app.py`.
4. `get_students()` calls `db.get_all_students()`.
5. `db.get_all_students()` uses `_connection()` to open a connection to host `db` (the Postgres container) using the environment variables.
6. It runs `SELECT id, name, course, mark FROM students ORDER BY id` and returns the rows as a list of dicts.
7. Flask returns that list as JSON with status 200.

That’s the full path from HTTP request to database and back.

---

## 5. Troubleshooting

| Symptom | What to check |
|--------|----------------|
| Backend won’t start / connection errors | Ensure `docker-compose.yml` has the correct `environment` for `backend` and that `DB_HOST` is `db`. |
| “No such table: students” | Ensure `./db/init.sql` is mounted under `/docker-entrypoint-initdb.d/` and that you’ve rebuilt/restarted the db (or removed the volume so init runs again). |
| Port 5000 in use | Change the host port in compose, e.g. `"5001:5000"`, and use `http://localhost:5001` for the backend. |
| Changes to `app.py` not reflected | Run `docker compose up --build` so the backend image is rebuilt. |

You’re now ready to implement the remaining routes (POST, PUT, DELETE, GET /stats) in `app.py` using the other functions in `db.py`.
