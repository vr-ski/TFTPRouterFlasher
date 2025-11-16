import os
import tempfile

import pytest


@pytest.fixture
def sample_firmware_file():
    """Create a temporary firmware file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(b"fake firmware content")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def mock_logger():
    """Provide a mock logger for tests."""
    import logging

    logger = logging.getLogger("test_logger")
    return logger


@pytest.fixture
def mock_sleep():
    """Mock time.sleep for all tests to speed them up."""
    with patch("time.sleep"):
        yield
