from unittest.mock import MagicMock, patch
from app.services.monitor import probe_website_sync


def test_probe_website_sync_success():
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.history = []
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        res = probe_website_sync("https://adani.com", expected_status_codes="200,201")
        assert res["status"] in ("UP", "WARNING")
        assert res["http_status"] == 200


def test_probe_website_sync_http_500():
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.history = []
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        res = probe_website_sync("https://adani.com", expected_status_codes="200")
        assert res["status"] == "DOWN"
        assert res["http_status"] == 500
        assert res["error_type"] == "HTTP 5xx"
