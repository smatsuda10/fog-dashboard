## 📘 Project Architecture & Deployment Reference – NBA/WNBA Dash App

### Project Name

Team 23 NBA/WNBA Analytics Platform

### Purpose

Full-stack analytics dashboard with prediction capabilities for NBA and WNBA teams.

---

### 🔧 Technology Stack Overview

| Component        | Technology                         | Purpose                                            |
| ---------------- | ---------------------------------- | -------------------------------------------------- |
| Frontend         | Dash (Python)                      | Interactive UI for visualizing and predicting wins |
| Backend Model    | LightGBM                           | Machine learning model for win predictions         |
| API Hosting      | Cloud Run / Cloud Functions (Gen2) | Hosts the LightGBM inference endpoint              |
| Data Warehouse   | BigQuery                           | Centralized storage for NBA/WNBA data              |
| Deployment CI/CD | Cloud Build                        | Automates deployment of app + model                |
| Infra Platform   | Google Cloud Platform (GCP)        | Unified cloud infrastructure                       |

---

### 🖥️ Dash App: Hosting & Deployment

* **App Directory:** `visualization_app/`
* **Entrypoint:** `main.py`

#### ✅ Key Files

* `app.yaml`: Tells GCP how to deploy the Dash app to App Engine
* `main.py`: Contains Dash layout, callbacks, and `server = app.server`
* `requirements.txt`: Python dependencies for App Engine

#### ✅ Deployment Target

* **Platform:** Google App Engine (Standard)
* **Command:**

```bash
cd visualization_app
gcloud app deploy
```

#### ✅ Example `app.yaml`

```yaml
runtime: python312
entrypoint: gunicorn -b :$PORT main:server
env: standard
instance_class: F1
handlers:
  - url: /.*
    script: auto
    secure: always
automatic_scaling:
  min_instances: 0
  max_instances: 8
```

#### 🔥 Why `server = app.server` Matters

App Engine uses this line to locate and serve your Dash app through Flask/Gunicorn.

---

### 🤖 LightGBM Model: Hosting & Behavior

* **Directory:** `machine_learning_models/light_gradient_boosting_machine/`
* **Entrypoint:** `main.py`
* **Function Name:** `train_lgbm`

#### ✅ What It Does

* Receives POST requests with:

  * BigQuery table
  * Independent variables
  * What-if input values
* Queries BigQuery
* Trains LightGBM model on-the-fly
* Returns JSON prediction

#### ✅ Hosting Method

* **Platform:** Cloud Run (originally named like Cloud Function)
* **Trigger:** HTTP POST
* **Endpoint:**

```
https://us-west1-team-23-mj-6242.cloudfunctions.net/train_lgbm
```

---

### 📊 BigQuery: Data Warehouse

* **Project:** `team-23-mj-6242`
* **Dataset:** `team_23_dataset`

#### Example Tables

* `combined_nba_data`
* `combined_wnba_data`
* `combined_nba_coordinates`
* `new_nba_stack`, `new_wnba_stack`

#### dbt Project

* **Path:** `team_23_data_warehouse/`
* SQL transformations run via `dbt run`, `dbt build`, etc.

---

### 📦 Cloud Build Deployment

* **Config File:** `cloudbuild.yaml`
* **Steps:**

  * Deploy LightGBM API using `gcloud functions deploy`
  * Deploy Dash app using `gcloud app deploy`
* **Logs Stored In:**

```
gs://team-23-mj-storage-bucket-6242
```

---

### 📁 Project Structure Highlights

```plaintext
visualization_app/
├── app.yaml
├── main.py
├── requirements.txt

machine_learning_models/
└── light_gradient_boosting_machine/
    ├── main.py
    ├── requirements.txt

cloudbuild.yaml

team_23_data_warehouse/
└── models/
```
* Full directory up to level 3

