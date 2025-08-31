import json
from ngbse20.collectors.http_async import _parse_html

HTML = """
<html>
  <head>
    <title>Test Title</title>
    <meta property="article:published_time" content="2024-12-31T12:00:00Z"/>
  </head>
  <body>
    <p>Hello <b>world</b>! This is a test page.</p>
  </body>
</html>
"""

def test_parse_html_to_finding():
    f = _parse_html("https://example.org/a", HTML, "2025-01-01T00:00:00Z")
    assert f.title == "Test Title"
    assert f.published == "2024-12-31T12:00:00Z"
    assert f.domain == "example.org"
    assert len(f.hash) == 64
    d = json.loads(json.dumps(f.__dict__))
    assert d["url"] == "https://example.org/a"
