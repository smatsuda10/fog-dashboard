# fog-dashboard

## What To Do Next

### 🔄 Model & API

1. 🔧 Improve model feature engineering:

   * Add pressure trends, fog history, and long-range deltas (6h, 12h)
   * Explore time-of-day embeddings or categorical binning
2. 🔍 Add model versioning:

   * Save model metadata (AUC, train date)
   * Version endpoints (e.g., `/predict/v2`)

### 🌐 API & Backend

3. 🧪 Add `/health` and `/version` endpoints to the Flask API
4. 📦 Set up automated rebuilds via `cloudbuild.yaml` and GitHub → Cloud Run

### 🎨 Dash App

5. ✅ MVP Dash UI is working locally
6. ⬇️ Next enhancements:

   * Add all 24 input fields
   * Let user select a **Bay Area weather station**

     * Load historical ranges (e.g., HAF, SFO, OAK)
     * Autocomplete or dropdown list
   * Add location map and station info card
7. 🚀 Deploy Dash app (via App Engine or Cloud Run)

### 📊 Looker Studio Dashboard

8. 🛍️ Create a Looker Studio dashboard for high-level insights:

   * Monthly fog day frequency
   * Fog trends per station
   * Aggregated humidity vs. fog correlation
   * Seasonality patterns (heatmap or calendar view)



---

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
  * Processed ~28,000 rows (~3.5 MiB)

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

### 7. Model Training & Evaluation (June 8, 2025)

* Trained both **Logistic Regression** and **Random Forest** classifiers
* Preprocessed with:
  * `dropna()` to exclude rows with missing features
  * `StandardScaler` for Logistic Regression
* Performance:
  * Logistic Regression: AUC = 0.939 | Accuracy = 0.849
  * Random Forest: AUC = 0.936 | Accuracy = 0.863
* Logged key metrics, confusion matrix, and feature importance
* Visualized ROC curve using `RocCurveDisplay`
* Saved models with `joblib.dump()` (next: serve via Flask API)

---

### 8. Decision History

* ✅ Logistic regression was chosen first for interpretability
* ✅ Scaling added after noticing convergence warning
* ✅ Random forest added for comparison, shows slightly higher accuracy and better recall
* ✅ Top features consistently include: humidity_avg_3hr, humidity_lag_1hr, dewpoint_c, and visibility_km
* ✅ You plan to expose model predictions via Flask API, following a pattern from the reference project
* ✅ Dash app will offer a technical drill-down, while Looker Studio gives high-level stats for non-technical users


## 9. Flask API Deployment (June 8, 2025)

* Created a production-ready Flask API:

  * Validates 24 features from JSON
  * Applies appropriate scaler and model (logistic or random forest)
  * Returns fog probability as JSON
* Thorough exception handling added for debugging
* API tested successfully locally with `curl` and deployed to Cloud Run:

  * Endpoint: `https://fog-api-475194601518.us-west1.run.app/predict`

## 10. Dash UI (Local Frontend)

* Built an interactive Dash app to:

  * Accept weather input (temp, dew point, humidity, etc.)
  * Submit to `/predict` endpoint
  * Display fog probability as a percentage
* Developed within `fog_dashboard_frontend/` directory with separate virtual environment
* Example screenshot saved as: `fog_dashboard_dash_ui_screenshot.png`

![Fog Prediction Dashboard UI](fog_dashboard_dash_ui_screenshot.png)
