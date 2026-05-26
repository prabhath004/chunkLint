# Rules And Config

ChunkLint rules are deterministic static checks. Chunk-scoped rules inspect one
chunk at a time. Cross-chunk rules inspect the full chunk list.

The boundary checks are production-oriented heuristics, not certified accuracy
claims. To honestly claim 90-95% precision or recall, the project needs a
labeled corpus of real chunks and a repeatable evaluation script. Until then,
the rules are designed to be transparent, configurable, and conservative about
common false positives.

## Config Loading

ChunkLint loads `chunklint.yml` or `chunklint.yaml` from the current working
directory when present. The CLI can also receive a config path:

```bash
chunklint scan chunks.json --config config/chunklint.yml
```

Python can pass the same path:

```python
from chunklint import lint

report = lint(chunks, config_path="config/chunklint.yml")
```

## Default Config

```yaml
version: 1

thresholds:
  min_words: 30
  max_words: 700
  duplicate_similarity: 0.92
  max_line_break_ratio: 0.35

required_metadata:
  - source

heading_keys:
  - heading
  - title
  - section
  - heading_path
  - document_title
  - file_name

rules:
  missing_text:
    enabled: true
    severity: high
  missing_id:
    enabled: true
    severity: medium
  missing_source:
    enabled: true
    severity: medium
  missing_heading:
    enabled: true
    severity: medium
  starts_mid_sentence:
    enabled: true
    severity: high
    connector_words:
      - also
      - although
      - and
      - because
      - but
      - except
      - however
      - or
      - that
      - then
      - therefore
      - which
    ignore_start_words:
      - api
      - asyncio
      - aws
      - azure
      - ebay
      - github
      - ios
      - ipad
      - iphone
      - javascript
      - langchain
      - llamaindex
      - macos
      - mongodb
      - node.js
      - npm
      - openai
      - postgres
      - pytest
      - python
      - qdrant
      - sqlite
      - typescript
      - weaviate
  ends_mid_sentence:
    enabled: true
    severity: medium
    allow_colon_endings: true
  broken_chunk_boundary:
    enabled: true
    severity: high
  too_short:
    enabled: true
    severity: low
  too_long:
    enabled: true
    severity: medium
  broken_markdown_table:
    enabled: true
    severity: high
  broken_code_block:
    enabled: true
    severity: medium
  near_duplicate:
    enabled: true
    severity: low
  pdf_noise:
    enabled: true
    severity: low
```

## Thresholds

| Name | Default | Used by |
| --- | --- | --- |
| `min_words` | `30` | `too_short` |
| `max_words` | `700` | `too_long` |
| `duplicate_similarity` | `0.92` | `near_duplicate` |
| `max_line_break_ratio` | `0.35` | `pdf_noise` |

## Rule Reference

### `missing_text`

Severity: high.

Flags chunks with empty or whitespace-only text. Empty chunks waste embedding
calls and cannot help retrieval.

### `missing_id`

Severity: medium.

Flags chunks without a stable ID. IDs are important for debugging, deduping, and
mapping bad retrieval results back to source chunks.

### `missing_source`

Severity: medium.

Flags chunks without a source reference. Source can come from the top-level
`source` field or metadata keys such as `source`, `file_name`, `path`, or
`document_id`.

### `missing_heading`

Severity: medium.

Flags chunks without heading or title context. Accepted metadata keys are
configured through `heading_keys`. PDF page labels are useful for traceability,
but they are not section context and are not included by default.

### `starts_mid_sentence`

Severity: high.

Flags chunks that begin with connector words such as `except`, `however`,
`therefore`, `because`, `although`, `which`, `that`, `and`, `but`, `or`, `also`,
or `then`. It also flags lowercase starts unless the chunk appears to be code,
a table, a heading, a quote, or a list item.

The rule now uses multiple signals:

- continuation punctuation at the start, such as `,`, `;`, `)`, or `-`
- configurable connector words
- stronger treatment for relative and coordinating starts such as `which`,
  `that`, `and`, `but`, or `or`
- lowercase starts with false-positive exclusions
- short heading/label detection
- markdown table, code fence, HTML tag, quote, and list-item exclusions
- configurable ignored start words for corpus-specific terms such as `iPhone`,
  `npm`, or `OpenAI`

Custom connector and ignored words:

```yaml
rules:
  starts_mid_sentence:
    enabled: true
    severity: high
    connector_words:
      - except
      - which
      - meanwhile
    ignore_start_words:
      - iphone
      - ebay
      - yourproduct
```

### `ends_mid_sentence`

Severity: medium.

Flags chunks that do not end with sentence-ending punctuation. It also catches
strong continuation endings, such as trailing commas, semicolons, dashes, or
connector words like `and`, `because`, `which`, and `while`.

It skips common cases where punctuation is not expected, such as markdown table
rows, list items, code fences, URLs, headings, short labels, HTML tags, and
colon-ended intro labels when `allow_colon_endings` is true.

### `broken_chunk_boundary`

Severity: high.

Compares adjacent chunks and flags likely sentence splits across chunk
boundaries. This catches higher-confidence cases from real RAG output, such as:

```text
chunk A ends:   The results demonstrated that, on the
chunk B starts: qualitative and quantitative analysis...
```

The issue is attached to the second chunk because that is the chunk that starts
with incomplete context.

### `too_short`

Severity: low by default.

Flags chunks below `thresholds.min_words`. If a short chunk also lacks heading
metadata, the issue is raised to medium because the chunk is both small and
context-poor.

### `too_long`

Severity: medium.

Flags chunks above `thresholds.max_words`. Large chunks can blend unrelated
topics and weaken retrieval precision.

### `broken_markdown_table`

Severity: high.

Flags chunks with multiple pipe-delimited table rows but no markdown separator
row such as `| --- | --- |`. Table chunks without headers lose column meaning.

### `broken_code_block`

Severity: medium.

Flags chunks with an odd number of triple-backtick fences. Broken fences can
distort code examples and surrounding prose.

### `near_duplicate`

Severity: low.

Uses RapidFuzz to compare chunks and flags later chunks whose similarity meets
or exceeds `thresholds.duplicate_similarity`.

### `pdf_noise`

Severity: low.

Flags common extraction artifacts:

- standalone page numbers
- `Page X` labels
- words split with line-break hyphenation
- unusually high line-break ratios
- repeated first/last lines that look like headers or footers

## Disabling A Rule

```yaml
rules:
  near_duplicate:
    enabled: false
```

## Changing Severity

```yaml
rules:
  too_short:
    enabled: true
    severity: medium
```
