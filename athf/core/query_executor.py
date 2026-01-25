"""Query executor for rendering parameterized queries."""

import re
from typing import Any, Dict, List, Tuple

import jinja2


class QueryExecutor:
    """Executor for rendering parameterized SQL queries with Jinja2."""

    def __init__(self) -> None:
        """Initialize query executor with Jinja2 environment."""
        self.template_env = jinja2.Environment(  # nosec B701 - SQL templates, not HTML (XSS not applicable)
            variable_start_string="{{",
            variable_end_string="}}",
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_query(self, query_template: str, parameters: Dict[str, Any]) -> str:
        """Render query template with Jinja2 placeholder substitution.

        Args:
            query_template: Query SQL template with {{placeholder}} syntax
            parameters: Dictionary of parameter values

        Returns:
            Rendered SQL query string
        """
        try:
            template = self.template_env.from_string(query_template)
            rendered = template.render(**parameters)
            # Clean up extra whitespace
            rendered = re.sub(r"\n\s*\n", "\n", rendered)
            return rendered.strip()
        except jinja2.TemplateError as e:
            raise ValueError(f"Template rendering error: {e}") from e

    def validate_parameters(self, query: Dict[str, Any], parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate provided parameters match query placeholders.

        Args:
            query: Query dictionary with placeholders metadata
            parameters: Dictionary of parameter values

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        placeholders = query.get("placeholders", {})

        # Check required parameters (no default value)
        for name, info in placeholders.items():
            if "default" not in info and name not in parameters:
                errors.append(f"Missing required parameter: {name} ({info.get('description', '')})")

        # Check parameter types
        for name, value in parameters.items():
            if name not in placeholders:
                # Optional parameter not defined in query (like organization_id)
                # This is OK - allow extra parameters
                continue

            expected_type = placeholders[name].get("type")
            if expected_type == "integer":
                if not isinstance(value, int):
                    try:
                        int(value)
                    except (TypeError, ValueError):
                        errors.append(f"Parameter {name} must be an integer")
            elif expected_type == "string":
                if not isinstance(value, str):
                    errors.append(f"Parameter {name} must be a string")

        return (len(errors) == 0, errors)

    def apply_defaults(self, query: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing optional parameters.

        Args:
            query: Query dictionary with placeholders metadata
            parameters: Dictionary of parameter values

        Returns:
            Updated parameters dictionary with defaults applied
        """
        placeholders = query.get("placeholders", {})
        result = dict(parameters)

        for name, info in placeholders.items():
            if name not in result and "default" in info:
                result[name] = info["default"]

        return result

    def execute_query(self, query: Dict[str, Any], parameters: Dict[str, Any]) -> str:
        """Render and return executable SQL query.

        Note: This method only renders queries. Use execute_query_with_params()
        to actually execute queries via the ClickHouse Python client.

        Args:
            query: Query dictionary
            parameters: Dictionary of parameter values

        Returns:
            Rendered SQL query string
        """
        # Apply defaults
        params = self.apply_defaults(query, parameters)

        # Validate parameters
        valid, errors = self.validate_parameters(query, params)
        if not valid:
            raise ValueError(f"Parameter validation failed: {', '.join(errors)}")

        # Render query
        query_template = query.get("query", "")
        return self.render_query(query_template, params)

    def execute_query_with_params(
        self, query: Dict[str, Any], parameters: Dict[str, Any], format: str = "json", validate: bool = True
    ) -> Dict[str, Any]:
        """Render and execute parameterized query via ClickHouse Python client.

        Args:
            query: Query dictionary from library
            parameters: Parameter values
            format: Output format (json/table/csv) - used for formatting, not query execution
            validate: Whether to validate query before execution (default: True)

        Returns:
            Query results with metadata:
            {
                'columns': List[str],
                'data': List[List[Any]],
                'rows': int,
                'elapsed': str,
                'query': str
            }

        Raises:
            ValueError: If parameter validation fails or query validation fails
            ClickHouseConnectionError: If connection fails
            ClickHouseQueryError: If query execution fails
        """
        # Import here to avoid circular dependencies
        from athf.core.clickhouse_connection import ClickHouseClient
        from athf.core.query_validator import QueryValidator

        # Render query first
        rendered = self.execute_query(query, parameters)

        # Validate rendered query if requested
        if validate:
            validator = QueryValidator()
            validation = validator.validate(rendered, target="clickhouse")

            if not validation.is_valid:
                error_msg = "Query validation failed:\n" + "\n".join(f"  - {e}" for e in validation.errors)
                raise ValueError(error_msg)

        # Execute via ClickHouseClient
        client = ClickHouseClient()
        results = client.execute_query(rendered, format=format)

        return results
