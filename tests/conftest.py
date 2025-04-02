import sys
import os
import pytest
from src.logger import setup_logger

# Ensure src/ is on the path so imports like `from logger import` work
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

logger = setup_logger("test")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    logger.info(f"Running test: {item.name}")
