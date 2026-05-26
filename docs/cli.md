# CLI

The `chunklint` CLI is built with Typer and is intended for local debugging and
CI checks before re-indexing a vector database.

## Install Locally

From this repository:

```bash
python -m pip install -e .
```

Verify the console command:

```bash
chunklint --help
```

Fallback if the console script is not on your PATH:

```bash
python -m chunklint.cli --help
```

## `scan`

Scan a chunk export:

```bash
chunklint scan chunks.json
chunklint scan chunks.jsonl
```

Use the demo fixture:

```bash
chunklint scan examples/bad_chunks.json
```

Fail on a severity threshold:

```bash
chunklint scan chunks.json --fail-on high
chunklint scan chunks.json --fail-on medium
chunklint scan chunks.json --fail-on low
```

Threshold behavior is inclusive. `--fail-on medium` fails on medium and high
issues. `--fail-on low` fails on any issue.

`--fail-on` is an inclusive gate. In text output, it prints structured gate
tables for the summary, ignored lower-severity details, blocking root causes,
and next steps. JSON output remains the full machine-readable scan.

Write machine-readable output:

```bash
chunklint scan chunks.json --format json
chunklint scan chunks.json --format json --out report.json
chunklint scan chunks.json --verbose
chunklint scan chunks.json --examples-per-rule 5
chunklint scan chunks.json --raw --max-issues 50
chunklint scan chunks.json --raw --max-issues 0
```

Suppress terminal output while preserving the exit code:

```bash
chunklint scan chunks.json --fail-on high --quiet
```

By default, text output groups related rules into root causes and keeps examples
hidden. Use `--verbose` to show examples with snippets, and
`--examples-per-rule` to control how many examples are shown. Use `--raw` for
row-level findings; `--max-issues` limits raw rows and `--max-issues 0` prints
every raw row.

Load a specific config:

```bash
chunklint scan chunks.json --config chunklint.yml
```

## `init`

Create `chunklint.yml` in the current directory:

```bash
chunklint init
```

Create a config at a custom path:

```bash
chunklint init config/chunklint.yml
```

Overwrite an existing config:

```bash
chunklint init --force
```

## `rules`

List supported rules:

```bash
chunklint rules
```

The output includes default severity and scope. Chunk-scoped rules inspect one
chunk at a time. Cross-chunk rules inspect the full list, which is needed for
duplicate and repeated PDF noise detection.

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Completed successfully and did not fail the selected threshold. |
| `1` | Lint threshold failed. |
| `2` | Input file or config was invalid. |
| `3` | Unexpected internal error. |

## Input Examples

JSON array:

```json
[
  {
    "id": "chunk_1",
    "text": "Refund Policy. Customers can request refunds within 30 days.",
    "source": "refund_policy.pdf",
    "metadata": {"page": 2, "heading": "Refund Policy"}
  }
]
```

JSONL:

```json
{"id":"chunk_1","text":"Refund Policy. Customers can request refunds within 30 days.","source":"refund_policy.pdf","metadata":{"page":2,"heading":"Refund Policy"}}
{"id":"chunk_2","text":"except enterprise customers may request refunds within 90 days.","source":"refund_policy.pdf","metadata":{"page":2,"heading":"Refund Policy"}}
```
