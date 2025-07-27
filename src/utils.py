import json
import os
from urllib.parse import urlencode


def ensure_output_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def build_ad_library_url(params: dict) -> str:
    return f"https://www.facebook.com/ads/library/?{urlencode(params)}"

def write_batch_to_file(output_file, batch):
    with open(output_file, "a", encoding="utf-8") as f:
        for ad in batch:
            f.write(json.dumps(ad, ensure_ascii=False) + "\n")
