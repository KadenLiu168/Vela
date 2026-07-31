import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def setup_logging(level: str | int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT, force=True)
    logging.getLogger("alembic.runtime.migration").setLevel(logging.WARNING)
