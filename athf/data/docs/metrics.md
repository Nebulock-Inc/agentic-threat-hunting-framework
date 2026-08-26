# Hunting Metrics

ATHF tracks the cost, effort, and outcome of every hunt by writing **events** to an append-only log and computing **aggregates** from them on demand. The system is vault-agnostic: ATHF core ships the schema, storage, recording API, and CLI; vault plugins extend it with platform-specific surfaces (cloud cost telemetry, data-source query metadata, org-level rollups).

This page is the canonical reference. If you're integrating a new tool or vault, this is the contract.

---

## Why Metrics?

You can't improve what you can't see. The metrics core answers:

- **What did this hunt cost me?** — LLM tokens, dollar cost, query time, web searches, similarity searches.
- **What did the program produce?** — per-verdict outcome counts, hunts completed, coverage by tactic / technique / data source.
- **Where is the time going?** — per-hunt and workspace-wide rollups.

ATHF auto-records the things it owns (LLM calls, web search, similarity search). Anything else — query latency from your data source, manual outcomes, custom events — is one function call away.

---

## Storage Model

Two files per workspace, both under `metrics/`:

| File                       | Role                                       | Source of truth?       |
| -------------------------- | ------------------------------------------ | ---------------------- |
| `metrics/events.jsonl`     | Append-only canonical event log            | **Yes**                |
| `metrics/aggregates.json`  | Derived per-hunt + workspace rollups       | No — regenerable       |

Each line of `events.jsonl` is one JSON object — a `MetricEvent`. Files are created lazily on first write. Concurrent appends are safe: ATHF takes an exclusive `fcntl.flock` per write on POSIX, with a process-local fallback on Windows.

`aggregates.json` is rebuilt from `events.jsonl` plus your hunt files (`hunts/H-*.md` frontmatter and body). It is regenerable — delete it and `athf metrics extract` will rebuild it.

### Tenancy

ATHF core metrics storage is **single-tenant per workspace**. One workspace = one organization's data. There is no `organization_id` scoping inside `events.jsonl`, and ATHF will not partition mixed-org events for you. If you deploy ATHF in a multi-tenant context (shared service backing several orgs), the extension layer is responsible for keeping each org's events in its own workspace path or for partitioning reads/writes by `organization_id` in a wrapper around the recording API. Don't share an `events.jsonl` across orgs.

---

## Event Schema

Every event has an `event_type` from this closed set:

| `event_type`         | When it fires                                       | Auto-recorded? |
| -------------------- | --------------------------------------------------- | -------------- |
| `llm_call`           | LLM API completion (tokens + cost + duration)       | Yes            |
| `query`              | Data-source query (Splunk, Elasticsearch, Athena, …) | Vault-side     |
| `web_search`         | Tavily / web search                                 | Yes            |
| `similarity_search`  | TF-IDF similarity (`athf similar`)                  | Yes            |
| `hunt_outcome`       | Hunt-level verdict (see the ladder below)           | Manual         |
| `manual`             | Anything else (custom plugins, scripts)             | Manual         |

Canonical fields (all optional except `event_type`):

```text
event_type        : str          # required, must be in EVENT_TYPES
timestamp         : str (RFC3339, ms precision)  # auto-set
event_id          : str          # 16-hex random, auto-set

hunt_id           : str | None
session_id        : str | None
agent             : str | None   # e.g. "hypothesis-generator"
model             : str | None   # e.g. "claude-sonnet-4"

input_tokens      : int  | None
output_tokens     : int  | None
cost_usd          : float| None
duration_ms       : int  | None

query_count       : int  | None
events_analyzed   : int  | None
rows_returned     : int  | None
status            : str  | None  # success | error | timeout | inconclusive

outcome           : str  | None  # verdict for hunt_outcome events (see below);
                                 # legacy tp | fp | inconclusive still accepted

custom            : dict         # anything that doesn't fit the above
```

Fields that are `None` are dropped from the JSONL line, keeping the file compact.

---

## Outcome Verdicts

`outcome` on a `hunt_outcome` event takes one of five verdicts. The old `tp` / `fp` / `inconclusive` values still parse, so nothing in an existing workspace breaks.

| Verdict | Counter in `totals` | Meaning |
| ------- | ------------------- | ------- |
| `confirmed` | `confirmed` | Malicious activity established — telemetry **plus** independent confirmation (reproduction, host forensics, or config review) |
| `suspected` | `suspected` | Telemetry evidence only. The ceiling when you can't independently confirm |
| `attempted_not_vulnerable` | `attempted_not_vulnerable` | Attack behavior observed; the named control held |
| `benign` | `benign` | Explained as legitimate activity |
| `inconclusive` | `inconclusive` | Insufficient telemetry to decide |

