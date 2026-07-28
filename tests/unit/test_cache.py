from onecent.repositories.data import cache_key


def test_cache_key_stable_and_parameter_sensitive() -> None:
    first = cache_key("extract", "https://example.com/", "links=False")
    assert first == cache_key("extract", "https://example.com/", "links=False")
    assert first != cache_key("extract", "https://example.com/", "links=True")
