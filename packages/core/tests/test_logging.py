import logging
import re
from collections.abc import Iterator

import pytest
from vela_core.logging import LOG_FORMAT, setup_logging


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_disabled = root_logger.disabled
    original_filters = root_logger.filters[:]
    original_handlers = root_logger.handlers[:]

    for handler in original_handlers:
        root_logger.removeHandler(handler)

    yield

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    for handler in original_handlers:
        root_logger.addHandler(handler)

    root_logger.setLevel(original_level)
    root_logger.disabled = original_disabled
    root_logger.filters[:] = original_filters


def test_setup_logging_configures_root_logger() -> None:
    setup_logging()

    root_logger = logging.getLogger()

    assert root_logger.handlers
    assert root_logger.handlers[0].formatter is not None
    assert root_logger.handlers[0].formatter._fmt == LOG_FORMAT


def test_setup_logging_uses_info_level_by_default() -> None:
    setup_logging()

    assert logging.getLogger().level == logging.INFO


def test_setup_logging_accepts_custom_string_level() -> None:
    setup_logging("DEBUG")

    assert logging.getLogger().level == logging.DEBUG


def test_setup_logging_accepts_custom_numeric_level() -> None:
    setup_logging(logging.WARNING)

    assert logging.getLogger().level == logging.WARNING


def test_setup_logging_uses_unified_format(capsys) -> None:
    setup_logging()

    logging.getLogger("vela.test").warning("rotation signal generated")

    captured = capsys.readouterr()
    assert re.match(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} "
        r"WARNING vela\.test rotation signal generated\n",
        captured.err,
    )
