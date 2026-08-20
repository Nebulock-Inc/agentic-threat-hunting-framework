"""Tests for MCP server bind-address handling.

The HTTP transports serve unauthenticated tools over the entire workspace, so
the default bind address must stay on loopback and widening it must be an
explicit, warned-about choice.
"""

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("mcp", reason="MCP optional dependency not installed")

from athf.mcp.server import DEFAULT_HOST, is_exposed_host, main  # noqa: E402


class TestIsExposedHost:
    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "[::1]", "LOCALHOST", " 127.0.0.1 "])
    def test_loopback_is_not_exposed(self, host):
        assert is_exposed_host(host) is False

    @pytest.mark.parametrize("host", ["0.0.0.0", "::", "[::]", "*", "", "192.168.1.10", "10.0.0.5"])
    def test_routable_and_wildcard_are_exposed(self, host):
        assert is_exposed_host(host) is True


class TestMainBindAddress:
    """`main()` must not bind beyond loopback unless explicitly told to."""

    def _run(self, transport, **kwargs):
        server = MagicMock()
        server.settings = MagicMock()
        with patch("athf.mcp.server.create_server", return_value=server):
            main(transport=transport, **kwargs)
        return server

    def test_default_host_is_loopback(self):
        """Regression: this was hardcoded to 0.0.0.0, exposing the workspace."""
        server = self._run("streamable-http")

        assert server.settings.host == DEFAULT_HOST
        assert DEFAULT_HOST == "127.0.0.1"

    def test_default_host_is_loopback_for_sse(self):
        server = self._run("sse")

        assert server.settings.host == DEFAULT_HOST

    def test_explicit_host_is_honored(self):
        server = self._run("streamable-http", host="0.0.0.0")  # nosec B104

        assert server.settings.host == "0.0.0.0"  # nosec B104

    def test_port_is_applied(self):
        server = self._run("streamable-http", port=9999)

        assert server.settings.port == 9999

    def test_stdio_does_not_touch_network_settings(self):
        """stdio has no listening socket, so host/port must never be assigned."""

        class Settings:
            pass

        server = MagicMock()
        server.settings = Settings()
        with patch("athf.mcp.server.create_server", return_value=server):
            main(transport="stdio")

        server.run.assert_called_once_with(transport="stdio")
        assert not hasattr(server.settings, "host")
        assert not hasattr(server.settings, "port")

    def test_exposed_host_logs_warning(self, caplog):
        with caplog.at_level("WARNING", logger="athf.mcp.server"):
            self._run("streamable-http", host="0.0.0.0")  # nosec B104

        assert "UNAUTHENTICATED" in caplog.text
        assert "0.0.0.0" in caplog.text

    def test_loopback_host_logs_no_warning(self, caplog):
        with caplog.at_level("WARNING", logger="athf.mcp.server"):
            self._run("streamable-http")

        assert "UNAUTHENTICATED" not in caplog.text
