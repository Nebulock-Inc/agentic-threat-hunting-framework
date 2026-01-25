"""ClickHouse connection management and configuration."""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# Custom exceptions
class ClickHouseConfigError(Exception):
    """Configuration validation or loading error."""

    pass


class ClickHouseConnectionError(Exception):
    """Connection establishment or network error."""

    pass


class ClickHouseQueryError(Exception):
    """Query execution error."""

    pass


@dataclass
class ClickHouseConfig:
    """Configuration for ClickHouse connection.

    Attributes:
        host: ClickHouse server hostname
        port: ClickHouse server port (default: 8443 for HTTPS)
        username: Database username (required)
        password: Database password (required)
        database: Default database name (default: "default")
        secure: Use SSL/TLS encryption (default: True)
    """

    host: str
    port: int
    username: str
    password: str
    database: str = "default"
    secure: bool = True

    @classmethod
    def load(cls) -> "ClickHouseConfig":
        """Load configuration from environment variables and config file.

        Precedence order:
        1. Environment variables (highest priority)
        2. Config file (~/.athf/clickhouse.yaml)
        3. Hardcoded defaults (host, port, database only)

        Returns:
            ClickHouseConfig instance

        Raises:
            ClickHouseConfigError: If required credentials are missing
        """
        config_data: Dict[str, Any] = {}

        # Load from config file first
        config_file = Path.home() / ".athf" / "clickhouse.yaml"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    yaml_data = yaml.safe_load(f) or {}
                    clickhouse_section = yaml_data.get("clickhouse", {})
                    config_data.update(clickhouse_section)
            except Exception as e:
                raise ClickHouseConfigError(f"Failed to load config file {config_file}: {e}")

        # Override with environment variables
        if host := os.getenv("CLICKHOUSE_HOST"):
            config_data["host"] = host
        if port := os.getenv("CLICKHOUSE_PORT"):
            config_data["port"] = int(port)
        if user := os.getenv("CLICKHOUSE_USER"):
            config_data["username"] = user
        if password := os.getenv("CLICKHOUSE_PASSWORD"):
            config_data["password"] = password
        if database := os.getenv("CLICKHOUSE_DATABASE"):
            config_data["database"] = database
        if secure := os.getenv("CLICKHOUSE_SECURE"):
            config_data["secure"] = secure.lower() in ("true", "1", "yes")

        # Apply defaults
        config_data.setdefault("host", "ohma99qewu.us-east-1.aws.clickhouse.cloud")
        config_data.setdefault("port", 8443)
        config_data.setdefault("database", "default")
        config_data.setdefault("secure", True)

        # Validate required fields
        if "username" not in config_data or not config_data["username"]:
            raise ClickHouseConfigError(
                "Missing required credential: CLICKHOUSE_USER environment variable not set. "
                "Set credentials with: export CLICKHOUSE_USER='your_username'"
            )
        if "password" not in config_data or not config_data["password"]:
            raise ClickHouseConfigError(
                "Missing required credential: CLICKHOUSE_PASSWORD environment variable not set. "
                "Set credentials with: export CLICKHOUSE_PASSWORD='your_password'"
            )

        return cls(
            host=config_data["host"],
            port=config_data["port"],
            username=config_data["username"],
            password=config_data["password"],
            database=config_data["database"],
            secure=config_data["secure"],
        )

    def to_dict(self, mask_password: bool = True) -> Dict[str, Any]:
        """Convert config to dictionary.

        Args:
            mask_password: If True, replace password with asterisks

        Returns:
            Dictionary representation of config
        """
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": "***" if mask_password else self.password,
            "database": self.database,
            "secure": self.secure,
        }


