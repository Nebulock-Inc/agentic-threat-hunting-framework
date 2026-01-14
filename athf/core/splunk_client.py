"""Splunk REST API client for ATHF.

This module provides direct Splunk API integration using authentication tokens.
Use this when MCP integration is not available or for programmatic access.
"""

import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SplunkClient:
    """Client for Splunk REST API operations.

    Args:
        host: Splunk host (e.g., "splunk.example.com" or "https://splunk.example.com:8089")
        token: Splunk authentication token
        verify_ssl: Whether to verify SSL certificates (default: True)
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> client = SplunkClient(host="splunk.example.com", token="your-token")
        >>> results = client.search("index=main | head 10", max_count=10)
        >>> for event in results:
        ...     print(event)
    """

    def __init__(self, host: str, token: str, verify_ssl: bool = True, timeout: int = 30):
        # Normalize host URL
        if not host.startswith(("http://", "https://")):
            host = f"https://{host}"
        if ":8089" not in host and not host.endswith(":8089"):
            # Add default management port if not specified
            host = host.rstrip("/") + ":8089"

        self.base_url = host.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Create session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_response: bool = True,
    ) -> Any:
        """Make HTTP request to Splunk API.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Form data for POST requests
            json_response: Whether to parse JSON response

        Returns:
            Response data (parsed JSON or raw response)

        Raises:
            requests.HTTPError: If request fails
        """
        url = urljoin(self.base_url, endpoint)

        response = self.session.request(
            method=method, url=url, params=params, data=data, verify=self.verify_ssl, timeout=self.timeout
        )

        response.raise_for_status()

        if json_response:
            return response.json()
        return response

    def test_connection(self) -> Dict[str, Any]:
        """Test connection and authentication to Splunk.

        Returns:
            Dict with server info if successful

        Raises:
            requests.HTTPError: If authentication fails
        """
        return self._request("GET", "/services/server/info", params={"output_mode": "json"})  # type: ignore[no-any-return]

    def get_indexes(self) -> List[str]:
        """List available Splunk indexes.

        Returns:
            List of index names
        """
        response = self._request("GET", "/services/data/indexes", params={"output_mode": "json"})
        return [entry["name"] for entry in response.get("entry", [])]

    def search(
        self,
        query: str,
        earliest_time: str = "-24h",
        latest_time: str = "now",
        max_count: int = 100,
        output_mode: str = "json",
    ) -> List[Dict[str, Any]]:
        """Execute a Splunk search query (oneshot search for quick results).

        Args:
            query: SPL search query
            earliest_time: Start time (e.g., "-24h", "2024-01-01T00:00:00")
            latest_time: End time (e.g., "now", "2024-01-02T00:00:00")
            max_count: Maximum number of results to return
            output_mode: Output format (json, xml, csv)

        Returns:
            List of search results

        Example:
            >>> results = client.search(
            ...     'index=main sourcetype=linux_secure "Failed password"',
            ...     earliest_time="-1h",
            ...     max_count=50
            ... )
        """
        # Use oneshot search for quick results (no job creation)
        data = {
            "search": query if query.startswith("search") else f"search {query}",
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "max_count": max_count,
            "output_mode": output_mode,
        }

        response = self._request("POST", "/services/search/jobs/oneshot", data=data)

        # Extract results from response
        results = []
        if "results" in response:
            results = response["results"]
        elif "entry" in response:
            # Handle alternative response format
            for entry in response["entry"]:
                if "content" in entry:
                    results.append(entry["content"])

        return results

    def create_search_job(self, query: str, earliest_time: str = "-24h", latest_time: str = "now", **kwargs: Any) -> str:
        """Create an async search job for long-running queries.

        Args:
            query: SPL search query
            earliest_time: Start time
            latest_time: End time
            **kwargs: Additional search parameters

        Returns:
            Search job ID (sid)

        Example:
            >>> sid = client.create_search_job(
            ...     'index=* | stats count by sourcetype',
            ...     earliest_time="-7d"
            ... )
            >>> results = client.get_search_results(sid)
        """
        data = {
            "search": query if query.startswith("search") else f"search {query}",
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "output_mode": "json",
            **kwargs,
        }

        response = self._request("POST", "/services/search/jobs", data=data)

        # Extract search ID from response
        if "sid" in response:
            return response["sid"]  # type: ignore[no-any-return]
        elif "entry" in response and len(response["entry"]) > 0:
            return response["entry"][0]["name"]  # type: ignore[no-any-return]

        raise ValueError("Could not extract search job ID from response")

    def get_search_job_status(self, sid: str) -> Dict[str, Any]:
        """Get status of a search job.

        Args:
            sid: Search job ID

        Returns:
            Dict with job status information
        """
        return self._request("GET", f"/services/search/jobs/{sid}", params={"output_mode": "json"})  # type: ignore[no-any-return]

    def wait_for_search_job(self, sid: str, poll_interval: int = 2, max_wait: int = 300) -> bool:
        """Wait for search job to complete.

        Args:
            sid: Search job ID
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait

        Returns:
            True if job completed, False if timeout
        """
        elapsed = 0
        while elapsed < max_wait:
            status = self.get_search_job_status(sid)

            # Check if job is done
            if "entry" in status and len(status["entry"]) > 0:
                content = status["entry"][0].get("content", {})
                if content.get("isDone"):
                    return True

            time.sleep(poll_interval)
            elapsed += poll_interval

        return False

    def get_search_results(
        self, sid: str, offset: int = 0, count: int = 100, output_mode: str = "json"
    ) -> List[Dict[str, Any]]:
        """Get results from a completed search job.

        Args:
            sid: Search job ID
            offset: Result offset (for pagination)
            count: Number of results to return
            output_mode: Output format

        Returns:
            List of search results
        """
        params = {
            "output_mode": output_mode,
            "offset": offset,
            "count": count,
        }

        response = self._request("GET", f"/services/search/jobs/{sid}/results", params=params)

        results = []
        if "results" in response:
            results = response["results"]
        elif "entry" in response:
            for entry in response["entry"]:
                if "content" in entry:
                    results.append(entry["content"])

        return results

    def delete_search_job(self, sid: str) -> None:
        """Delete a search job.

        Args:
            sid: Search job ID
        """
        self._request("DELETE", f"/services/search/jobs/{sid}")

    def search_async(
        self,
        query: str,
        earliest_time: str = "-24h",
        latest_time: str = "now",
        max_results: int = 100,
        wait: bool = True,
        max_wait: int = 300,
    ) -> List[Dict[str, Any]]:
        """Execute a search asynchronously and return results.

        This is useful for longer-running queries that may timeout with oneshot.

        Args:
            query: SPL search query
            earliest_time: Start time
            latest_time: End time
            max_results: Maximum results to return
            wait: Whether to wait for job completion
            max_wait: Maximum seconds to wait for job

        Returns:
            List of search results

        Example:
            >>> results = client.search_async(
            ...     'index=* | stats count by sourcetype',
            ...     earliest_time="-7d",
            ...     max_results=1000
            ... )
        """
        # Create search job
        sid = self.create_search_job(query, earliest_time, latest_time)

        try:
            if wait:
                # Wait for completion
                if not self.wait_for_search_job(sid, max_wait=max_wait):
                    raise TimeoutError(f"Search job {sid} did not complete within {max_wait}s")

            # Get results
            return self.get_search_results(sid, count=max_results)

        finally:
            # Clean up search job
            try:
                self.delete_search_job(sid)
            except Exception:
                pass  # Ignore cleanup errors


def create_client_from_env() -> SplunkClient:
    """Create Splunk client from environment variables.

    Environment variables:
        SPLUNK_HOST: Splunk host
        SPLUNK_TOKEN: Authentication token
        SPLUNK_VERIFY_SSL: Whether to verify SSL (default: true)

    Returns:
        Configured SplunkClient instance

    Raises:
        ValueError: If required environment variables are missing
    """
    import os

    host = os.getenv("SPLUNK_HOST")
    token = os.getenv("SPLUNK_TOKEN")

    if not host:
        raise ValueError("SPLUNK_HOST environment variable is required")
    if not token:
        raise ValueError("SPLUNK_TOKEN environment variable is required")

    verify_ssl = os.getenv("SPLUNK_VERIFY_SSL", "true").lower() in ("true", "1", "yes")

    return SplunkClient(host=host, token=token, verify_ssl=verify_ssl)
