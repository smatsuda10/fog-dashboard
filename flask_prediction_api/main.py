from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

# Load models
log_reg_model = joblib.load("models/logistic_model.joblib")
log_reg_scaler = joblib.load("models/logistic_model_scaler.joblib")

rf_model = joblib.load("models/rf_model.joblib")
rf_scaler = joblib.load("models/rf_model_scaler.joblib")

@app.route("/")
def index():
    return "Fog Prediction API is running!"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        input_json = request.get_json()
        model_type = input_json.get("model", "logistic")  # default: logistic

        # Expected order of features
        expected_features = [
            "temp_c",
            "dewpoint_c",
            "humidity_percent",
            "wind_speed_mps",
            "wind_direction_deg",
            "visibility_km",
            "altimeter_inhg",
            "precip_1hr_in",
            "temp_c_lag_1hr",
            "humidity_lag_1hr",
            "visibility_lag_1hr",
            "temp_delta_1hr",
            "humidity_delta_1hr",
            "visibility_delta_1hr",
            "temp_avg_3hr",
            "humidity_avg_3hr",
            "visibility_avg_3hr",
            "is_night",
            "month",
            "temp_c_7pm_yesterday",
            "dewpoint_c_7pm_yesterday",
            "humidity_7pm_yesterday",
            "visibility_7pm_yesterday",
            "is_foggy_at_7pm_yesterday"
        ]

        features = [float(input_json[feat]) for feat in expected_features]
        features_array = np.array(features).reshape(1, -1)

        if model_type == "random_forest":
            scaled = rf_scaler.transform(features_array)
            proba = rf_model.predict_proba(scaled)[0][1]
        else:
            scaled = log_reg_scaler.transform(features_array)
            proba = log_reg_model.predict_proba(scaled)[0][1]

        return jsonify({"probability_of_fog": round(proba, 4)})

    except KeyError as e:
        return jsonify({"error": f"Missing field: {e}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
