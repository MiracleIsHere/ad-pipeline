import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright

from src.constants import AD_CARD_SELECTOR
from src.logger import shared_logger
from src.parser import parse_ad
from src.utils import build_ad_library_url, ensure_output_file, write_batch_to_file


async def scrape_ads(config: dict):
    ad_params = config["ad_library"]
    scraper_cfg = config["scraper"]
    output_path = os.path.join(
        config["paths"]["parsed_ads_dir"],
        config["paths"]["output_file"]
    )
    ensure_output_file(output_path)
    quarantine_path = os.path.join(
        config["paths"]["quarantine_dir"],
        config["paths"]["output_file"]
    )
    ensure_output_file(quarantine_path)

    headless = scraper_cfg["headless"]
    max_ads = scraper_cfg["max_ads"]
    max_scroll_tries = scraper_cfg["max_scroll_tries"]
    scroll_timeout = scraper_cfg["scroll_timeout_ms"]
    batch_size = scraper_cfg["batch_size"]

    ads, output_count, prev_count, tries = [], 0, 0, 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto(build_ad_library_url(ad_params))

        while output_count < max_ads and tries < max_scroll_tries:
            ad_cards = await page.query_selector_all(AD_CARD_SELECTOR)
            new_cards = ad_cards[prev_count:]

            if not new_cards:
                tries += 1
                shared_logger.info(f"No new ads found. Try {tries}")
            else:
                tries = 0

            for ad_el in new_cards:
                try:
                    ad = await parse_ad(ad_el)
                    ad["scraped_at"] = datetime.now(timezone.utc).isoformat()
                    ads.append(ad)
                    if len(ads) >= batch_size:
                        shared_logger.info(f"Writing {len(ads)} ads to file")
                        write_batch_to_file(output_path, ads)
                        output_count += len(ads)
                        ads.clear()
                    if output_count >= max_ads:
                        break
                except Exception as e:
                    shared_logger.error(f"Skipped ad due to error: {e}")
                    try:
                        ad_html = await ad_el.inner_html()
                        quarantine_record = {
                            "error": str(e),
                            "html": ad_html,
                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                        }
                        write_batch_to_file(quarantine_path, [quarantine_record])
                    except Exception as inner_e:
                        shared_logger.error(f"Failed to write to quarantine: {inner_e}")
            
            prev_count = len(ad_cards)
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(scroll_timeout)
        
        if ads:
            write_batch_to_file(output_path, ads)
        await browser.close()
        shared_logger.info(f"Finished. Output: {output_path}")
