"""Query library parser for YAML query files."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class QueryParser:
    """Parser for query library YAML files."""

    def __init__(self, queries_dir: Path):
        """Initialize query parser with queries directory.

        Args:
            queries_dir: Path to queries/ directory containing YAML files
        """
        self.queries_dir = Path(queries_dir)
        self._queries_cache: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def load_all_queries(self) -> List[Dict[str, Any]]:
        """Load all queries from YAML files in queries/ directory.

        Returns:
            List of query dictionaries
        """
        if self._loaded and self._queries_cache:
            return list(self._queries_cache.values())

        all_queries = []
        yaml_files = sorted(self.queries_dir.glob("*.yaml"))

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data or not isinstance(data, dict):
                    continue

                category = data.get("category")
                queries = data.get("queries", [])

                for query in queries:
                    # Add category from file-level metadata
                    query["category"] = category
                    query["source_file"] = yaml_file.name

                    # Cache by query_id
                    query_id = query.get("query_id")
                    if query_id:
                        self._queries_cache[query_id] = query

                    all_queries.append(query)

            except Exception as e:
                # Log error but continue loading other files
                print(f"Warning: Failed to parse {yaml_file}: {e}")
                continue

        self._loaded = True
        return all_queries

    def get_query_by_id(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve query metadata by Q-XXXX ID.

        Args:
            query_id: Query ID (e.g., Q-USER-001)

        Returns:
            Query dictionary or None if not found
        """
        if not self._loaded:
            self.load_all_queries()

        return self._queries_cache.get(query_id)

    def search_queries(self, keyword: str) -> List[Dict[str, Any]]:
        """Search queries by keyword in name, description, tags.

        Args:
            keyword: Search keyword

        Returns:
            List of matching query dictionaries
        """
        all_queries = self.load_all_queries()
        keyword_lower = keyword.lower()
        results = []

        for query in all_queries:
            # Search in name
            if keyword_lower in query.get("name", "").lower():
                results.append(query)
                continue

            # Search in description
            if keyword_lower in query.get("description", "").lower():
                results.append(query)
                continue

            # Search in tags
            tags = query.get("tags", [])
            if any(keyword_lower in tag.lower() for tag in tags):
                results.append(query)
                continue

        return results

    def filter_queries(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Filter queries by category or tags.

        Args:
            category: Category to filter by (e.g., "user-activity")
            tags: List of tags to filter by (any match)

        Returns:
            List of matching query dictionaries
        """
        all_queries = self.load_all_queries()
        results = all_queries

        if category:
            results = [q for q in results if q.get("category") == category]

        if tags:
            tag_set = {t.lower() for t in tags}
            results = [q for q in results if any(qt.lower() in tag_set for qt in q.get("tags", []))]

        return results

    def validate_query(self, query: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate query structure and required fields.

        Args:
            query: Query dictionary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Required fields
        required_fields = ["query_id", "name", "description", "query"]
        for field in required_fields:
            if not query.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate query_id format: Q-[A-Z]+-[0-9]+
        query_id = query.get("query_id", "")
        if not re.match(r"^Q-[A-Z]+-\d+$", query_id):
            errors.append(f"Invalid query_id format: {query_id} (expected Q-[CATEGORY]-[NUMBER])")

        # Validate query includes time bounds
        query_sql = query.get("query", "")
        has_time_bound = "INTERVAL" in query_sql.upper() or "timestamp >=" in query_sql or "timestamp BETWEEN" in query_sql
        if not has_time_bound:
            errors.append("Query missing time constraint (INTERVAL or timestamp >=)")

        # Validate query includes LIMIT clause
        if "LIMIT" not in query_sql.upper():
            errors.append("Query missing LIMIT clause")

        # Validate placeholders match {{}} in query
        placeholders_defined = set(query.get("placeholders", {}).keys())
        placeholders_in_query = set(re.findall(r"\{\{(\w+)\}\}", query_sql))

        # Check for placeholders used in query but not defined
        undefined = placeholders_in_query - placeholders_defined
        if undefined:
            errors.append(f"Placeholders used but not defined: {', '.join(undefined)}")

        # Check for placeholders defined but not used (warning, not error)
        unused = placeholders_defined - placeholders_in_query
        if unused:
            # This is just a warning, not an error
            pass

        return (len(errors) == 0, errors)

    def get_categories(self) -> List[str]:
        """Get list of all unique categories in query library.

        Returns:
            List of category names
        """
        all_queries = self.load_all_queries()
        categories: set[str] = {cat for q in all_queries if (cat := q.get("category")) is not None}
        return sorted(categories)

    def get_all_tags(self) -> List[str]:
        """Get list of all unique tags in query library.

        Returns:
            List of tag names
        """
        all_queries = self.load_all_queries()
        tags = set()
        for query in all_queries:
            tags.update(query.get("tags", []))
        return sorted(tags)
