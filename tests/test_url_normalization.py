from ngbse20.utils.url import extract_domain, normalize_url


def test_normalize_basic():
    u = "HTTP://Example.COM:80/path?b=2&a=1&utm_source=x#frag"
    assert normalize_url(u) == "http://example.com/path?a=1&b=2"


def test_extract_domain():
    assert extract_domain("https://sub.example.co.uk/x") == "example.co.uk"
