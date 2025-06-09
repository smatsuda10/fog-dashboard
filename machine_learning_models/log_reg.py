import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    ConfusionMatrixDisplay,
    classification_report,
    roc_auc_score,
    RocCurveDisplay,
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from google.cloud import bigquery
from loguru import logger
import joblib


def conduct_logistic_regression():
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

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, stratify=y, random_state=42
    )

    # Train model
    model = LogisticRegression(max_iter=500)
    model.fit(X_train, y_train)

    # Predict labels and probabilities
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    conf_mat = confusion_matrix(y_test, y_pred)

    # Logging
    logger.info(f"Accuracy:  {acc:.3f}")
    logger.info(f"Precision: {prec:.3f}")
    logger.info(f"Recall:    {rec:.3f}")
    logger.info(f"AUC:       {auc:.3f}")
    logger.info(f"Confusion Matrix:\n{conf_mat}")
    print(classification_report(y_test, y_pred))

    # ROC Curve
    RocCurveDisplay.from_estimator(model, X_test, y_test)
    plt.title("ROC Curve for Fog Prediction")
    plt.grid(True)
    plt.show()

    # Feature importance
    feature_importance = pd.Series(model.coef_[0], index=feature_cols)
    feature_importance = feature_importance.sort_values(key=abs, ascending=False)
    print("\nTop 10 Most Influential Features:")
    print(feature_importance.head(10))
    joblib.dump(model, "logistic_model.joblib")
    joblib.dump(scaler, "logistic_model_scaler.joblib")
    logger.info("Model and scaler saved to disk.")


    return model, X_test, y_test, y_pred


if __name__ == "__main__":
    log_reg_model, X_test, y_test, y_pred = conduct_logistic_regression()

