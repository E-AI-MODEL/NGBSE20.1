import logging

def configure_logging(level: str = "INFO") -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
