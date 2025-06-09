import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)
from google.cloud import bigquery
from loguru import logger
import joblib


def conduct_random_forest():
    # Initialize BigQuery client
    client = bigquery.Client(project="fog-dashboard-dev")
    logger.info("BigQuery client initialized.")

    # Load data from BigQuery
    table_id = "fog-dashboard-dev.fog_weather_data.ml_fog_training_data"
    query = f"""
        SELECT *
        FROM `{table_id}`
        WHERE is_foggy_at_7pm IS NOT NULL
    """
    df = client.query(query).to_dataframe()
    logger.info(f"Raw data pulled: {df.shape[0]} rows, {df.shape[1]} columns")

    # Drop rows with any missing values
    df = df.dropna()
    logger.info(f"After dropping NaNs: {df.shape[0]} rows remain")

    # Drop non-feature columns
    drop_cols = [
        "local_date", "station_id", "season", "fog_fraction", "is_foggy_at_7pm"
    ]
    feature_cols = [col for col in df.columns if col not in drop_cols]
    X = df[feature_cols]
    y = df["is_foggy_at_7pm"].astype(int)

    # Scale the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, stratify=y, random_state=42
    )

    # Train Random Forest model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Predict
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # Evaluate
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    conf_mat = confusion_matrix(y_test, y_pred)

    logger.info(f"Accuracy:  {acc:.3f}")
    logger.info(f"Precision: {prec:.3f}")
    logger.info(f"Recall:    {rec:.3f}")
    logger.info(f"AUC:       {auc:.3f}")
    logger.info(f"Confusion Matrix:\n{conf_mat}")
    print(classification_report(y_test, y_pred))

    # Feature importances
    importances = pd.Series(model.feature_importances_, index=feature_cols)
    importances = importances.sort_values(ascending=False).head(10)
    print("\nTop 10 Most Important Features (Random Forest):")
    print(importances)
    joblib.dump(model, "rf_model.joblib")
    joblib.dump(scaler, "rf_model_scaler.joblib")
    logger.info("Model and scaler saved to disk.")

    return model, X_test, y_test, y_pred


if __name__ == "__main__":
    rf_model, X_test, y_test, y_pred = conduct_random_forest()
