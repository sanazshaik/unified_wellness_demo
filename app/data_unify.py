
import pandas as pd

# Loads and merges csv data files
def load_and_merge(sleep_path, activity_path, nutrition_path, biometrics_path):
    sleep = pd.read_csv(sleep_path, parse_dates=['date'])
    act = pd.read_csv(activity_path, parse_dates=['date'])
    nut = pd.read_csv(nutrition_path, parse_dates=['date'])
    bio = pd.read_csv(biometrics_path, parse_dates=['date'])

    df = sleep.merge(act, on='date', how='outer') \
             .merge(nut, on='date', how='outer') \
             .merge(bio, on='date', how='outer')
    df = df.sort_values('date').reset_index(drop=True)

    # Features
    df['sugar_next_day'] = df['sugar_g'].shift(-1)
    df['sleep_prev'] = df['sleep_hours'].shift(1)
    df['calories_prev'] = df['calories'].shift(1)

    # Baselines for anomaly input
    for col in ['resting_hr','systolic_bp','diastolic_bp','weight_lb','sleep_hours']:
        if col in df.columns:
            df[f'{col}_baseline'] = df[col].rolling(window=14, min_periods=7).median()
            df[f'{col}_dev'] = df[col] - df[f'{col}_baseline']

    return df
