from ngbse20.utils.hash import content_hash, normalize_text


def test_content_hash_stable():
    a = " Hello   world \n\n!"
    b = "Hello world !"
    assert normalize_text(a) == "Hello world !"
    assert content_hash(a) == content_hash(b)

def test_content_hash_context_changes():
    txt = "same body"
    h1 = content_hash(txt, url="https://example.com/a")
    h2 = content_hash(txt, url="https://example.com/b")
    assert h1 != h2
