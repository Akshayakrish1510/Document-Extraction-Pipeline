# document extraction pipeline

Turn messy customer documents into validated, reviewable structured data.

`docpipe` reads documents (invoices in the sample data), extracts the key fields, validates them, scores
its own confidence, and routes anything doubtful to a human review queue. Results land in SQLite and
export to CSV. It ships with an eval harness so you can measure accuracy instead of guessing.

This is the kind of problem a forward deployed engineer gets handed on day one: a customer with a
manual, error-prone workflow and no appetite for a rewrite. The repo is a small, tested starting point for
that engagement.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

docpipe ingest data/sample_invoices      # extract, validate, store
docpipe review                           # what needs a human?
docpipe export results.csv               # hand results to the client
docpipe eval data/sample_invoices data/labels.json   # measure accuracy
pytest                                   # run the tests
```

Example output:

```
[ok    ] inv_001.txt  confidence=1.00
[ok    ] inv_002.txt  confidence=1.00
[ok    ] inv_003.txt  confidence=1.00
[review] inv_004.txt  confidence=0.25  (missing invoice_number; missing total; missing currency)
[ok    ] inv_005_resend.txt  confidence=1.00

5 documents ingested, 1 need review.
warning: possible duplicate ACME Industrial Supplies #INV-1001: inv_001.txt, inv_005_resend.txt
```

## How it works

```
documents (.txt)
      |
      v
  Extractor  --- RegexExtractor (default, deterministic)
      |      \-- LLMExtractor  (optional, for layouts regexes cannot handle)
      v
  Validator  --- missing fields, bad dates, non-positive totals -> issues + confidence
      |
      v
  SQLite store --- idempotent upserts, duplicate detection, review queue
      |
      v
  CSV export / review list / eval report
```

Design choices worth knowing:

- **A bad document never stops the batch.** Extraction errors are recorded as issues and the file goes to
  review. Configuration errors (like a missing model name) do stop the run, because they affect every file.
- **Re-running is safe.** Ingestion upserts by file name, so you can run it again after fixing the extractor.
- **Humans stay in the loop.** Low confidence is a feature: the pipeline says "look at this" instead of
  silently writing a wrong number into the client's books.
- **Accuracy is measured.** `docpipe eval` compares output with hand-labelled documents, and CI fails if
  accuracy drops.

## LLM extractor (optional)

```bash
pip install -e ".[llm]"
export ANTHROPIC_API_KEY=...        # your API key
export DOCPIPE_LLM_MODEL=...        # a model name from the provider's documentation
docpipe ingest data/sample_invoices --extractor llm
docpipe eval data/sample_invoices data/labels.json --extractor llm
```

The model name is configuration, not code, so you can swap models and re-run the eval to compare them.
Tests use a fake client and run fully offline.


## Project layout

```
src/docpipe/     models, extract, validate, store, pipeline, evaluate, cli
tests/           pytest suite (offline, no API key needed)
data/            sample invoices and labels for the eval harness
docs/            discovery, scope and handoff templates
.github/         CI: lint, tests on Python 3.10-3.13, accuracy gate
```

## Roadmap ideas

- PDF and image input (OCR) alongside plain text
- Line-item extraction and checks that line items add up to the total
- Per-vendor extraction rules and a feedback loop from corrected review items
- Web UI for the review queue
- Scheduled ingestion from an email inbox or shared folder

## License

MIT. See [LICENSE](LICENSE).
