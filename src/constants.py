AD_CARD_SELECTOR = "div.xrvj5dj > div.xh8yej3"

SUMMARY_BLOCK_SELECTOR = "div.x78zum5.xdt5ytf.x2lwn1j.xeuugli" # within ad card

CONTENT_BLOCK_SELECTOR = "div._7jyg._7jyh" # within ad card
ADVERTISER_SELECTOR = '//div[contains(@class, "_8nsi") and contains(@class, "_8nqp")]//span[1]' # within content block

AD_BODY_BLOCK_SELECTOR = "div.x6ikm8r.x10wlt62" # within content block
AD_VIDEO_SELECTOR = "div.x14ju556.x1n2onr6" # within ad body block

CALL_TO_ACTION_REF = "a.x1hl2dhg.x1lku1pv.x8t9es0.x1fvot60.xxio538.xjnfcd9.xq9mrsl.x1yc453h.x1h4wwuj.x1fcty0u.x1lliihq" # within ad body block
CALL_TO_ACTION_BLOCK_SELECTOR = "div.x1iyjqo2.x2fvf9.x6ikm8r.x10wlt62.xt0b8zv" # within CTA ref
CALL_TO_ACTION_TEXTS_SELECTORS = (
    "div.x6ikm8r.x10wlt62.xlyipyv.x5e6ka.x1eftoo1",
    "div.x6ikm8r.x10wlt62.xlyipyv.x1mcwxda.x190qgfh",
    "div.x6ikm8r.x10wlt62.xlyipyv.x5e6ka.xb2kyzz"
) # within CTA block

CALL_TO_ACTIONS_BLOCK_SELECTOR = "div.x1odjw0f" # within content block
CALL_TO_ACTION_CARD_SELECTOR = "div._7jy-" # within CTAs block
