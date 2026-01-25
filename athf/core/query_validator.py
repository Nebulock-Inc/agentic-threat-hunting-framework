"""Query validation for ClickHouse SQL safety checks."""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidationResult:
    """Result of query validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    estimated_row_count: Optional[int] = None


class QueryValidator:
    """Validates SQL queries for ClickHouse MCP safety requirements.

    Enforces rules from integrations/clickhouse/README.md:
    - Time bounds required (7 days max initially)
    - LIMIT clause required (start with 100)
    - No SQL comments (breaks MCP)
    - Early filtering recommended
    - Avoid multiple DISTINCT
    """

    # Time-related patterns
    TIME_PATTERNS = [
        r"toDate\(.+\)\s*>=\s*",  # toDate(timestamp) >= ...
        r"toDateTime\(.+\)\s*>=\s*",  # toDateTime(timestamp) >= ...
        r"timestamp\s*>=\s*",  # timestamp >= ...
        r"time\s*>=\s*",  # time >= ...
        r"WHERE.+>=\s*now\(\)\s*-\s*INTERVAL",  # WHERE ... >= now() - INTERVAL
        r"WHERE.+>=\s*subtractDays",  # WHERE ... >= subtractDays()
        r"WHERE.+>=\s*subtractHours",  # WHERE ... >= subtractHours()
        r">=\s*toDateTime\(",  # >= toDateTime('...')
        r">=\s*'[\d\-:\s]+'",  # >= '2025-01-15 00:00:00' or >= '2025-01-15'
        r"<=\s*'[\d\-:\s]+'",  # <= '2025-01-15 23:59:59'
        r"BETWEEN\s+['\"]\d{4}-\d{2}-\d{2}",  # BETWEEN '2025-01-15' AND '2025-01-22'
        r"=\s*'[\d\-:\s]+'",  # = '2025-01-15' (exact date match)
    ]

    # LIMIT patterns
    LIMIT_PATTERNS = [
        r"LIMIT\s+\d+",  # LIMIT 100
        r"TOP\s+\d+",  # TOP 100 (alternative syntax)
    ]

    # Comment patterns (these break MCP)
    COMMENT_PATTERNS = [
        r"--",  # Single-line comment
        r"/\*.*?\*/",  # Multi-line comment
    ]

    # Expensive operations
    EXPENSIVE_PATTERNS = [
        (r"DISTINCT.*DISTINCT", "Multiple DISTINCT clauses detected (expensive operation)"),
        (r"SELECT\s+\*\s+FROM", "SELECT * detected (prefer explicit columns for performance)"),
        (r"GROUP BY.+ORDER BY.+LIMIT", "GROUP BY + ORDER BY without early filtering may be slow"),
    ]

    def __init__(self) -> None:
        """Initialize the query validator."""
        pass

    def validate(self, query: str, target: str = "clickhouse") -> ValidationResult:
        """Validate a SQL query against safety requirements.

        Args:
            query: The SQL query to validate
            target: The target database (currently only 'clickhouse' supported)

        Returns:
            ValidationResult with validation status and messages
        """
        if target != "clickhouse":
            return ValidationResult(
                is_valid=False,
                errors=[f"Unsupported target: {target} (only 'clickhouse' is currently supported)"],
                warnings=[],
                info=[],
            )

        errors: List[str] = []
        warnings: List[str] = []
        info: List[str] = []

        # Normalize query (remove extra whitespace)
        normalized = " ".join(query.split())

        # 1. CRITICAL: Check for SQL comments (breaks MCP)
        if self._has_comments(query):
            errors.append("SQL comments detected (-- or /* */). Comments break MCP - remove them before execution.")

        # 2. CRITICAL: Check for time bounds
        if not self._has_time_bounds(normalized):
            errors.append(
                "No time bounds detected. Add time constraints (e.g., WHERE timestamp >= now() - INTERVAL 7 DAY "
                "or WHERE time >= '2025-01-15 00:00:00') to prevent timeouts."
            )
        else:
            info.append("Time bounds detected")

        # 3. CRITICAL: Check for LIMIT clause
        limit_value = self._extract_limit(normalized)
        if limit_value is None:
            errors.append("No LIMIT clause detected. Add LIMIT (start with 100, max 1000) to prevent large result sets.")
        else:
            if limit_value <= 100:
                info.append(f"LIMIT {limit_value} (safe - good starting point)")
            elif limit_value <= 1000:
                info.append(f"LIMIT {limit_value} (moderate - may need refinement if exactly {limit_value} rows returned)")
            else:
                warnings.append(
                    f"LIMIT {limit_value} is high. Consider starting with LIMIT 100 and increasing if needed "
                    "(progressive strategy)."
                )

        # 4. Check for early filtering (WHERE clause before aggregations)
        if not self._has_early_filtering(normalized):
            warnings.append(
                "No early filtering detected. Add WHERE clause before aggregations (GROUP BY, DISTINCT) "
                "for better performance."
            )
        else:
            info.append("Early filtering detected (WHERE clause present)")

        # 5. Check for expensive operations
        for pattern, message in self.EXPENSIVE_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                warnings.append(message)

        # 6. Check for query structure (FROM clause required)
        if not re.search(r"FROM\s+\w+", normalized, re.IGNORECASE):
            errors.append("No FROM clause detected. Query must select from a table.")

        # Determine overall validity
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=info,
        )

    def _has_comments(self, query: str) -> bool:
        """Check if query contains SQL comments."""
        # Check for single-line comments
        if "--" in query:
            return True

        # Check for multi-line comments
        if re.search(r"/\*.*?\*/", query, re.DOTALL):
            return True

        return False

    def _has_time_bounds(self, normalized_query: str) -> bool:
        """Check if query has time constraints."""
        for pattern in self.TIME_PATTERNS:
            if re.search(pattern, normalized_query, re.IGNORECASE):
                return True
        return False

    def _extract_limit(self, normalized_query: str) -> Optional[int]:
        """Extract LIMIT value from query."""
        # Check for LIMIT clause
        limit_match = re.search(r"LIMIT\s+(\d+)", normalized_query, re.IGNORECASE)
        if limit_match:
            return int(limit_match.group(1))

        # Check for TOP clause (alternative syntax)
        top_match = re.search(r"TOP\s+(\d+)", normalized_query, re.IGNORECASE)
        if top_match:
            return int(top_match.group(1))

        return None

    def _has_early_filtering(self, normalized_query: str) -> bool:
        """Check if query has WHERE clause before aggregations."""
        # Look for WHERE clause
        where_match = re.search(r"WHERE", normalized_query, re.IGNORECASE)
        if not where_match:
            return False

        # Check if WHERE comes before GROUP BY or DISTINCT
        where_pos = where_match.start()

        group_match = re.search(r"GROUP\s+BY", normalized_query, re.IGNORECASE)
        if group_match and group_match.start() < where_pos:
            return False

        distinct_match = re.search(r"DISTINCT", normalized_query, re.IGNORECASE)
        if distinct_match and distinct_match.start() < where_pos:
            return False

        return True

    def suggest_improvements(self, query: str, validation: ValidationResult) -> List[str]:
        """Suggest improvements based on validation results.

        Args:
            query: The original query
            validation: The validation result

        Returns:
            List of suggested improvements
        """
        suggestions: List[str] = []

        # If missing time bounds, suggest adding them
        if any("time bounds" in error.lower() for error in validation.errors):
            suggestions.append(
                "Add time bounds: WHERE timestamp >= now() - INTERVAL 7 DAY "
                "or WHERE time >= '2025-01-15 00:00:00' AND time <= '2025-01-22 23:59:59'"
            )

        # If missing LIMIT, suggest adding it
        if any("limit" in error.lower() for error in validation.errors):
            suggestions.append("Add LIMIT clause: LIMIT 100 (progressive strategy)")

        # If has comments, suggest removing them
        if any("comment" in error.lower() for error in validation.errors):
            suggestions.append("Remove SQL comments (-- or /* */) - they break ClickHouse MCP")

        # If missing early filtering
        if any("early filtering" in warning.lower() for warning in validation.warnings):
            suggestions.append(
                "Add WHERE clause before aggregations for better performance: " "WHERE timestamp >= ... AND condition"
            )

        # If SELECT *
        if any("SELECT \\*" in warning for warning in validation.warnings):
            suggestions.append("Replace SELECT * with explicit columns: SELECT column1, column2, ...")

        return suggestions
