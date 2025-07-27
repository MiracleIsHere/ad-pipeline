import hashlib
import json
import os
import re

from datetime import datetime, date, timezone
from langdetect import detect
from typing import Any, Dict, Optional, Tuple

from src.logger import shared_logger
from src.utils import ensure_output_file


def clean_text(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    return re.sub(r"[\u200b\u200e\u200f\xa0]", "", s).strip()

def date_to_iso(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None

def has_non_empty(lst: list) -> bool:
    return bool(lst and any(item is not None for item in lst))

def join_texts(lst: list) -> Optional[str]:
    if not lst:
        return None
    texts = [text for text in lst if text]
    return "\n".join(texts) if texts else None

def extract_dates_from_run_info(run_dates: str) -> Tuple[Optional[date], Optional[date]]:
    """
    Parses ad run info text and returns start and end dates as date objects.
    """
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    patterns_with_end = [
        r"(\d{1,2} \w+ \d{4}) - (\d{1,2} \w+ \d{4})",
        r"(\w+ \d{1,2}, \d{4}) - (\w+ \d{1,2}, \d{4})",
    ]

    for pattern in patterns_with_end:
        m = re.match(pattern, run_dates)
        if m:
            try:
                start_date = datetime.strptime(m.group(1), "%b %d, %Y" if "," in m.group(1) else "%d %B %Y").date()
                end_date = datetime.strptime(m.group(2), "%b %d, %Y" if "," in m.group(2) else "%d %B %Y").date()
                return start_date, end_date
            except Exception as e:
                shared_logger.error(f"Error parsing start/end dates: {run_dates} | {e}")
                return None, None

    patterns_with_start_only = [
        r"Started running on (\w+ \d{1,2}, \d{4})",
        r"Started running on (\d{1,2} \w+ \d{4})",
    ]

    for pattern in patterns_with_start_only:
        m = re.search(pattern, run_dates)
        if m:
            try:
                start_date = datetime.strptime(m.group(1), "%b %d, %Y" if "," in m.group(1) else "%d %B %Y").date()
                return start_date, None
            except Exception as e:
                shared_logger.error(f"Error parsing start-only date: {run_dates} | {e}")
                return None, None

    shared_logger.warning(f"No date pattern matched: {run_dates}")
    return None, None

def extract_library_id(raw_id: Optional[str]) -> Optional[str]:
    if raw_id is None:
        return None
    return raw_id.rsplit(" ", 1)[-1]

def calculate_duration_hours(
    start_date: Optional[date],
    end_date: Optional[date],
    is_active: bool,
    scraped_at: datetime,
    run_dates: str
) -> Optional[float]:
    """
    Calculates duration_hours based on available dates, ad status, and run time text.
    """
    duration_hours = None

    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    if end_date:
        end_dt = datetime.combine(end_date, datetime.min.time(), tzinfo=timezone.utc)
    if start_date and not end_date and is_active:
        end_dt = scraped_at

    m = re.search(r"Total active time (\d+(?:\.\d+)?) hrs", run_dates)
    if m:
        duration_hours = float(m.group(1))
    if start_dt and end_dt and duration_hours is None:
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
    return round(duration_hours, 2) if duration_hours else None

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"

def infer_media_mix(media: dict) -> str:
    has_images = bool(media.get("images"))
    has_videos = bool(media.get("videos"))
    if has_images and has_videos:
        return "both"
    elif has_images:
        return "image-only"
    elif has_videos:
        return "video-only"
    return "none"

def normalize_for_hash(value: Any) -> Any:
    """Prepare the value for hashing: sort lists, convert None to empty string."""
    if value is None:
        return ""
    if isinstance(value, list):
        return sorted(normalize_for_hash(v) for v in value)
    return value

def compute_ad_hash(ad: Dict[str, Any]) -> str:
    """Compute a SHA256 hash based on specific ad fields."""
    fields_to_hash = {
        "advertiser_name": normalize_for_hash(ad.get("advertiser_name")),
        "ad_text": normalize_for_hash(ad.get("ad_text")),
        "ad_redirect": normalize_for_hash(ad.get("ad_redirect")),
        "has_call_to_action": normalize_for_hash(ad.get("has_call_to_action")),
        "call_to_action_text": normalize_for_hash(ad.get("call_to_action_text")),
        "has_call_to_actions": normalize_for_hash(ad.get("has_call_to_actions")),
        "media_images": normalize_for_hash(ad.get("media_images")),
        "media_videos": normalize_for_hash(ad.get("media_videos")),
    }
    serialized = json.dumps(fields_to_hash, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def normalize_ad(ad: Dict[str, Any]) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    scraped_at = ad.get("scraped_at")
    raw_run_dates = ad.get("run_dates", "")
    
    run_start_date, run_end_date = extract_dates_from_run_info(raw_run_dates)
    is_active = clean_text(ad.get("status_name", "")).lower() == "active"
    
    library_id_raw = ad.get("library_id")
    library_id = extract_library_id(ad.get("library_id"))

    if not library_id:
        raise ValueError(f"Missing or invalid library_id in ad: {library_id_raw}")
    
    normalized = {
        "library_id": library_id,
        "advertiser_name": ad.get("advertiser_name", "").strip(),
        "run_start_date": date_to_iso(run_start_date),
        "run_end_date": date_to_iso(run_end_date),
        "run_duration_hours": calculate_duration_hours(
            run_start_date,
            run_end_date,
            is_active,
            datetime.fromisoformat(scraped_at),
            raw_run_dates
        ),
        "ad_text": ad.get("ad_text"),
        "ad_redirect": ad.get("ad_redirect"),
        "has_call_to_action": has_non_empty(ad.get("call_to_action_texts", [])),
        "call_to_action_text": join_texts(ad.get("call_to_action_texts", [])),
        "has_call_to_actions": has_non_empty(ad.get("call_to_actions", [])),
        "language": detect_language(ad.get("ad_text", "")) if ad.get("ad_text") else None,
        "media_images": ad.get("media", {}).get("images", []),
        "media_videos": ad.get("media", {}).get("videos", []),
        "media_mix": infer_media_mix(ad.get("media", {})),
        "is_active": is_active,
        "scraped_at": scraped_at,
        "normalized_at": now_iso,
    }
    normalized["ad_hash"] = compute_ad_hash(normalized)
    return normalized

def transform(config: dict):
    input_path = os.path.join(
        config["paths"]["parsed_ads_dir"],
        config["paths"]["output_file"]
    )
    ensure_output_file(input_path)
    output_path = os.path.join(
        config["paths"]["transformed_ads_dir"],
        config["paths"]["output_file"]
    )
    ensure_output_file(output_path)

    with open(input_path, "r", encoding="utf-8") as fin, \
            open(output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            try:
                ad = json.loads(line)
                transformed_ad = normalize_ad(ad)
                fout.write(json.dumps(transformed_ad, ensure_ascii=False) + "\n")
            except json.JSONDecodeError:
                shared_logger.error(f"Skipping invalid JSON line: {line}")
            except Exception as e:
                shared_logger.error(f"Error transforming ad: {e}")

    shared_logger.info(f"Transformed and saved: {output_path}")
