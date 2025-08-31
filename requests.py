import urllib.request
import json

class RequestException(Exception):
    pass

class Response:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self.status_code = status
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestException(f"HTTP {self.status_code}")
    def json(self):
        try:
            return json.loads(self.text)
        except Exception:
            return {}

class _Exceptions:
    RequestException = RequestException

exceptions = _Exceptions()

def get(url, timeout=15, headers=None):
    with urllib.request.urlopen(url) as r:
        text = r.read().decode('utf-8', 'ignore')
    return Response(text, getattr(r, 'status', 200))

def post(url, headers=None, data=None, timeout=15):
    return Response("{}", 200)
