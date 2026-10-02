"""Who produced a confirmation, and could they have done the work.

The prose check on ``confirmation`` was measured against a labeled corpus and
hit a floor it cannot cross: "cross-validated by running a second query against
the same table" is grammatically indistinguishable from real corroboration. No
pattern set separates them, because reading a confirmation cannot establish that
the work behind it happened.

What is not forgeable by an agent that can only run queries is *who produced the
finding*. So capabilities live here — in workspace config, loaded from disk —
never in the finding. An LLM emits ``verdict`` / ``evidence`` / ``confirmation``;
it cannot rewrite the config that says what its producer can reach. That
separation is the gate. A producer declaring only query access is capped at
``suspected`` by construction, permanently, without anyone grading its prose.

Declared capability is still forgeable by a human editing config. That is the
accepted residual: the lie moves out of unfalsifiable prose into a separate file,
in its own commit, contradicted by source an auditor can read.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, FrozenSet, Mapping, Optional

# Capabilities that only read the log corpus. Declaring one is honest — querying
# is real work — but it can never be a *confirmation* method, because the corpus
# is the thing being confirmed. Naming these explicitly is what stops a
# corpus-only producer from satisfying the gate by declaring what it already does.
CORPUS_ONLY_CAPABILITIES: FrozenSet[str] = frozenset(
    {
        "clickhouse_query",
        "dataset_query",
        "log_query",
        "log_review",
        "siem_search",
        "splunk_search",
        "sql_query",
        "telemetry_review",
    }
)

# Keys that would carry capability inside the finding itself. Present means an
# author tried to declare their own reach in the same payload as the claim, which
# is the forgeable field this module exists to replace. Refused rather than
# ignored: silently dropping it would let the author believe it counted.
SELF_DECLARATION_KEYS = ("analyst_capabilities", "capabilities", "producer_capabilities")


class ProducerRegistry:
    """The declared capabilities of each producer, loaded from workspace config.

    Constructed from config, never from a hunt file. ``athf hunt validate``
    already loads workspace config, so the gate can reach this without the
    finding supplying any part of it.
    """

    def __init__(self, producers: Optional[Mapping[str, Any]] = None):
        self._capabilities: Dict[str, FrozenSet[str]] = {}
        for name, spec in (producers or {}).items():
            declared = spec.get("capabilities") if isinstance(spec, Mapping) else None
            if not isinstance(declared, (list, tuple, set, frozenset)):
                declared = ()
            self._capabilities[str(name)] = frozenset(
                str(c).strip().lower() for c in declared if isinstance(c, str) and c.strip()
            )

    @classmethod
    def from_config(cls, config: Optional[Mapping[str, Any]]) -> "ProducerRegistry":
        """Build from a loaded ``.athfconfig.yaml`` mapping.

        A config with no ``provenance`` section yields an empty registry — every
        workspace already on PyPI. Empty is restrictive, not permissive: nothing
        is registered, so nothing reaches ``confirmed``.
        """
        section = (config or {}).get("provenance")
        producers = section.get("producers") if isinstance(section, Mapping) else None
        return cls(producers if isinstance(producers, Mapping) else {})

    def knows(self, producer: Any) -> bool:
        """Return ``True`` when ``producer`` is declared in config."""
        return isinstance(producer, str) and producer in self._capabilities

    def knows_folded(self, name: str) -> bool:
        """Return ``True`` when ``name`` matches a declared producer, ignoring case.

        Used by the attestation check, which asks whether a name refers to a
        producer at all rather than looking its capabilities up. Case-insensitive
        because ``attested_by: Analyst`` names the same tool as ``analyst``, and a
        rule one shift key wide is not a rule.
        """
        return name in {p.strip().lower() for p in self._capabilities}

    def capabilities_for(self, producer: Any) -> FrozenSet[str]:
        """Return the declared capabilities, or empty for an unknown producer."""
        if not isinstance(producer, str):
            return frozenset()
        return self._capabilities.get(producer, frozenset())

    def is_empty(self) -> bool:
        return not self._capabilities

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"ProducerRegistry({sorted(self._capabilities)!r})"


def confirming_capabilities(registry: ProducerRegistry, producer: Any) -> FrozenSet[str]:
    """Return the producer's capabilities that could actually confirm something."""
    return registry.capabilities_for(producer) - CORPUS_ONLY_CAPABILITIES


