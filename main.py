import argparse
import asyncio

from src.ads_analysis import analyze
from src.config import load_config
from src.logger import shared_logger
from src.scraper import scrape_ads
from src.transformer import transform


def parse_args():
    parser = argparse.ArgumentParser(description="Run Ad pipeline.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml")
    return parser.parse_args()

def main():
    args = parse_args()
    config = load_config(args.config)
    try:
        asyncio.run(scrape_ads(config))
        transform(config)
        analyze(config)
    except Exception as e:
        shared_logger.exception("Unhandled exception during pipeline run")

# python main.py --config config.yaml
if __name__ == "__main__":
    main()
