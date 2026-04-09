# Streamlit in Snowflake + Snowflake Postgres Workshop

A multi-page Streamlit app running in Snowflake's container runtime that connects to a Snowflake Postgres instance, visualizes e-commerce data, and integrates Cortex AI features.

## Pages

- **Dashboard** - KPI cards, monthly revenue chart, top customers, orders by region
- **Data Explorer** - Interactive table browser with column selection and text filtering
- **Chart Builder** - Describe a chart in plain English; Cortex AI generates SQL and an Altair chart
- **Chatbot** - Multi-turn AI conversation about your data, powered by Snowflake Cortex

## Project Structure

```
sis-pg-workshop/
├── .streamlit/secrets.toml      # Postgres credentials (placeholder values)
├── pyproject.toml               # pip dependencies for container runtime
├── requirements.txt             # Same deps in requirements.txt format
├── snowflake.yml                # Snow CLI deployment config
├── streamlit_app.py             # Main entry point with sidebar navigation
└── src/
    ├── __init__.py
    ├── cortex.py                # Snowpark session + Cortex COMPLETE wrapper
    ├── db.py                    # Postgres connection via st.secrets
    ├── dashboard.py             # Dashboard page
    ├── explorer.py              # Data Explorer page
    ├── chart_builder.py         # AI Chart Builder page
    └── chatbot.py               # AI Chatbot page
```

## Prerequisites

- Snowflake account with ACCOUNTADMIN (or equivalent) role
- Snowflake Postgres instance (created via Snowsight UI)
- Cortex AI enabled in your region
- A compute pool (e.g., `SYSTEM_COMPUTE_POOL_CPU`)
- Snow CLI v3.14+

## Setup

### 1. Create Snowflake Objects

Run these SQL statements in Snowsight (replace placeholder values with your own):

```sql
-- Database
CREATE DATABASE IF NOT EXISTS SIS_PG_WORKSHOP;
USE DATABASE SIS_PG_WORKSHOP;
USE SCHEMA PUBLIC;

-- Egress rule for Postgres connectivity
CREATE OR REPLACE NETWORK RULE SIS_PG_EGRESS_RULE
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('<your-postgres-host>:5432');

-- Egress rule for PyPI package installs
CREATE OR REPLACE NETWORK RULE SIS_PG_PYPI_RULE
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('pypi.org', 'pypi.python.org', 'pythonhosted.org', 'files.pythonhosted.org');

-- Secret for Postgres connection string
CREATE OR REPLACE SECRET SIS_PG_SECRET
  TYPE = GENERIC_STRING
  SECRET_STRING = 'postgresql://snowflake_admin:<your-password>@<your-postgres-host>:5432/postgres';

-- External Access Integration (includes both Postgres and PyPI rules)
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION SIS_PG_EAI
  ALLOWED_NETWORK_RULES = (SIS_PG_EGRESS_RULE, SIS_PG_PYPI_RULE)
  ALLOWED_AUTHENTICATION_SECRETS = (SIS_PG_SECRET)
  ENABLED = TRUE;
```

### 2. Configure Credentials

Edit `.streamlit/secrets.toml` with your Postgres connection details:

```toml
[postgres]
host = "<your-postgres-host>.postgres.snowflake.app"
port = 5432
dbname = "postgres"
user = "snowflake_admin"
password = "<your-password>"
```

### 3. Update snowflake.yml

Update the object names in `snowflake.yml` to match what you created in step 1:

```yaml
external_access_integrations:
  - SIS_PG_EAI
secrets:
  pg_secret: SIS_PG_SECRET
```

### 4. Seed Sample Data

Install `psycopg2-binary` locally and run the seed script (if provided) or manually create the e-commerce tables (`customers`, `products`, `orders`, `order_items`) in your Postgres instance.

### 5. Deploy

```bash
snow streamlit deploy --replace
```

The container typically takes 2-3 minutes to start and install dependencies on first deploy.

### 6. Open the App

```bash
snow streamlit get-url sis_pg_app
```

## Key Technical Details

- **Container runtime** (`SYSTEM$ST_CONTAINER_RUNTIME_PY3_11`) is required for `psycopg2-binary` and outbound Postgres connectivity
- **`runtime_name`** must be specified alongside `compute_pool` in `snowflake.yml`
- **PyPI network rule** is required so the container can install pip packages at startup
- **`pyproject.toml`** declares dependencies for the container runtime (not `environment.yml`, which is for warehouse runtime)
- **`snowflake-snowpark-python`** is not pre-installed in the container; it must be in `pyproject.toml`
- **Cortex AI** calls are made via `Session.builder.getOrCreate()` and Snowpark SQL
- **Postgres credentials** are stored in `.streamlit/secrets.toml` and accessed via `st.secrets` (the `_snowflake` module is not available in container runtime)
