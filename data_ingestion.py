import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_theft_dataset_with_time(start_time, end_time, sampling_rate_sec=30, seed=42):
    np.random.seed(seed)

    # --- Create timestamp index ---
    time_series = pd.date_range(start_time, end_time, freq=f'{sampling_rate_sec}s')
    df = pd.DataFrame(index=time_series)
    df.index.name = 'timestamp'

    # --- Normal Data (150-200W, 0.5-1A) ---
    df['power'] = np.random.uniform(150, 200, len(df))
    df['current'] = np.random.uniform(0.5, 1.0, len(df))
    df['label'] = 0

    # --- Theft Injection ---
    # Choose random intervals for theft
    n_thefts = 5
    theft_duration = timedelta(hours=2)  # each theft lasts 2 hours

    for _ in range(n_thefts):
        start_theft = pd.to_datetime(np.random.choice(df.index[:-240]))
        end_theft = start_theft + theft_duration
        theft_mask = (df.index >= start_theft) & (df.index < end_theft)

        # Case 1: Higher power but low current
        if np.random.rand() > 0.5:
            df.loc[theft_mask, 'power'] = np.random.uniform(250, 500, theft_mask.sum())
            df.loc[theft_mask, 'current'] = np.random.uniform(0.3, 0.7, theft_mask.sum())
        # Case 2: Normal power but unusually high current
        else:
            df.loc[theft_mask, 'power'] = np.random.uniform(150, 200, theft_mask.sum())
            df.loc[theft_mask, 'current'] = np.random.uniform(1.5, 3.0, theft_mask.sum())

        df.loc[theft_mask, 'label'] = 1

    # --- Time-based features ---
    df['hour_of_day'] = df.index.hour
    df['day_of_week'] = df.index.dayofweek  # Monday=0
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    # --- Final dataframe ---
    final_df = df[['power', 'current', 'hour_of_day', 'day_of_week', 'is_weekend', 'label']]

    return final_df


if __name__ == "__main__":
    start = datetime(2025, 8, 1, 0, 0, 0)
    end = start + timedelta(days=7)  # one week of data
    dataset = generate_theft_dataset_with_time(start, end, sampling_rate_sec=60)  # 1-min interval
    dataset.to_csv("power_dataset.csv", index=False)
    print("Dataset saved to power_dataset.csv")
    print(dataset.head())