Telemetry alone never records `confirmed`. See [FORMAT_GUIDELINES.md](../hunts/FORMAT_GUIDELINES.md) for the evidence gate and the routing rule.

### Why `attempted_not_vulnerable` Gets Its Own Counter

Because it's the number that used to disappear. Under `TP` / `FP`, a hunt that watched an adversary attempt credential theft and get stopped by SELinux recorded an `fp` — indistinguishable from a hunt that found nothing at all. For a managed-service report those are opposite results, and the first one is frequently the most valuable thing in the deliverable. Now it counts as itself.

### Precision Is Deliberately Narrow

`suspected` and `attempted_not_vulnerable` are **not** folded into precision:

```text
precision = positives / (positives + negatives)
          = confirmed  / (confirmed  + benign)
```

Only verdicts that made an actual malicious/not-malicious call participate. Rationale:

- **`suspected` never passed the evidence gate.** Counting it as a positive imports unverified findings into a quality number, which is exactly the laundering the gate exists to stop.
- **`attempted_not_vulnerable` isn't a hunting error.** The behavior was really there — the hunt was right. Scoring it as a false positive would punish hunters for a control working, and the fastest way to make people stop reporting blocked attacks is to make reporting them look bad on a dashboard.
- **`inconclusive` is a telemetry problem, not a precision problem.** It belongs in coverage and data-quality reporting, not in the ratio.

Track the other three tiers as their own counters and read them alongside precision. A program with 40 `attempted_not_vulnerable` results is in good shape; a diluted precision figure would have hidden that.

---

## Public Recording API

The stable surface lives at `athf.metrics`. **Always import from there**, not from `athf.core.metrics` (the latter is the internal engine and may change).

```python
import athf.metrics as m

# LLM call (auto-instrumented from athf.agents.base.LLMAgent)
m.record_llm_call(
    model="claude-sonnet-4",
    input_tokens=120,
    output_tokens=80,
    duration_ms=420,
    agent="hypothesis-generator",
    # cost_usd computed from athf.core.cost_tracker.estimate_cost if omitted
)

# Data-source query (call from your vault's query runner)
m.record_query(sql="SELECT ...", duration_ms=15, rows=42)

# Web search (auto-instrumented from athf.core.web_search.TavilySearchClient)
m.record_web_search(query="lsass dumping", duration_ms=900, result_count=5)

# Similarity search (auto-instrumented from athf similar)
m.record_similarity_search(query="kerberoast", duration_ms=12)

# Hunt outcomes — call this when you close a hunt
m.record_hunt_outcome(hunt_id="H-0019", outcome="confirmed")

# The control held — this is a result, not an absence of one
m.record_hunt_outcome(hunt_id="H-0020", outcome="attempted_not_vulnerable")

# Generic escape hatch
m.record("manual", hunt_id="H-0019", duration_ms=300, custom={"step": "triage"})
```

### Behavior contract

- **Best-effort.** Every helper wraps its append in a `try/except`; serialization or filesystem failures are silently dropped. Metrics never break callers.
- **Active-session lookup.** If `hunt_id` / `session_id` are omitted, the helpers ask whatever context provider was registered via `athf.metrics.register_context_provider` for the active session and fill them in. Plugins register their own session manager at import time; ATHF core ships no provider, so without a registration the helpers leave both fields `None`.
- **Cost is automatic.** `record_llm_call` defers to `athf.core.cost_tracker.estimate_cost` when `cost_usd` is not passed.
- **Search text is hashed, not stored.** `record_query`, `record_web_search`, and `record_similarity_search` write a SHA-256 prefix of the input text (`custom.sql_hash` / `custom.query_hash`) so patterns can be grouped without leaking hunt content, IOCs, or user prose into the metrics log.
- **Outcomes are canonicalized.** `record_hunt_outcome` lowercases whatever it's given. The five ladder verdicts (`confirmed`, `suspected`, `attempted_not_vulnerable`, `benign`, `inconclusive`) and the legacy values (`TP`, `tp`, `FP`, `fp`, `inconclusive`) are all accepted. Legacy `tp` is counted as legacy — it is **not** silently rewritten to `confirmed`, because those events predate the evidence gate.

---

## CLI

```bash
athf metrics show     --hunt H-0019            # per-hunt detail
athf metrics summary                            # workspace totals + rollups
athf metrics extract                            # rebuild aggregates.json
athf metrics record   --type manual --hunt H-0019 --field note=ran-the-thing
```

All four take `--workspace PATH` (default: cwd). `show` and `summary` take `--format table|json`. `record` takes repeated `--field key=value` pairs; values are coerced to int / float / bool / string in that order.

`show` and `summary` auto-extract on first read, so the commands always work.

See `CLI_REFERENCE.md` for the full per-flag reference.

