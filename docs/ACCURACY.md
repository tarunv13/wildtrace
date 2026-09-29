# How accurate is WildTrace?

Accuracy is measured, not asserted. A reviewer draws a random sample of published cases
(`wildtrace accuracy sample`), reads each case's source headlines blind to how the pipeline scored it,
and records whether it is a genuine wildlife-trade enforcement event (a seizure, arrest, prosecution,
conviction, or a rescue linked to trade), whether its species are right, and why when it is not.
`wildtrace accuracy score` computes precision with a 95% Wilson interval and publishes it on the site
(`web/data/accuracy.json`, the "How accurate is WildTrace?" answer). Label files stay private because
they contain headlines; the counts and error classes are public.

## Current figure

**95.5% of published cases are genuine wildlife-trade enforcement events** (191 of 200; 95% interval
91.7% to 97.6%; audit of 29 September 2026 on the build of that day). Species were right in 99.0% of the
genuine cases.

The target is 98%. It is not reached yet, and WildTrace does not claim it. Precision by evidence grade in
the same audit: corroborated 97.6% (40/41), single report 95.1% (135/142), official 94.1% (16/17).

## History

| Audit | Pipeline | Sample | Genuine events | Main error classes found |
| --- | --- | --- | --- | --- |
| 1 | v1.10.0 | 200 | 163 (81.5%) | features and commentary, programmes and launches, statistics, topic words ("trafficking") taken as events, place and person names read as species |
| 2 | event-verb gate, genre and statistics rules, masks | 200, fresh | 189 (94.5%) | statistics in Portuguese and Spanish, reports, "arrêtés" (orders), a town named Araras (macaws) |
| 3 | second round of rules | 200, fresh | 192 (96.0%) | football ("Costa do Marfim"), bycatch rescues, tender notices, political statements, NGO complaints |
| 4 | third round of rules, leftmost-longest species matching | 200, fresh | 191 (95.5%) | a suburb named Rosewood, the Sandalwood film industry, legal decrees, opinion, research features |

Each fix is recorded with its evidence in [CURATION.md](CURATION.md). Every audit uses a new random seed,
so no figure is measured on cases the rules were tuned on.

## What the figure does not cover

- **Recall** (events WildTrace misses) is not measured by these audits. After the first round of rules,
  148 of the 163 genuine events in audit 1 were still published (90.8%); later verb additions recovered
  some of the rest.
- **Coverage** follows the sources searched: newsrooms, government sites and the languages WildTrace reads.
- **Place** accuracy is not yet audited systematically; known errors come from towns that share a name with
  a place elsewhere.

## Why the last few percent are hard

The remaining errors are a long tail: each fresh sample surfaces classes the last one did not (a suburb, a
film industry, a decree). Rules close each class but not the tail. The next step is a learned relevance
model trained on the audit labels, used alongside the rules and checked the same way, with a fresh blind
audit every quarter ([FUNDING.md](FUNDING.md) lists what pays for them).
