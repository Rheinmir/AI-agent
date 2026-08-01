from demo_agents.weather_agent.agent import NO_DATA, _get_weather_impl


def test_get_weather_known_city():
    result = _get_weather_impl("Hà Nội")
    assert "Hà Nội" in result
    assert "29°C" in result


def test_get_weather_case_and_space_insensitive():
    result = _get_weather_impl("  HÀ NỘI  ")
    assert "Hà Nội" in result


def test_get_weather_unknown_city_returns_no_data_marker():
    result = _get_weather_impl("Atlantis")
    assert result == f"{NO_DATA}:Atlantis"
