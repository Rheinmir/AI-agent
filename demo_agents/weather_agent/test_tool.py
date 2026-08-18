from unittest.mock import MagicMock, patch

import requests

from demo_agents.weather_agent.agent import (
    NO_DATA,
    _fetch_current,
    _geocode,
    _get_weather_impl,
    _wmo_description,
)


def _mock_response(json_data):
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


def test_wmo_description_known_code():
    assert _wmo_description(0) == "Trời quang"


def test_wmo_description_unknown_code_has_fallback():
    assert "9999" in _wmo_description(9999)


@patch("demo_agents.weather_agent.agent.requests.get")
def test_geocode_finds_city(mock_get):
    mock_get.return_value = _mock_response(
        {"results": [{"name": "Hà Nội", "latitude": 21.03, "longitude": 105.85}]}
    )
    assert _geocode("ha noi") == {"name": "Hà Nội", "lat": 21.03, "lon": 105.85}


@patch("demo_agents.weather_agent.agent.requests.get")
def test_geocode_no_results_returns_none(mock_get):
    mock_get.return_value = _mock_response({"results": []})
    assert _geocode("Atlantis") is None


@patch("demo_agents.weather_agent.agent.requests.get")
def test_geocode_network_error_returns_none(mock_get):
    mock_get.side_effect = requests.RequestException("timeout")
    assert _geocode("Hà Nội") is None


@patch("demo_agents.weather_agent.agent.requests.get")
def test_fetch_current_returns_temp_and_code(mock_get):
    mock_get.return_value = _mock_response(
        {"current": {"temperature_2m": 29.5, "weather_code": 3}}
    )
    assert _fetch_current(21.03, 105.85) == {"temp_c": 29.5, "code": 3}


@patch("demo_agents.weather_agent.agent.requests.get")
def test_fetch_current_missing_fields_returns_none(mock_get):
    mock_get.return_value = _mock_response({"current": {}})
    assert _fetch_current(21.03, 105.85) is None


@patch("demo_agents.weather_agent.agent._remember_last_city")
@patch("demo_agents.weather_agent.agent._fetch_current")
@patch("demo_agents.weather_agent.agent._geocode")
def test_get_weather_known_city(mock_geocode, mock_fetch, mock_remember):
    mock_geocode.return_value = {"name": "Hà Nội", "lat": 21.03, "lon": 105.85}
    mock_fetch.return_value = {"temp_c": 29.0, "code": 3}
    result = _get_weather_impl("Hà Nội")
    assert result == "Hà Nội: 29.0°C, Nhiều mây"
    mock_remember.assert_called_once_with("Hà Nội")


@patch("demo_agents.weather_agent.agent._remember_last_city")
@patch("demo_agents.weather_agent.agent._fetch_current")
@patch("demo_agents.weather_agent.agent._geocode")
def test_get_weather_case_and_space_insensitive(mock_geocode, mock_fetch, mock_remember):
    mock_geocode.return_value = {"name": "Hà Nội", "lat": 21.03, "lon": 105.85}
    mock_fetch.return_value = {"temp_c": 29.0, "code": 3}
    result = _get_weather_impl("  HÀ NỘI  ")
    assert "Hà Nội" in result
    mock_geocode.assert_called_once_with("HÀ NỘI")


@patch("demo_agents.weather_agent.agent._geocode")
def test_get_weather_unknown_city_returns_no_data_marker(mock_geocode):
    mock_geocode.return_value = None
    result = _get_weather_impl("Atlantis")
    assert result == f"{NO_DATA}:Atlantis"


@patch("demo_agents.weather_agent.agent._fetch_current")
@patch("demo_agents.weather_agent.agent._geocode")
def test_get_weather_forecast_failure_returns_no_data_marker(mock_geocode, mock_fetch):
    mock_geocode.return_value = {"name": "Hà Nội", "lat": 21.03, "lon": 105.85}
    mock_fetch.return_value = None
    result = _get_weather_impl("Hà Nội")
    assert result == f"{NO_DATA}:Hà Nội"
