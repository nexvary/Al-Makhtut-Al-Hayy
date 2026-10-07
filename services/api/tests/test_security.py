import pytest

from app.security import UnsafeSourceUrl, validate_public_http_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/manifest.json",
        "http://10.0.0.5/a",
        "http://169.254.169.254/latest/meta-data",
        "file:///etc/passwd",
        "http://localhost/a",
    ],
)
def test_rejects_unsafe_sources(url: str) -> None:
    with pytest.raises(UnsafeSourceUrl):
        validate_public_http_url(url)


def test_accepts_public_hostname() -> None:
    assert validate_public_http_url("https://gallica.bnf.fr/example") == "https://gallica.bnf.fr/example"
