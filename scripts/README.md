# ATHF Scripts

Utility scripts for the Agentic Threat Hunting Framework.

---

## Hunt Metrics Gap Checking

**The metrics gap checking functionality has moved to the CLI:**

```bash
# Human-readable report (default)
athf hunt metrics gaps

# JSON output (for automation)
athf hunt metrics gaps --format json

# CSV output (for spreadsheets)
athf hunt metrics gaps --format csv

# CI/CD mode (strict validation)
athf hunt metrics gaps --strict
```

**See:** `athf hunt metrics gaps --help` for full documentation.

---

## verify_packaging.py

Python script to verify package installation and distribution.

```bash
python scripts/verify_packaging.py
```

---

## Related Documentation

- **Metrics System:** `athf/core/hunt_metrics.py`
- **Metrics CLI:** `athf hunt metrics --help`
- **Hunt Schema:** Hunt file frontmatter requirements

---

**Last Updated:** 2026-11-17  
**Maintained By:** ATHF Framework Team