def load_registry(
    workspace: Optional[Path] = None, *, root: Optional[Path] = None
) -> ProducerRegistry:
    """Load the registry from workspace config, or an empty one.

    Both enforcement surfaces call this so they agree: ``athf hunt validate``
    rejects what the tally declines to count. They decided this separately once
    before, and a ``confirmed`` entry whose confirmation read ``ok`` was refused
    by validate and credited by the dashboard in the same breath.

    A missing or unreadable config yields an empty registry, which is restrictive.
    Failing closed here is deliberate: an unparseable config must not become a
    reason that ``confirmed`` starts passing.

    ``root`` is the workspace root. When given, the walk stops there and the
    hunt-tree test is evaluated *relative* to it, so an unrelated ancestor
    directory that happens to be named ``hunts`` (e.g. a workspace under
    ``/srv/hunts/``) no longer skips the workspace root's own config. Callers
    that know the root should always pass it; the ``None`` default keeps the
    older absolute-path behavior for callers that don't.
    """
    import yaml

    base = Path(workspace) if workspace else Path.cwd()
    root = Path(root) if root is not None else None
    # Walk up: hunt files live several directories below the workspace root
    # (hunts/production/2026/Q2/H-0042.md), and the config is at the root.
    for parent in (base, *base.parents):
        if _inside_hunt_tree(parent, root):
            continue
        # Root before config/: `athf init` writes the config/ copy, so most
        # workspaces have both, and the root file is the one the docs tell hunters
        # to edit. Reading config/ first made an edited root declaration invisible.
        for candidate in (parent / ".athfconfig.yaml", parent / "config" / ".athfconfig.yaml"):
            if not candidate.exists():
                continue
            try:
                with open(candidate, "r", encoding="utf-8") as handle:
                    return ProducerRegistry.from_config(yaml.safe_load(handle) or {})
            except (OSError, yaml.YAMLError):
                return ProducerRegistry()
        # The root's config is the last one the workspace legitimately owns.
        # Never keep walking into ancestors above it looking for a stray config.
        if root is not None and parent == root:
            break
    return ProducerRegistry()


def _inside_hunt_tree(directory: Path, root: Optional[Path] = None) -> bool:
    """Return ``True`` for a directory inside the workspace's ``hunts/`` tree.

    Config found there is ignored. The walk starts from a hunt file's own
    directory, which is a place the finding author writes to — so without this,
    an agent drops ``.athfconfig.yaml`` beside ``H-0042.md``, declares itself
    capable of host forensics, and validation accepts the ``confirmed``. That is
    a self-declaration with a different filename, and the whole reason
    capabilities live in config is that the claim cannot reach the grant.

    With ``root`` the test runs on the path *below* the workspace root, so a
    ``hunts`` component sitting above the root (an unrelated ancestor) is no
    longer mistaken for the workspace's own hunt tree — that false match made
    ``load_registry`` skip the real root config and left ``confirmed``
    unreachable workspace-wide with no diagnostic. A directory at or above the
    root is never inside the tree. Without ``root`` the older behavior stands:
    any ancestor named ``hunts`` skips, which also means a workspace whose own
    root is named ``hunts`` fails closed.
    """
    if root is None:
        return "hunts" in directory.parts
    try:
        relative = directory.relative_to(root)
    except ValueError:
        return False
    return "hunts" in relative.parts


__all__ = [
    "CORPUS_ONLY_CAPABILITIES",
    "SELF_DECLARATION_KEYS",
    "ProducerRegistry",
    "confirming_capabilities",
    "load_registry",
]
