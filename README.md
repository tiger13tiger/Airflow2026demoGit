# Airflow 2026 Demo

A small, from-scratch Apache Airflow project for learning: what Airflow is,
how it's configured, and how to run/test it both locally and in GitHub
Actions.

Contributing changes? See [CONTRIBUTING.md](CONTRIBUTING.md) for the
branch/PR workflow this repo uses.

## Core concepts (the vocabulary you need)

- **DAG** (Directed Acyclic Graph): a Python file under `dags/` that
  declares a set of tasks and the order they run in. "Directed Acyclic"
  just means dependencies flow one way with no loops.
- **Task**: one unit of work inside a DAG, created by instantiating an
  **Operator** (e.g. `PythonOperator` runs a Python function,
  `BashOperator` runs a shell command). A running instance of a task on a
  given date is a **Task Instance**.
- **Scheduler**: the process that reads your DAG files, figures out which
  tasks are due to run, and hands them to the executor.
- **Executor**: decides *where* tasks actually run. `SequentialExecutor`
  (one task at a time, SQLite) is the default toy setup; `LocalExecutor`
  (parallel, needs Postgres/MySQL) is used in `docker-compose.yaml` here;
  `CeleryExecutor`/`KubernetesExecutor` scale out across machines in
  production.
- **Webserver**: serves the UI at `localhost:8080` where you see DAG runs,
  logs, and the UI for connections/variables.
- **Metadata DB**: where Airflow stores DAG run history, task state, etc.
  SQLite for the CI/toy setup, Postgres in `docker-compose.yaml`.
- **XCom**: a small key/value store Airflow uses to pass data between
  tasks (see `dags/etl_pipeline_dag.py`).

## Configuration, in order of precedence

Airflow configuration can come from (highest priority first):

1. Environment variables shaped `AIRFLOW__{SECTION}__{KEY}`, e.g.
   `AIRFLOW__CORE__EXECUTOR=LocalExecutor`. This is what the CI workflow
   and `docker-compose.yaml` use - no config file needed.
2. `airflow.cfg`, generated on first run inside `$AIRFLOW_HOME` (defaults
   to `~/airflow`, we point it elsewhere in CI).
3. Airflow's built-in defaults.

Two settings matter most for *this* repo:
- `AIRFLOW__CORE__DAGS_FOLDER` - tells Airflow where to look for DAG files
  (we point it at `./dags`).
- `AIRFLOW__CORE__EXECUTOR` - which executor to use.

## Project layout

```
dags/                       # Your DAGs. Airflow auto-discovers any .py file here.
  hello_world_dag.py        # Single-task DAG - start here.
  etl_pipeline_dag.py       # extract -> transform -> load, with XCom + retries.
tests/
  test_dag_validation.py    # DAG integrity tests (import errors, tags, retries).
docker-compose.yaml         # Postgres + LocalExecutor, for the real local UI.
.github/workflows/
  airflow-ci.yml            # Installs Airflow and runs the DAG in CI on every push.
```

## Running it locally with the real UI

```bash
cp .env.example .env
docker compose up airflow-init   # one-time: creates DB tables + admin user
docker compose up                # starts webserver + scheduler
```

Open http://localhost:8080 (login `airflow` / `airflow`), find `etl_pipeline`
in the DAG list, unpause it (the toggle on the left), and trigger a run
with the ▶ button. Click into a task to see its logs - this is the main
day-to-day Airflow workflow.

Stop everything with `docker compose down` (add `-v` to also wipe the
Postgres volume and start fresh next time).

## Running it without Docker (quick CLI check)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export AIRFLOW_HOME="$(pwd)/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
airflow db migrate
airflow dags list                       # confirms both DAGs are discovered
airflow dags test etl_pipeline 2024-01-01   # runs the whole DAG in one real run, prints logs
```

## How CI works (`.github/workflows/airflow-ci.yml`)

Running a full Airflow webserver in CI would be overkill. Instead the
workflow does what real Airflow projects do to catch problems before
merge:

1. Install Airflow pinned to a specific version + upstream "constraints"
   file (Airflow has many dependencies with narrow compatible version
   ranges - the constraints file is how the Airflow project itself pins a
   known-good combination).
2. `airflow db migrate` - sets up a throwaway SQLite metadata DB.
3. `airflow dags list-import-errors` - fails the build if any DAG file
   raises an exception on import (the #1 real-world Airflow CI failure).
4. `pytest tests/` - the DAG integrity tests.
5. `airflow dags test <dag> <date>` - actually *executes* every task in
   the DAG, in one real run, with no scheduler needed. This catches logic
   bugs "it imports fine" wouldn't, including broken XCom hand-offs
   between tasks (which is also why this uses `dags test` rather than
   calling `tasks test` once per task - each `tasks test` call gets its
   own throwaway run, so XComs pushed in one call aren't visible to the
   next).

This pattern (constraints file + `list-import-errors` + `dags test`)
scales to real production Airflow repos, just with more DAGs and tests.

## Suggested next steps as you learn

- Add a third DAG using `BashOperator` or the `@task` decorator (TaskFlow
  API) instead of `PythonOperator`.
- Add an Airflow **Connection** (e.g. to a public API) via the UI or
  `AIRFLOW_CONN_*` env var, and use `SimpleHttpOperator`/`requests` in a
  task.
- Try `schedule="*/10 * * * *"` on a DAG and watch the scheduler pick it
  up in the UI.
- Make a task fail on purpose and watch `retries`/`retry_delay` kick in.
