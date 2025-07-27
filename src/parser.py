from typing import Any, Dict, List, Optional
from playwright.async_api import ElementHandle

from src.constants import (
    SUMMARY_BLOCK_SELECTOR,
    CONTENT_BLOCK_SELECTOR,
    ADVERTISER_SELECTOR,
    AD_BODY_BLOCK_SELECTOR,
    AD_VIDEO_SELECTOR,
    CALL_TO_ACTION_REF,
    CALL_TO_ACTION_BLOCK_SELECTOR,
    CALL_TO_ACTION_TEXTS_SELECTORS,
    CALL_TO_ACTIONS_BLOCK_SELECTOR,
    CALL_TO_ACTION_CARD_SELECTOR
)


async def extract_text(el: Optional[ElementHandle]) -> Optional[str]:
    return await el.inner_text() if el else None

async def extract_media(media_div: Optional[ElementHandle]) -> Dict[str, List[str]]:
    if not media_div:
        return {
        "images": [],
        "videos": []
    }

    images, videos = [], []

    img_tags = await media_div.query_selector_all("img")
    for img in img_tags:
        src = await img.get_attribute("src")
        if src:
            images.append(src)

    video_tags = await media_div.query_selector_all("video")
    for vid in video_tags:
        src = await vid.get_attribute("src")
        if src:
            videos.append(src)

    return {
        "images": images,
        "videos": videos
    }

async def extract_call_to_action_texts(cta_div: Optional[ElementHandle]) -> Optional[List[Optional[str]]]:
    if not cta_div:
        return None
    texts = []
    for selector in CALL_TO_ACTION_TEXTS_SELECTORS:
        el = await cta_div.query_selector(selector)
        text = await extract_text(el)
        texts.append(text)
    return texts

async def parse_ad(ad_el: ElementHandle) -> Dict[str, Any]:
    ad = {}
    summary_block = await ad_el.query_selector(SUMMARY_BLOCK_SELECTOR)
    summary_items = await summary_block.query_selector_all(":scope > div")
    ad["status_name"] = await extract_text(await summary_items[0].query_selector("span")) if len(summary_items) > 0 else None
    ad["library_id"] = await extract_text(await summary_items[1].query_selector("span")) if len(summary_items) > 1 else None
    ad["run_dates"] = await extract_text(await summary_items[2].query_selector("span")) if len(summary_items) > 2 else None

    content_block = await ad_el.query_selector(CONTENT_BLOCK_SELECTOR)
    advertiser = await content_block.query_selector(ADVERTISER_SELECTOR)
    ad["advertiser_name"] = await extract_text(advertiser)

    ad_body_block = await content_block.query_selector(AD_BODY_BLOCK_SELECTOR)
    ad["ad_text"] = await extract_text(await ad_body_block.query_selector("div._7jyr > span"))
    ad["ad_redirect"] = None
    ad["call_to_action_texts"] = []

    video = await ad_body_block.query_selector(AD_VIDEO_SELECTOR)
    ad["media"] = await extract_media(video)

    ref_block = await ad_body_block.query_selector(CALL_TO_ACTION_REF)
    if ref_block:
        ad["ad_redirect"] = await ref_block.get_attribute("href")
        cta_block = await ref_block.query_selector(CALL_TO_ACTION_BLOCK_SELECTOR)
        ad["call_to_action_texts"] = await extract_call_to_action_texts(cta_block)
        found_media = await extract_media(ref_block)
        ad["media"] = {
            "images": ad["media"]["images"] + found_media["images"],
            "videos": ad["media"]["videos"] + found_media["videos"]
        }
    ctas_block = await content_block.query_selector(CALL_TO_ACTIONS_BLOCK_SELECTOR)
    if ctas_block:
        ad["call_to_actions"] = []
        for card in await ctas_block.query_selector_all(CALL_TO_ACTION_CARD_SELECTOR):
            redirect_url_el = await card.query_selector("a")
            redirect_url = await redirect_url_el.get_attribute("href") if redirect_url_el else None
            cta_block = await card.query_selector(CALL_TO_ACTION_BLOCK_SELECTOR)
            ad["call_to_actions"].append({
                "ad_redirect": redirect_url,
                "call_to_action_texts": await extract_call_to_action_texts(cta_block),
                "media": await extract_media(card),
            })

    return ad
