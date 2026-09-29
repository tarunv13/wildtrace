# Tooling WildTrace uses, and tools evaluated

WildTrace's constraints decide what fits: it runs free, daily, on GitHub Actions, with no API keys
and no paid inference; private data (labelled listings, OCR text, headlines) never leaves the
machine; every number must be reproducible from code and raw records.

## In use

| Tool | Licence | Used for |
| --- | --- | --- |
| [LiteParse](https://github.com/run-llama/liteparse) (LlamaIndex) | Apache-2.0 | Local OCR of text inside images (listings, seizure photos, scanned releases), no cloud, no key |
| [BioCLIP](https://huggingface.co/imageomics/bioclip) via [OpenCLIP](https://github.com/mlfoundations/open_clip) | MIT | Zero-shot visual species recognition that confirms or questions ambiguous text matches |
| scikit-learn TF-IDF + logistic regression | BSD-3 | Online-listing relevance classifier |
| MapLibre, Cytoscape, PhyloPic, Tabler, flag-icons | open licences | The Atlas |

## Evaluated: awesome-ai-apps (September 2026)

[Arindam200/awesome-ai-apps](https://github.com/Arindam200/awesome-ai-apps) (MIT, about 16k stars)
collects about 130 example apps. Most call a paid hosted model (Nebius Token Factory); WildTrace
takes their **patterns**, not their dependencies.

| Project | What it shows | Use in WildTrace |
| --- | --- | --- |
| LiteParse Invoice Auditor | local OCR with bounding boxes, evidence pinned to the scan | **adopted**: LiteParse powers `wildtrace vision` OCR |
| Trustworthy RAG | per-claim verdicts (supported, partial, unsupported, contradicted) against cited evidence | pattern for claim checking (research agenda A4) and case summaries |
| Agentic Typed RAG (LlamaIndex) | typed answers with exact-quote checks and a refusal gate for weak evidence | pattern: never state what the sources do not contain; matches WildTrace's evidence grades |
| Human-in-the-Loop Agent | actions paused for human approval | already WildTrace's rule for code words and ambiguous terms (review queues) |
| Maintainer Intelligence Brief | weekly brief where every claim links to the exact spot in its source | pattern for a weekly WildTrace brief with receipts |
| Web Intelligence Agent | Ask, Collect, Reason, Verify workflow with an audit trail | pattern for investigator-facing research runs |
| Temporal Agents | durable, retryable workflows | only if the daily pipeline outgrows GitHub Actions |
| Cost-Aware Model Router, Prompt Format Benchmark | model routing and prompt evaluation | relevant only if a hosted model is ever added |
| Gemma 3 / NVIDIA Nemotron OCR | OCR through a hosted vision model | not adopted: needs a paid key; LiteParse is local |

Not relevant here: finance, travel, calendar, sales and voice-agent examples.

## Principles taken from them

1. Evidence is pinned: every automated claim points to the phrase, pixel box or record behind it.
2. Weak evidence produces a refusal or a review item, not a guess.
3. Humans approve anything that changes what WildTrace publishes about a new term or claim.
4. Local first: OCR and vision run on the machine; nothing private is uploaded.
