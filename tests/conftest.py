import pytest
from src.logger import setup_logger

logger = setup_logger("test")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    logger.info(f"Running test: {item.name}")
