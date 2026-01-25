"""Query suggestion engine for LLM-driven alert triage."""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from athf.core.query_parser import QueryParser


class QuerySuggester:
    """Suggests relevant queries based on alert text analysis."""

    def __init__(self, queries_dir: Path):
        """Initialize query suggester.

        Args:
            queries_dir: Path to queries/ directory
        """
        self.parser = QueryParser(queries_dir)
        self.all_queries = self.parser.load_all_queries()

    def extract_parameters(self, alert_text: str) -> Dict[str, str]:
        """Extract username, hostname, and other parameters from alert text.

        Patterns supported:
        - "user: john.doe" or "username: john.doe" or "User: john.doe"
        - "host: LAPTOP-123" or "hostname: LAPTOP-123" or "Host: LAPTOP-123"
        - "process: powershell.exe" or "Process: powershell.exe"
        - "ip: 8.8.8.8" or "IP: 8.8.8.8"
        - "organization: acme-corp" or "org: acme-corp"

        Args:
            alert_text: Alert text to analyze

        Returns:
            Dictionary of extracted parameters
        """
        parameters = {}

        # Username patterns
        username_patterns = [
            r"(?:user|username|User|USERNAME):\s*([a-zA-Z0-9._@-]+)",
            r"user\s+([a-zA-Z0-9._@-]+)",
            r"for\s+user\s+([a-zA-Z0-9._@-]+)",
        ]
        for pattern in username_patterns:
            if match := re.search(pattern, alert_text):
                parameters["username"] = match.group(1)
                break

        # Hostname patterns
        hostname_patterns = [
            r"(?:host|hostname|Host|HOSTNAME):\s*([a-zA-Z0-9._-]+)",
            r"(?:on|from)\s+host\s+([a-zA-Z0-9._-]+)",
            r"endpoint\s+([a-zA-Z0-9._-]+)",
        ]
        for pattern in hostname_patterns:
            if match := re.search(pattern, alert_text):
                parameters["hostname"] = match.group(1)
                break

        # Process name patterns
        process_patterns = [
            r"(?:process|Process|PROCESS):\s*([a-zA-Z0-9._-]+\.exe)",
            r"(?:process|Process)\s+([a-zA-Z0-9._-]+\.exe)",
            r"execution\s+of\s+([a-zA-Z0-9._-]+\.exe)",
        ]
        for pattern in process_patterns:
            if match := re.search(pattern, alert_text):
                parameters["process_name"] = match.group(1)
                break

        # IP address patterns
        ip_pattern = r"(?:ip|IP|address):\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        if match := re.search(ip_pattern, alert_text):
            parameters["ip_address"] = match.group(1)

        # Organization patterns
        org_patterns = [
            r"(?:organization|org):\s*([a-zA-Z0-9_-]+)",
            r"customer\s+([a-zA-Z0-9_-]+)",
        ]
        for pattern in org_patterns:
            if match := re.search(pattern, alert_text):
                parameters["organization_id"] = match.group(1)
                break

        return parameters

    def suggest_queries(self, alert_text: str, max_suggestions: int = 5) -> List[Tuple[int, Dict[str, Any]]]:
        """Analyze alert text and suggest relevant queries with scores.

        Scoring algorithm:
        - Keyword in query name: +3 points
        - Keyword in query description: +2 points
        - Keyword in query tags: +1 point
        - Extracted parameter matches query placeholder: +5 points

        Args:
            alert_text: Alert text to analyze
            max_suggestions: Maximum number of queries to suggest

        Returns:
            List of tuples (score, query) sorted by relevance
        """
        # Extract parameters
        parameters = self.extract_parameters(alert_text)

        # Extract keywords
        keywords = self._extract_keywords(alert_text)

        # Score queries by relevance
        scored_queries = []
        for query in self.all_queries:
            score = 0

            # Match keywords against query metadata
            for keyword in keywords:
                keyword_lower = keyword.lower()

                # Check name
                if keyword_lower in query.get("name", "").lower():
                    score += 3

                # Check description
                if keyword_lower in query.get("description", "").lower():
                    score += 2

                # Check tags
                query_tags = " ".join(query.get("tags", [])).lower()
                if keyword_lower in query_tags:
                    score += 1

            # Boost score if extracted parameters match query placeholders
            query_placeholders = set(query.get("placeholders", {}).keys())
            for param in parameters.keys():
                if param in query_placeholders:
                    score += 5

            if score > 0:
                scored_queries.append((score, query))

        # Sort by score (descending) and return top N
        scored_queries.sort(key=lambda x: x[0], reverse=True)
        return scored_queries[:max_suggestions]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant security keywords from alert text.

        Args:
            text: Alert text to analyze

        Returns:
            List of security-related keywords found
        """
        keywords = []
        text_lower = text.lower()

        # Security keywords organized by category
        security_terms = {
            # Execution
            "powershell",
            "cmd",
            "bash",
            "shell",
            "script",
            "execution",
            "process",
            # Credential Access
            "credential",
            "password",
            "mimikatz",
            "lsass",
            "procdump",
            "sam",
            "ntds",
            # Network
            "network",
            "connection",
            "lateral",
            "smb",
            "rdp",
            "winrm",
            "exfiltration",
            "c2",
            "command-and-control",
            # General
            "suspicious",
            "malicious",
            "privilege",
            "escalation",
            "file",
            "access",
        }

        for term in security_terms:
            if term in text_lower:
                keywords.append(term)

        # Extract MITRE ATT&CK technique IDs
        technique_pattern = r"T\d{4}(?:\.\d{3})?"
        techniques = re.findall(technique_pattern, text, re.IGNORECASE)
        keywords.extend(techniques)

        return keywords

    def get_parameter_coverage(self, query: Dict[str, Any], extracted_params: Dict[str, str]) -> float:
        """Calculate what percentage of query placeholders can be filled.

        Args:
            query: Query dictionary
            extracted_params: Extracted parameters from alert

        Returns:
            Coverage percentage (0.0 to 1.0)
        """
        placeholders = query.get("placeholders", {})
        if not placeholders:
            return 1.0  # No placeholders, fully covered

        # Count how many placeholders can be filled
        required = [name for name, info in placeholders.items() if "default" not in info]
        optional = [name for name, info in placeholders.items() if "default" in info]

        filled_required = sum(1 for r in required if r in extracted_params)
        filled_optional = sum(1 for o in optional if o in extracted_params)

        # Weight required higher than optional
        total_score = len(required) * 2 + len(optional)
        filled_score = filled_required * 2 + filled_optional

        if total_score == 0:
            return 1.0

        return filled_score / total_score