---

## Auto-Instrumented Surfaces

| Surface                                | Hook                                                     | Notes                          |
| -------------------------------------- | -------------------------------------------------------- | ------------------------------ |
| `athf.agents.base.LLMAgent._call_llm`  | Calls `record_llm_call` after every provider response    | Used by every LLM-backed agent |
| `athf.core.web_search.TavilySearchClient.search` | Calls `record_web_search` after a successful response | Tavily only — extend per client |
| `athf.commands.similar`                | Wraps `_find_similar_hunts` and calls `record_similarity_search` | Records latency + result count |

Vault plugins are responsible for `record_query` (every vault has its own data-source client) and `record_hunt_outcome` (driven by hunt closeout).

---

## Aggregates: What `extract` Produces

`metrics/aggregates.json` has this shape:

```jsonc
{
  "schema_version": "1.0.0",
  "generated_at": "2026-06-24T08:00:00.000Z",
  "workspace": "/abs/path/to/workspace",
  "totals": {
    "hunts": 12,
    "llm_calls": 87,
    "input_tokens": 122_340,
    "output_tokens": 38_410,
    "cost_usd": 1.42,
    "queries": 64,
    "query_duration_ms": 18_220,
    "events_analyzed": 1_840_000,
    "web_searches": 11,
    "similarity_searches": 6,

    // verdict ladder counters
    "confirmed": 3,
    "suspected": 5,
    "attempted_not_vulnerable": 4,
    "benign": 9,
    "inconclusive": 2,

    // legacy counters — still populated from older hunts, never derived
    // from the ladder counters above
    "true_positives": 3,
    "false_positives": 4
  },
  "rollups": {
    "by_platform":    { "macOS": 4, "linux": 6 },
    "by_tactic":      { "credential-access": 5, "persistence": 3 },
    "by_technique":   { "T1003.001": 2, "T1078.004": 1 },
    "by_data_source": { "edr": 7, "iam": 3 }
  },
  "hunts": {
    "H-0019": { /* per-hunt bucket */ }
  }
}
```

The extractor blends two sources:

1. **`events.jsonl`** — sums per-hunt `llm_calls`, `queries`, etc.
2. **Hunt files** — pulls frontmatter (`findings`, `ruled_out`, `true_positives`, `events_analyzed`, etc.) and falls back to body regexes (`**Total Queries Executed:** N`) for older hunts. Frontmatter wins when both are present.

Verdict counters come from the `findings` and `ruled_out` frontmatter lists: each entry's `verdict` increments its counter. Hunts that only carry `true_positives` / `false_positives` contribute to the legacy counters only — the two sets sit side by side rather than one being inferred from the other.

`extract` is idempotent and uses an atomic `mkstemp` + `os.replace` write, so it's safe to run while other processes are reading the file.

---

## Extending: Plugin Surfaces

The vault-agnostic core is intentionally narrow. Vault plugins extend the `metrics` Click group at import time:

```python
# in your vault's commands package
from athf.commands.metrics import metrics

@metrics.command()
def usage() -> None:
    """Show CloudWatch / per-AWS-account LLM usage."""
    ...
```

Once the plugin is loaded, `athf metrics usage` works alongside the core subcommands. This is how vault extensions add platform-specific reporting (cloud usage, org-level rollups, …) without forking.

---

## Migration Notes

If you have an older workspace with a legacy `metrics/execution_metrics.json`:

- `aggregates.json` replaces it. The numbers should match within rounding.
- New code should call `athf.metrics.record_*` directly. Vault plugins that previously shipped a `MetricsTracker` class can keep one as a thin in-plugin shim, but ATHF core no longer provides one.
- `events.jsonl` is the new source of truth — if you want to backfill from a legacy execution log, `Aggregator.extract_from_hunt_file()` reads the same hunt-file regexes the old tracker used.

If you're moving a workspace onto the verdict ladder:

- Nothing needs to change. `true_positives` / `false_positives` keep working and keep aggregating.
- Start writing `findings` / `ruled_out` on new hunts. Old hunts can stay as they are indefinitely.
- Do **not** script a bulk `true_positives → confirmed` migration. Those findings never passed the evidence gate, so promoting them would put unverified results in the top tier. Re-read the hunts you care about and assign verdicts by hand; most legacy TPs are honestly `suspected`.
- Legacy `false_positives` mixes `benign` with `attempted_not_vulnerable`. Splitting it requires reading the hunt — that's the whole reason the ladder exists.

---

## See Also

- `athf metrics --help` — quick CLI reference
- `athf/data/docs/CLI_REFERENCE.md` — full per-flag CLI documentation
- `athf.core.metrics` — schema, storage, aggregator (internal)
- `athf.metrics` — public recording API (stable surface)
