"""
pytest 설정 파일
"""

import pytest
import os
import sys

# 테스트 환경 변수 설정
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-api-key")
os.environ.setdefault("GENERATION_MODEL", "gemini-3-flash-preview")


@pytest.fixture
def mock_llm():
    """Mock LLM 인스턴스"""
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def mock_vector_store():
    """Mock Vector Store"""
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture  
def mock_retriever():
    """Mock Retriever"""
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def mock_compatibility_engine():
    """Mock Compatibility Engine"""
    from unittest.mock import MagicMock
    return MagicMock()
