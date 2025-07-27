import logging
import sys


shared_logger = logging.getLogger("ad_pipeline")
shared_logger.setLevel(logging.DEBUG)

if not shared_logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    shared_logger.addHandler(console_handler)

shared_logger.propagate = False