```plaintext
├── cloudbuild.yaml
├── correlation_and_pca
│   ├── Explained Variance by PC - NBA.png
│   ├── Explained Variance by PC - WNBA.png
│   ├── Loadings by PC - Var - NBA.jpg
│   ├── Loadings by PC - Var - WNBA.jpg
│   ├── nba_analysis.py
│   ├── nba_correlation_checks.py
│   ├── WNBA_correlation_checks.py
│   └── wnba_pca.py
├── logs
│   └── dbt.log
├── machine_learning_models
│   ├── light_gradient_boosting_machine
│   │   ├── calculate_season_wins_stats.py
│   │   ├── main.py
│   │   ├── Metrics
│   │   ├── Notes on IAM
│   │   └── requirements.txt
│   ├── ols_linear_regression
│   │   ├── linear_reg_nba.py
│   │   └── linear_reg_wnba.py
│   ├── random_forest
│   │   ├── random_forest_nba.py
│   │   └── random_forest_wnba.py
│   └── superceded
│       └── rough_log_model_nba_avgs.py
├── nba
│   ├── demo_resources
│   │   └── combined_nba_data.csv
│   ├── get_box_scores.py
│   ├── get_shot_coordinates.py
│   ├── invoke_lgbm_example.py
│   ├── main.py
│   ├── play_by_play.py
│   └── superceded
│       ├── calculate_time_between_crits.py
│       └── nba_api_coordinates_exploration.py
├── README.md
├── README.txt
├── reference
│   └── reference.md
├── requirements.txt
├── run_demo.py
├── team_23_data_warehouse
│   ├── analyses
│   ├── dbt_project.yml
│   ├── macros
│   ├── models
│   │   ├── combined_nba_coordinates.sql
│   │   ├── combined_nba_data.sql
│   │   ├── combined_wnba_data.sql
│   │   ├── count_records_by_league_year.sql
│   │   ├── count_season_wins_nba.sql
│   │   ├── count_season_wins_wnba.sql
│   │   ├── nba_pbp_scoring_avg.sql
│   │   ├── nba_pbp_sorted.sql
│   │   ├── nba_teambox_season_avgs.sql
│   │   ├── new_nba_stack.sql
│   │   ├── new_wnba_stack.sql
│   │   ├── Play_Type_Conversion_NBA.sql
│   │   ├── schema.yml
│   │   ├── temp_nba_viz.sql
│   │   ├── temp_wnba_viz.sql
│   │   ├── wnba_nba_winners_by_year.sql
│   │   ├── wnba_pbp_scoring_avg.sql
│   │   ├── wnba_pbp_scoring.sql
│   │   ├── wnba_pbp_sorted.sql
│   │   ├── wnba_pbp_with_schedule.py
│   │   ├── wnba_teambox_season_avgs.sql
│   │   └── wnba_teambox.sql
│   ├── README.md
│   ├── seeds
│   ├── snapshots
│   └── tests
├── visualization_app
│   ├── __pycache__
│   │   └── layout.cpython-39.pyc
│   ├── app.yaml
│   ├── Images
│   │   ├── App Instances as of 11.18.24 8pm.jpg
│   │   ├── Data dictionary.jpg
│   │   ├── Play Type - NBA AS OF 11.10.24 v2.jpg
│   │   ├── Play Type - NBA AS OF 11.10.24.jpg
│   │   ├── Play Type - WNBA AS OF 11.10.24.jpg
│   │   ├── Radar Chart - Team Comparison AS OF 11.10.24.jpg
│   │   ├── Season Wins Predictor AS OF 11.10.24.jpg
│   │   └── Updated dbt lineage AS OF 11.10.24.jpg
│   ├── layout.py
│   ├── main.py
│   ├── requirements.txt
│   └── Superceded
│       ├── assets
│       ├── coordinates-app.py
│       ├── dictionary_button_notes
│       ├── NBA Coordinates notes
│       ├── radar_chart
│       ├── shotchart_v2.py
│       └── Viz App Deployment Notes
└── WNBA
    ├── wnba_add_seasons.py
    ├── WNBA_API_ImportData_AddtlSeasons.R
    └── WNBA_API_ImportData.R

```


---

### ⚙️ App Behavior Flow

1. User opens Dash app (App Engine)
2. App queries BigQuery for metrics
3. User selects features and submits inputs
4. Dash app sends POST to Cloud Run model
5. Model queries BigQuery, trains LightGBM, returns prediction
6. Dash app visualizes the prediction

---

### ✅ Summary Table

| Layer     | Tech              | Hosting       | Notes                            |
| --------- | ----------------- | ------------- | -------------------------------- |
| UI        | Dash              | App Engine    | Public UI for predictions        |
| Model API | LightGBM + Flask  | Cloud Run     | Trains model per HTTP call       |
| Data      | BigQuery + dbt    | BigQuery      | Centralized structured data      |
| CI/CD     | Cloud Build       | GCP           | Deploys model + app via pipeline |
| Logs      | Stackdriver / GCS | Cloud Logging | Debugging + audit trail          |

---

### 🖼️ Architecture Diagram

Include the following in your README if diagram is stored locally:

```markdown
![Architecture Diagram](nba_wnba_architecture_diagram.png)
```
