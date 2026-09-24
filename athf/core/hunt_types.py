"""Controlled vocabulary for the ``hunt_type`` frontmatter field.

``hunt_type`` classifies *how* a hunt was driven, independent of its ATT&CK
mapping or outcome. It exists so that ``athf hunt stats --by hunt_type`` can
answer "how much of our hunting is hypothesis-driven vs. baseline vs.
model-assisted?" deterministically, instead of grepping titles.
"""

from typing import Optional

HUNT_TYPE_HYPOTHESIS = "hypothesis"
HUNT_TYPE_BASELINE = "baseline"
HUNT_TYPE_MODEL_ASSISTED = "model-assisted"

HUNT_TYPES = (
    HUNT_TYPE_HYPOTHESIS,
    HUNT_TYPE_BASELINE,
    HUNT_TYPE_MODEL_ASSISTED,
)

DEFAULT_HUNT_TYPE = HUNT_TYPE_HYPOTHESIS

# Label used in stats output for hunts with no (or an unknown) hunt_type.
UNCATEGORIZED_LABEL = "uncategorized"

HUNT_TYPE_DESCRIPTIONS = {
    HUNT_TYPE_HYPOTHESIS: "Hypothesis-driven: starts from a specific adversary behavior to test",
    HUNT_TYPE_BASELINE: "Baseline/anomaly: profiles normal activity and looks for deviations",
    HUNT_TYPE_MODEL_ASSISTED: "Model-assisted: driven by ML/statistical models or analytics output",
}


def normalize_hunt_type(value: object) -> Optional[str]:
    """Return the canonical hunt_type string, or ``None`` if missing/unknown.

    Accepts case and separator variations (``Model_Assisted`` -> ``model-assisted``).
    """
    if value is None:
        return None
    text = str(value).strip().lower().replace("_", "-").replace(" ", "-")
    if not text:
        return None
    return text if text in HUNT_TYPES else None


def is_valid_hunt_type(value: object) -> bool:
    """True if ``value`` is exactly one of the controlled vocabulary values."""
    return isinstance(value, str) and value in HUNT_TYPES
