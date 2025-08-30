import urllib.request

class Response:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self.status_code = status


def get(url, timeout=15, headers=None):
    with urllib.request.urlopen(url) as r:
        text = r.read().decode('utf-8', 'ignore')
    return Response(text, getattr(r, 'status', 200))
