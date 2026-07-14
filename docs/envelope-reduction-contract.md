# MCP Envelope-Reduction Response Contract

**Status:** Adopted (v0.15.0)
**Applies to:** ATHF MCP tools and any cooperating CLI command whose stdout becomes part of an LLM tool result.

## Why this exists

LLM tool calls accumulate: each round, the response payload of the previous call is re-included in the cached prefix that the model re-reads. Large structured payloads (rendered hypotheses, query result rows, hunt bodies) cause the input-token envelope to balloon — eventually crossing the model's effective context window and triggering autocompact-thrash on smaller models (Haiku-class).

The fix is mechanical: when a payload is large *or* has a natural durable home on disk, the producer writes the payload to a file and returns a small reference instead. The agent reads the file on demand using `Read` (a normal file-read tool call), which is cheap and does not pollute the cached prefix the way an inline body does.

This contract specifies the canonical shape of that reference so producers and consumers can interoperate without negotiation.

## Core fields

Every envelope-reduced response contains these four fields:

| Field | Type | Description |
|-------|------|-------------|
| `preview` | string | Short, human-readable summary of what was persisted. ~200 chars max. Lets the model state what happened without re-reading the file. |
| `path` | string | **Absolute** path to the persisted artifact on the filesystem the model can read from. Stable across the session. |
| `persisted` | bool | `true` when content was written to disk; `false` when the response was returned inline (under threshold + no parent artifact). |
| `byte_count` | int | Size, in bytes, of the persisted serialization. Lets the consumer reason about cost before reading. |

## Producer-specific extension

A `metadata` object holds producer-defined keys. The contract is opaque to its contents — consumers parse `metadata` only when they recognize the producer.

Examples:

- Research-hypothesis writer:
  `metadata: { research_id, mitre_techniques, data_sources }`
- Vault-side data-source query CLI:
  `metadata: { row_count, columns, query_hash }`

Producers are encouraged to keep `metadata` flat (one level deep) and JSON-serializable.

## Two persistence gates

Each producer chooses **one** gate:

### Gate A — parent artifact (preferred when one exists)

The producer accepts a parent-artifact identifier (e.g. `research_id` for hypothesis writes). When supplied, the payload is appended/written to that artifact and the response collapses to the envelope shape regardless of size. Without an identifier the producer falls back to inline.

Rationale: artifact-bound writes have a natural home on disk and a stable identity in the session, so the envelope is always an improvement.

### Gate B — byte threshold (preferred for ad-hoc payloads)

When no parent artifact applies, the producer measures the rendered serialization. If `byte_count > threshold`, it persists to its scratch directory and returns the envelope. Below threshold, it returns the payload inline as before.

**Default threshold:** 2048 bytes.

Rationale: small payloads are not the problem and round-tripping them through disk is needless work.

## Persistence directory

Each producer defines its own env var for the scratch directory, with a sensible default:

| Producer | Env var | Default |
|----------|---------|---------|
| Hypothesis writer (this repo) | `ATHF_HUNTS_DIR` | `<workspace>/research/` (existing — predates this contract) |
| Vault-side data-source query CLI (e.g. `hv query`) | `ATHF_QUERY_RESULTS_DIR` | `./query-results/` |

Producers do **not** share a single env var. The contract names the field (`path`), not the location of the bytes.

**Deployment requirement:** the persistence directory must be reachable at the same absolute path by both the producer (which writes) and the model's `Read` tool (which reads). On EC2 deployments this is automatic; on machines with sandboxed filesystems, operators must mount the directory consistently.

## Backwards compatibility

Producers may include additional fields beyond the four core ones — the contract is a **subset**, not a closed shape. ATHF's `athf_agent_run_hypothesis` MCP tool, for example, returns the canonical envelope plus `research_id`, `file_path` (path mirrored under its legacy name), `hypothesis_preview` (preview mirrored), `mitre_techniques`, `data_sources`, and `metadata`. New consumers should read `path` and `preview`; existing consumers reading `file_path` and `hypothesis_preview` continue to work.

## Examples

### Inline (under threshold, no parent)

```json
{
  "hypothesis": "Adversaries run native discovery commands post-access.",
  "mitre_techniques": ["T1016"],
  "data_sources": ["EDR process telemetry"],
  "persisted": false,
  "preview": "Adversaries run native discovery commands post-access.",
  "path": "",
  "byte_count": 0,
  "metadata": {}
}
```

### Persisted (parent artifact supplied)

```json
{
  "research_id": "R-0042",
  "file_path": "/workspace/research/R-0042.md",
  "hypothesis_preview": "Adversaries run native discovery commands post-access.",
  "mitre_techniques": ["T1016", "T1082"],
  "data_sources": ["EDR process telemetry"],
  "persisted": true,
  "preview": "Adversaries run native discovery commands post-access.",
  "path": "/workspace/research/R-0042.md",
  "byte_count": 4823,
  "metadata": {"latency_ms": 1240, "model": "claude-sonnet-4-6"}
}
```

### Persisted (byte threshold crossed)

```json
{
  "preview": "1000 rows from nocsf_unified_events (2025-11-21 18:00 → 19:00 UTC)",
  "path": "/workspace/query-results/a1b2c3d4.json",
  "persisted": true,
  "byte_count": 184293,
  "metadata": {
    "row_count": 1000,
    "columns": ["time", "actor.user.name", "process.name"],
    "query_hash": "a1b2c3d4e5f6..."
  }
}
```

## Reference implementation

`athf.core.envelope.build_envelope` in this repo is the canonical Python implementation. It accepts:

- `payload` — string (already-serialized) or any JSON-serializable structure
- `threshold` — bytes; default 2048
- `persist_dir` — directory to write to when persisting via Gate B
- `parent_artifact` — when supplied, switches to Gate A and forces persistence
- `metadata` — producer-specific extension

It returns a dict with the four core fields plus `metadata`, with `path` always absolute when `persisted=true`.

## Out of scope

- Cleanup / GC of the persistence directory. Producers may rotate or operators may sweep — the contract makes no statement.
- Encryption at rest. Files contain whatever the producer wrote; sensitive content must be handled by the producer's own policy.
- Cross-producer hash collisions. Each producer chooses its own naming scheme.
