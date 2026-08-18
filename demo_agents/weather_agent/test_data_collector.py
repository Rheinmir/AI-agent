from demo_agents.weather_agent.data_collector import lookup_city_note


def test_known_city_returns_note():
    assert "UTC+7" in lookup_city_note("Ha Noi")


def test_lookup_is_case_and_space_insensitive():
    assert lookup_city_note("  ToKyO  ") == lookup_city_note("tokyo")
    assert lookup_city_note("tokyo") is not None


def test_unknown_city_returns_none():
    assert lookup_city_note("Atlantis") is None


def test_known_city_exact_keys():
    assert lookup_city_note("new york") is not None
    assert lookup_city_note("paris") is not None
    assert lookup_city_note("singapore") is not None
