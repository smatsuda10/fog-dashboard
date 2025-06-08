# fog-dashboard


## Project Setup Summary for `fog_dashboard_dbt`

This document summarizes all setup steps and configurations completed for the `fog_dashboard_dbt` dbt project.

---

### 0. Project Background & Data Gathering

* **Goal:** Build a fog prediction dashboard using historical weather data.
* **Data Source Evaluation:**

  * Considered NOAA and other meteorological datasets.
  * Selected **NOAA Pacifica station (station ID: HAF)** for its coastal relevance.
* **Data Acquisition:**

  * Used IEM’s ASOS API endpoint: `https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py`.
  * Adapted a Python script (from IEM template) to:

    * Pull hourly data from **Aug 1, 2023 to Sep 1, 2024**.
    * Implement exponential backoff retries.
    * Save a `.csv` snapshot of weather data.
  * **Stations:** Pulled from `HAF` only (Pacifica).
  * **Future Work:** Plan to automate the API access for recurring updates instead of using a static snapshot.
* **Initial Cleaning:**

  * Used a `clean_csv` Python script to:

    * Convert timestamps.
    * Drop duplicates.
    * Replace missing values.
    * Ensure consistent schema for BigQuery upload.

---

### 1. GitHub Repository & Virtual Environment Setup

* Created a GitHub repo: `fog_dashboard_dbt`
* Initialized Python virtual environment (`.venv`) and installed `dbt` 1.9.6
* **Environment Conflict:**

  * Encountered issues where VSCode defaulted to Conda Python.
  * Fixed by:

    * Selecting `.venv/bin/python` manually in VSCode.
    * Deactivating Conda (`conda deactivate`).

---

### 2. Google BigQuery Setup

* Created GCP project: `fog-dashboard-dev`
* **Sandbox Mode:**

  * Initially tried but couldn’t query or generate tables.
  * Upgraded to billing-enabled project.
* **Dataset Created:** `fog_weather_data`
* **Table Created:** `hourly_weather_pacifica` via BigQuery UI
* **Verified Data Upload:**

  * Ran test queries like:

```sql
SELECT TOP(100) *
FROM `fog_weather_data.hourly_weather_pacifica`
```

---

### 3. dbt Initialization

* Ran `dbt init fog_dashboard_dbt`
* Chose:

  * Adapter: **BigQuery**
  * Auth method: **Service Account** (instead of OAuth)
* Downloaded and saved service account key to `.secrets/`
* **Issue:** `dbt debug` failed with `Profile should not be None`.

  * Cause: Running `dbt debug` from wrong directory (outside project subdir).
  * Fix: Changed into `fog_dashboard_dbt/` directory to resolve.

**Final `profiles.yml`:**

```yaml
fog_dashboard_dbt:
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: fog-dashboard-dev
      dataset: fog_weather_data
      keyfile: /Users/shusakumatsuda/Desktop/Fog_Dashboard_Project/fog_dashboard_dbt/.secrets/fog-dashboard-dev-XXXX.json
      threads: 1
      location: US
      priority: interactive
      job_execution_timeout_seconds: 300
      job_retries: 1
  target: dev
```

**`dbt_project.yml`:**

```yaml
profile: 'fog_dashboard_dbt'
```

* `dbt debug` passed after correcting working directory.

---

### 4. Source & Staging Model Setup

* Created `schema.yml` with the following source block:

```yaml
sources:
  - name: fog_dashboard_project
    database: fog-dashboard-dev
    schema: fog_weather_data
    tables:
      - name: hourly_weather_pacifica
        description: "Hourly weather data at the Pacifica weather station"
```

* Created `staging_raw_hourly_data.sql`:

```sql
{{ config(materialized='table') }}

select *
from {{ source('fog_dashboard_project', 'hourly_weather_pacifica') }}
```

* **Materialization Options Discussed:** `table`, `view`, `incremental`, `ephemeral`

---

### 5. dbt Run Execution

* Command: `dbt run`
* Outcome:

  * Successfully created `fog_weather_data.staging_raw_hourly_data`
  * Processed \~28,000 rows (\~3.5 MiB)
* Example Output:

```
1 of 1 OK created sql table model fog_weather_data.staging_raw_hourly_data ..... [CREATE TABLE (28.1k rows, 3.5 MiB processed) in 9.41s]
```

---

### 6. Schema Testing

* Added tests in `schema.yml`:

```yaml
models:
  - name: staging_raw_hourly_data
    description: "Raw staging model for hourly Pacifica weather data"
    columns:
      - name: timestamp
        description: "Timestamp of the reading"
        tests:
          - not_null
      - name: temp_f
        description: "Temperature in Fahrenheit"
        tests:
          - not_null
```

---

### 7. Key Learnings and Future Plans

* **Retained staging model** despite Python cleaning to enable downstream transforms.
* Resolved config warning for unused `models.fog_dashboard_dbt.example` path.
* **Next Steps:**

  * Add staging transformations:

    * Wind speed to m/s
    * Sky cover normalization
    * Wind direction cleaning
  * Add models for fog classification
  * Automate API pull process to replace snapshot
  * Use `dbt docs generate` for documentation
  * Explore dashboarding tools (e.g., Dash, Streamlit)

---

This summary reflects the full lifecycle of your fog weather dbt project—from sourcing and cleaning NOAA data, to BigQuery setup, dbt modeling, and schema testing.
