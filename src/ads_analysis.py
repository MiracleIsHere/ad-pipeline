import numpy as np
import os
import pandas as pd

from src.logger import shared_logger
from src.utils import ensure_output_file


def load_ads_data(filepath: str) -> pd.DataFrame:
    df = pd.read_json(filepath, lines=True)
    df['run_start_date'] = pd.to_datetime(df['run_start_date'], errors='coerce')
    df['run_end_date'] = pd.to_datetime(df['run_end_date'], errors='coerce')
    df['scraped_at'] = pd.to_datetime(df['scraped_at'], errors='coerce')
    df['normalized_at'] = pd.to_datetime(df['normalized_at'], errors='coerce')
    return df

def calculate_proxy_score(row) -> float:
    # Text length: Ideal range 50–250, peak at ~150
    text = row.get("ad_text") or ""
    text_len = len(text)
    # Two Gaussian-like peaks: one around 50, one around 150
    peak1 = np.exp(-((text_len - 50) ** 2) / (2 * 15 ** 2))
    peak2 = np.exp(-((text_len - 150) ** 2) / (2 * 30 ** 2))
    # Combine both scores and normalize to 0–1
    text_len_score = np.clip(max(peak1, peak2), 0, 1)

    media_type = row['media_mix']
    media_mix_score = {
        "video-only": 1.0,
        "both": 0.8,
        "image-only": 0.6,
        "none": 0.0
    }.get(media_type, 0.0)

    is_active_score = 1.0 if row.get('is_active') else 0.0

    # Cap duration to 36 hours before scoring
    duration = row.get("run_duration_hours") or 0
    capped_duration = min(duration, 36)
    duration_score = np.log1p(capped_duration) / np.log1p(36)

    score = (
        0.35 * text_len_score +
        0.3 * media_mix_score +
        0.2 * is_active_score +
        0.15 * duration_score
    )
    return round(score, 4)

def analyze(config: dict):
    input_path = os.path.join(
        config["paths"]["transformed_ads_dir"],
        config["paths"]["output_file"]
    )
    ensure_output_file(input_path)
    output_path = config["paths"]["analysis_output"]
    ensure_output_file(output_path)
    
    df = load_ads_data(input_path)

    try:
        df['proxy_performance_score'] = df.apply(calculate_proxy_score, axis=1)
        df['ad_text_len'] = df['ad_text'].fillna('').apply(len)
        top_ads_df = df.sort_values(by='proxy_performance_score', ascending=False).head(100)
        top_ads_df = top_ads_df[[
            'library_id',
            'advertiser_name',
            'proxy_performance_score',
            'ad_text_len',
            'media_mix',
            'is_active',
            'run_duration_hours'
        ]]
        top_ads_df.to_json(output_path, orient="records", lines=True)
    except Exception as e:
        shared_logger.error(f"Error analysing ads: {e}")

    shared_logger.info(f"Analysed and saved: {output_path}")
