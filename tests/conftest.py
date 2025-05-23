import pytest

@pytest.fixture(scope="session", autouse=True)
def download_nltk_punkt():
    import nltk
    nltk.download("punkt") 