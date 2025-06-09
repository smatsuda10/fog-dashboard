import dash
from dash import dcc, html, Input, Output, State
import requests

app = dash.Dash(__name__)
server = app.server  # for deployment

# Your Cloud Run endpoint
PREDICT_URL = "https://fog-api-475194601518.us-west1.run.app/predict"

# Layout
app.layout = html.Div([
    html.H2("Fog Prediction Dashboard"),

    html.Div([
        html.Label("Temperature (°C)"),
        dcc.Input(id='temp_c', type='number', value=12.0),
        html.Label("Dew Point (°C)"),
        dcc.Input(id='dewpoint_c', type='number', value=10.0),
        html.Label("Humidity (%)"),
        dcc.Input(id='humidity_percent', type='number', value=95),
        html.Label("Wind Speed (m/s)"),
        dcc.Input(id='wind_speed_mps', type='number', value=2.0),
        html.Label("Wind Direction (°)"),
        dcc.Input(id='wind_direction_deg', type='number', value=180),
        html.Label("Visibility (km)"),
        dcc.Input(id='visibility_km', type='number', value=5.0),
        html.Label("Altimeter (inHg)"),
        dcc.Input(id='altimeter_inhg', type='number', value=30.0),
        html.Label("Precipitation (in, past 1hr)"),
        dcc.Input(id='precip_1hr_in', type='number', value=0.0),
        # Add more inputs as needed...
    ], style={"columnCount": 2, "gap": "10px"}),

    html.Br(),
    html.Button("Predict Fog Probability", id='submit', n_clicks=0),
    html.Div(id='prediction_output', style={"marginTop": "20px", "fontSize": "20px"})
])

# Callback
@app.callback(
    Output('prediction_output', 'children'),
    Input('submit', 'n_clicks'),
    State('temp_c', 'value'),
    State('dewpoint_c', 'value'),
    State('humidity_percent', 'value'),
    State('wind_speed_mps', 'value'),
    State('wind_direction_deg', 'value'),
    State('visibility_km', 'value'),
    State('altimeter_inhg', 'value'),
    State('precip_1hr_in', 'value'),
)
def predict(n_clicks, temp_c, dewpoint_c, humidity_percent, wind_speed_mps, wind_direction_deg,
            visibility_km, altimeter_inhg, precip_1hr_in):
    if n_clicks == 0:
        return ""

    payload = {
        "temp_c": temp_c,
        "dewpoint_c": dewpoint_c,
        "humidity_percent": humidity_percent,
        "wind_speed_mps": wind_speed_mps,
        "wind_direction_deg": wind_direction_deg,
        "visibility_km": visibility_km,
        "altimeter_inhg": altimeter_inhg,
        "precip_1hr_in": precip_1hr_in,
        # Fill the rest with defaults or let user input them
        "temp_c_lag_1hr": temp_c,
        "humidity_lag_1hr": humidity_percent,
        "visibility_lag_1hr": visibility_km,
        "temp_delta_1hr": 0.0,
        "humidity_delta_1hr": 0.0,
        "visibility_delta_1hr": 0.0,
        "temp_avg_3hr": temp_c,
        "humidity_avg_3hr": humidity_percent,
        "visibility_avg_3hr": visibility_km,
        "is_night": 1,
        "month": 11,
        "temp_c_7pm_yesterday": temp_c,
        "dewpoint_c_7pm_yesterday": dewpoint_c,
        "humidity_7pm_yesterday": humidity_percent,
        "visibility_7pm_yesterday": visibility_km,
        "is_foggy_at_7pm_yesterday": 1
    }

    try:
        response = requests.post(PREDICT_URL, json=payload)
        result = response.json()
        if "probability_of_fog" in result:
            return f"🌫️ Fog Probability: {result['probability_of_fog']:.2%}"
        else:
            return f"Error: {result}"
    except Exception as e:
        return f"Error contacting API: {e}"

if __name__ == '__main__':
    app.run(debug=True)

