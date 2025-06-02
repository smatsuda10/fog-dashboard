import pandas as pd

# Read raw using pandas
df = pd.read_csv("data/HAF_202308010000_202409010000.csv", skiprows=5)

# Preview data
# pd.set_option('display.max_columns', None)
# pd.set_option('display.width', 200)  # or higher for wide terminals
# print(df.groupby('wxcodes').count())
# print(df.head())
# print(df.tail())
# print(df.sample(5))
# print(df.columns.tolist())
# df.info()
# df.describe(include='all')

# Drop irrelevant columns
df = df.drop(columns=['skyc4','skyl4', 'ice_accretion_1hr', 'ice_accretion_3hr', 'ice_accretion_6hr', 'metar', 'snowdepth', 'peak_wind_gust', 'peak_wind_drct', 'peak_wind_time', 'mslp'])
    # dropepd mslp since there was no nonnull data
# print(f"df with after dropping irrelevant columns:{df.head}")

# Clean column names
df = df.rename(columns={
    'valid': 'timestamp',
    'tmpf': 'temp_f',
    'dwpf': 'dewpoint_f',
    'relh': 'humidity_percent',
    'drct': 'wind_direction_deg',
    'sknt': 'wind_speed_kt',
    'p01i': 'precip_1hr_in',
    'alti': 'altimeter_inhg',
    'vsby': 'visibility_miles',
    'gust': 'wind_gust_kt',
    'skyc1': 'sky_cover_1',
    'skyc2': 'sky_cover_2',
    'skyc3': 'sky_cover_3',
    'skyl1': 'sky_altitude_1_ft',
    'skyl2': 'sky_altitude_2_ft',
    'skyl3': 'sky_altitude_3_ft',
    'wxcodes': 'weather_codes',
    'feel': 'feels_like_f',
    'station': 'station_id',
    'lon': 'longitude',
    'lat': 'latitude'
})

# Change timestamp column to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], utc = True)

# Convert missing values to NaN
df.replace("M", pd.NA, inplace=True)

# Change columns data types
# df.info()
numeric_cols = [
    'temp_f',
    'dewpoint_f',
    'humidity_percent',
    'wind_direction_deg',
    'wind_speed_kt',
    'precip_1hr_in',
    'altimeter_inhg',
    'visibility_miles',
    'wind_gust_kt',
    'sky_altitude_1_ft',
    'sky_altitude_2_ft',
    'sky_altitude_3_ft',
    'feels_like_f',
    'longitude',
    'latitude'
]
string_cols = [
    'station_id',
    'sky_cover_1',
    'sky_cover_2',
    'sky_cover_3',
    'weather_codes'
]

df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
df[string_cols] = df[string_cols].astype(str)
# df.info()

# Save clean df as csv
df.to_csv("data/hourly_weather_pacifica_clean.csv", index=False)



