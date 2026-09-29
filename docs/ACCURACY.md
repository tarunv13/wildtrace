# How accurate is WildTrace?

Accuracy is measured, not asserted. A reviewer draws a random sample of published cases
(`wildtrace accuracy sample`), reads each case's source headlines blind to how the pipeline scored it,
and records whether it is a genuine wildlife-trade enforcement event (a seizure, arrest, prosecution,
conviction, or a rescue linked to trade), whether its species are right, and why when it is not.
`wildtrace accuracy score` computes precision with a 95% Wilson interval and publishes it on the site
(`web/data/accuracy.json`, the "How accurate is WildTrace?" answer). Label files stay private because
they contain headlines; the counts and error classes are public.

## Current figure

**96.5% of published cases are genuine wildlife-trade enforcement events** (193 of 200; 95% interval
93.0% to 98.3%; audit 5, 29 September 2026). Species were right in 98.4% of the genuine cases. The previous
audit measured 95.5% (91.7% to 97.6%); the intervals overlap, so precision is holding steady rather than
proven higher.

The target is 98%. It is not reached yet, and WildTrace does not claim it. Precision by evidence grade in
the same audit: corroborated 97.6% (40/41), single report 95.1% (135/142), official 94.1% (16/17).

## History

| Audit | Pipeline | Sample | Genuine events | Main error classes found |
| --- | --- | --- | --- | --- |
| 1 | v1.10.0 | 200 | 163 (81.5%) | features and commentary, programmes and launches, statistics, topic words ("trafficking") taken as events, place and person names read as species |
| 2 | event-verb gate, genre and statistics rules, masks | 200, fresh | 189 (94.5%) | statistics in Portuguese and Spanish, reports, "arrêtés" (orders), a town named Araras (macaws) |
| 3 | second round of rules | 200, fresh | 192 (96.0%) | football ("Costa do Marfim"), bycatch rescues, tender notices, political statements, NGO complaints |
| 4 | third round of rules, leftmost-longest species matching | 200, fresh | 191 (95.5%) | a suburb named Rosewood, the Sandalwood film industry, legal decrees, opinion, research features |
| 5 | ambiguous-word rules tuned from 1,820 reviewed hits (below) | 200, fresh | 193 (96.5%) | meeting remarks, a research feature, administrative and fines policy, an awareness warning, a python-skin manuscript, one non-wildlife story |

Each fix is recorded with its evidence in [CURATION.md](CURATION.md). Every audit uses a new random seed,
so no figure is measured on cases the rules were tuned on.

## What the figure does not cover

- **Recall** (events WildTrace misses) is not measured by these audits. After the first round of rules,
  148 of the 163 genuine events in audit 1 were still published (90.8%); later verb additions recovered
  some of the rest.
- **Coverage** follows the sources searched: newsrooms, government sites and the languages WildTrace reads.
- **Place** accuracy is not yet audited systematically; known errors come from towns that share a name with
  a place elsewhere.

## Ambiguous-word review (29 September 2026)

Every hit of an ambiguous word in the screened reports (1,820 hits, 1,625 unique headlines) was read and labelled
`should_count` y/n: does the word mean the traded species or an enforcement act in that headline? Under the old
rules 86.5% of decisions were right: accepted words were 94.4% right, but half of held words (162) were real trade
stories the rule missed, because context words such as *trade*, *smugglers*, *sold*, *luggage* and *heist* were not
recognised. After the changes logged in CURATION.md, 92.1% of decisions are right on the same labels (accepted
95.6%, misses 162 -> 73). That is measured on the labels the changes came from, so audit 5 above is the
independent check. Labels are kept across rebuilds (private, `data/labels/ambiguous_review.csv`).

## Tried and not adopted: a learned relevance filter (29 September 2026)

A classifier trained on the 800 audit labels (65 non-events) was tested leave-one-audit-out: train on three
audits, score the fourth. Two feature sets, multilingual sentence embeddings (paraphrase-multilingual-MiniLM-L12-v2)
and character n-grams, gave the same result. Dropping the lowest-scoring 2% of cases removed 7 of 65 non-events
but also 9 of 735 real events (pooled precision 91.9% -> 92.6%); dropping 6% removed 16 non-events and 32 real
events. A filter that loses a real case for every false one it removes is not an improvement, so it is not used.
The remaining errors are too varied for 65 examples to teach.

## Why the last few percent are hard

The remaining errors are a long tail: each fresh sample surfaces classes the last one did not (a suburb, a
film industry, a decree). Rules close each class but not the tail. Reaching 98% needs many more labelled non-events (several hundred) before a learned model can help, or
human validation of single-report cases before they are published; both are funded work. Each quarter
brings a fresh blind audit ([FUNDING.md](FUNDING.md) lists what pays for them).
