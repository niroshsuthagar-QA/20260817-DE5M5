-- ---------------------------------------------------------------------------
-- This script runs automatically the FIRST time app-db starts up.
-- (Postgres runs anything in /docker-entrypoint-initdb.d/ on a fresh volume.)
--
-- We create two tables:
--   sales    -> raw example data, as if our app had been recording orders
--   sales_summary -> EMPTY for now. Our Airflow DAG will fill this in.
-- ---------------------------------------------------------------------------

CREATE TABLE sales (
    id          SERIAL PRIMARY KEY,
    product     TEXT NOT NULL,
    amount      NUMERIC(10, 2) NOT NULL,
    sold_at     DATE NOT NULL
);

-- Some fake sales so the DAG has something to crunch.
INSERT INTO sales (product, amount, sold_at) VALUES
    ('Widget',  19.99, '2024-01-01'),
    ('Widget',  19.99, '2024-01-02'),
    ('Gadget',  49.50, '2024-01-02'),
    ('Gizmo',    9.95, '2024-01-03'),
    ('Gadget',  49.50, '2024-01-03'),
    ('Widget',  19.99, '2024-01-03');

-- The DAG will write one summary row here every time it runs.
CREATE TABLE sales_summary (
    id            SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMPTZ NOT NULL,
    total_sales   NUMERIC(12, 2) NOT NULL,
    order_count   INTEGER NOT NULL
);
