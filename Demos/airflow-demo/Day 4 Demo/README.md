# Airflow + Postgres Demo

A tiny but real example: Airflow runs a 2-task pipeline that reads from a
database, summarises it, and writes the result back to another table.

```
extract_totals  ──►  write_summary
   (read sales)        (insert one summary row)
```

## What's in this folder

| File | What it is |
|------|-----------|
| `docker-compose.yml` | Defines all the containers (Airflow + 2 Postgres DBs) |
| `init-app-db.sql`    | Seeds our app database with fake sales data on first run |
| `dags/sales_summary_dag.py` | The actual Airflow pipeline (the "DAG") |

## The mental model (explain this to learners first)

There are **two separate databases** and that trips people up:

- **airflow-db** — Airflow's own bookkeeping DB. It tracks which tasks ran,
  when, and whether they succeeded. You never touch it directly.
- **app-db** — *your* application's database. This is the "real" data. Our
  pipeline reads from and writes to this one.

And there are **three Airflow containers**:

- **airflow-init** — runs once to set up tables + an admin login, then exits.
- **airflow-webserver** — the UI you open in your browser.
- **airflow-scheduler** — the "brain" that actually runs tasks on schedule.

---

## Step-by-step

### 1. Start everything

```bash
docker compose up
```

First run pulls images and may take a few minutes. You'll see lots of logs
from all the containers interleaved — that's normal. Wait until the noise
settles and you see the webserver reporting it's listening.

> **What just happened:** Compose started both Postgres databases, waited for
> their healthchecks to pass, ran `airflow-init` to create the metadata tables
> and admin user, then started the webserver and scheduler.

### 2. Open the Airflow UI

Go to **http://localhost:8080**

Log in with:
- Username: `admin`
- Password: `admin`

You'll see one DAG: **sales_summary**. It's paused by default (toggle on the left).

### 3. Look before you run

Click the **sales_summary** DAG, then the **Graph** view. You'll see the two
tasks connected by an arrow:

```
extract_totals  ──►  write_summary
```

This is the dependency in action: `write_summary` cannot start until
`extract_totals` succeeds.

### 4. Trigger it

- Unpause the DAG (toggle top-left).
- Click the **▶ (Trigger DAG)** button, top-right.

Watch both task boxes go from light green (running) to **dark green** (success)
in the Graph view. Click a task → **Logs** to see the `print()` output, e.g.
`Extracted: total=168.92, orders=6`.

### 5. Prove it actually wrote to the database

The app-db is exposed on host port **5433**, so you can query it directly:

```bash
docker compose exec app-db psql -U appuser -d appdb -c "SELECT * FROM sales_summary;"
```

You should see one row with the total, the order count, and a timestamp.
Trigger the DAG again → run the query again → a **second row** appears. That's
the pipeline doing real work against a real database.

### 6. Shut down

```bash
docker compose down            # stops containers, keeps the data
docker compose down -v         # also deletes the database volumes (clean slate)
```

---

## Likely questions from learners

**"Where did the `app_postgres` connection come from?"**
It's set via the `AIRFLOW_CONN_APP_POSTGRES` environment variable in the
compose file. Airflow turns any `AIRFLOW_CONN_<NAME>` variable into a usable
connection. In a real setup you'd add it through the UI under Admin → Connections.

**"What's XCom?"**
The way one task hands a small piece of data to the next. `extract_totals`
returns a dict; `write_summary` pulls it back with `xcom_pull`. Don't use it
for large data — just small values like our totals.

**"Why `schedule=None`?"**
So it only runs when you click Trigger — better for a demo. Change it to
`schedule="@daily"` to make it run automatically once a day, which is the
real-world use case.

**"Why two databases again?"**
Keeping Airflow's plumbing separate from business data is standard practice.
Mixing them is asking for trouble in production.