class ClickHouseConnectionManager:
    """Singleton connection manager for ClickHouse queries.

    Manages a single ClickHouse client instance with lazy initialization.
    Connection is reused across multiple queries within the same process.
    """

    _instance: Optional["ClickHouseConnectionManager"] = None
    _client: Optional[Any] = None  # Type: clickhouse_connect.driver.Client
    _config: Optional[ClickHouseConfig] = None

    def __new__(cls) -> "ClickHouseConnectionManager":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ClickHouseConnectionManager":
        """Get the singleton instance.

        Returns:
            ClickHouseConnectionManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(self) -> Any:
        """Get or create ClickHouse client (lazy initialization).

        Returns:
            ClickHouse client instance

        Raises:
            ClickHouseConnectionError: If connection fails
        """
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> Any:
        """Create ClickHouse client from configuration.

        Returns:
            ClickHouse client instance

        Raises:
            ClickHouseConnectionError: If client creation fails
            ClickHouseConfigError: If configuration is invalid
        """
        try:
            import clickhouse_connect
        except ImportError:
            raise ClickHouseConnectionError(
                "clickhouse-connect not installed. Install with: pip install 'hunt-vault[clickhouse]'"
            )

        # Load configuration
        if self._config is None:
            self._config = ClickHouseConfig.load()

        # Create client with retry logic
        max_retries = 2
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                # Check if running in AWS Lambda (no SSL verification)
                is_lambda = os.environ.get("AWS_EXECUTION_ENV") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")

                client = clickhouse_connect.get_client(
                    host=self._config.host,
                    port=self._config.port,
                    username=self._config.username,
                    password=self._config.password,
                    database=self._config.database,
                    secure=self._config.secure,
                    verify=not bool(is_lambda),  # Disable SSL verification in Lambda
                )
                # Test connection with simple query
                client.command("SELECT 1")
                return client
            except Exception as e:
                if "authentication" in str(e).lower() or "credential" in str(e).lower():
                    # Authentication failures should not retry
                    raise ClickHouseConnectionError(
                        f"Authentication failed: Invalid credentials for user '{self._config.username}'. "
                        f"Check CLICKHOUSE_USER and CLICKHOUSE_PASSWORD environment variables."
                    ) from e
                elif attempt < max_retries - 1:
                    # Network errors: retry once
                    time.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed
                    raise ClickHouseConnectionError(f"Failed to connect to ClickHouse at {self._config.host}: {e}") from e

        # Should never reach here due to max_retries logic, but for type safety
        raise ClickHouseConnectionError("Failed to establish connection after retries")

    def get_config(self) -> ClickHouseConfig:
        """Get current configuration.

        Returns:
            ClickHouseConfig instance

        Raises:
            ClickHouseConfigError: If configuration loading fails
        """
        if self._config is None:
            self._config = ClickHouseConfig.load()
        return self._config

    def close(self) -> None:
        """Close the current connection.

        Note: Typically not needed for CLI use cases (process termination handles cleanup).
        Provided for completeness and testing.
        """
        if self._client is not None:
            try:
                self._client.close()
            except Exception:  # nosec B110 - cleanup, safe to ignore failures
                pass  # Best effort close
            finally:
                self._client = None


class ClickHouseClient:
    """Wrapper for ClickHouse query execution with formatted output."""

    def __init__(self) -> None:
        """Initialize ClickHouse client wrapper."""
        self.manager = ClickHouseConnectionManager.get_instance()

    def execute_query(self, query: str, format: str = "json") -> Dict[str, Any]:
        """Execute query and return formatted results.

        Args:
            query: SQL query to execute
            format: Output format ('json', 'table', 'csv')

        Returns:
            Dictionary with query results and metadata:
            {
                'columns': List[str],
                'data': List[List[Any]],
                'rows': int,
                'elapsed': str,
                'query': str
            }

        Raises:
            ClickHouseQueryError: If query execution fails
        """
        try:
            client = self.manager.get_client()
            start_time = time.time()

            # Execute query
            result = client.query(query)

            elapsed = time.time() - start_time
            elapsed_ms = int(elapsed * 1000)

            # Extract column names and data
            columns = result.column_names
            data = result.result_rows
            rows = len(data)

            # Auto-log metrics to centralized tracker
            try:
                from athf.core.metrics_tracker import MetricsTracker

                MetricsTracker.get_instance().log_clickhouse_query(
                    sql=query,
                    duration_ms=elapsed_ms,
                    rows=rows,
                    status="success",
                )
            except Exception:
                pass  # Never fail query execution due to metrics logging

            return {
                "columns": columns,
                "data": data,
                "rows": rows,
                "elapsed": f"{elapsed:.3f}s",
                "query": query,
            }

        except Exception as e:
            # Log error metrics
            try:
                from athf.core.metrics_tracker import MetricsTracker

                status = "timeout" if "timeout" in str(e).lower() else "error"
                MetricsTracker.get_instance().log_clickhouse_query(
                    sql=query,
                    duration_ms=0,  # Unknown duration on error
                    rows=0,
                    status=status,
                )
            except Exception:
                pass  # Never fail due to metrics logging

            # Check for timeout errors
            if "timeout" in str(e).lower():
                raise ClickHouseQueryError(
                    f"Query timeout: {e}\n\n"
                    "Tips to avoid timeouts:\n"
                    "  1. Add time bounds: WHERE timestamp >= now() - INTERVAL 7 DAY\n"
                    "  2. Start with small LIMIT: LIMIT 100\n"
                    "  3. Filter early: Add WHERE clause before aggregations\n"
                    '  4. Validate query: athf validate query --sql "..."'
                ) from e
            else:
                raise ClickHouseQueryError(f"Query execution failed: {e}") from e

    def test_connection(self) -> Dict[str, Any]:
        """Test ClickHouse connection with simple query.

        Returns:
            Dictionary with connection status and details:
            {
                'success': bool,
                'host': str,
                'port': int,
                'database': str,
                'message': str
            }

        Raises:
            ClickHouseConnectionError: If connection test fails
        """
        try:
            client = self.manager.get_client()
            client.command("SELECT 1")

            config = self.manager.get_config()

            return {
                "success": True,
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "message": "Connection successful",
            }
        except Exception as e:
            config = self.manager.get_config()
            return {
                "success": False,
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "message": f"Connection failed: {e}",
            }
