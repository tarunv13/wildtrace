<div align="center">

<img src="docs/img/logo.svg" width="104" alt="WildTrace logo">

# WildTrace

**The open atlas of illegal wildlife trade.**

One map of seizures, arrests and convictions worldwide, in fauna and flora, with every case
graded by the strength of its evidence, and a link-analysis workbench that runs in your browser.
It traces wildlife crime from where nature is taken to where it touches national security:
crime revenue, disease risk and the loss of ecosystems people depend on.

[![CI](https://github.com/tarunv13/wildtrace/actions/workflows/ci.yml/badge.svg)](https://github.com/tarunv13/wildtrace/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/tarunv13/wildtrace)](https://github.com/tarunv13/wildtrace/releases)
[![License: MIT](https://img.shields.io/badge/code-MIT-blue)](LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-green)](#data-licence-and-citation)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22902819.svg)](https://doi.org/10.5281/zenodo.22902819)

[Open the Atlas](https://tarunv13.github.io/wildtrace/) ·
[Risk pathways](https://tarunv13.github.io/wildtrace/pathways.html) ·
[Research agenda](docs/RESEARCH_AGENDA.md) ·
[Who it's for](#who-its-for) ·
[How much to trust a case](#how-much-to-trust-a-case) ·
[Download the data](https://tarunv13.github.io/wildtrace/data/cases.csv) ·
[Run it yourself](#run-it-yourself) ·
[How to cite](#how-to-cite) ·
[Contributing](CONTRIBUTING.md)

</div>

<p align="center">
  <img src="docs/img/atlas.png" alt="The WildTrace globe with clustered case markers across Africa, South Asia and South America, a summary panel on the left and a timeline along the bottom" width="100%">
  <br>
  <sub>The Atlas (screenshot from an earlier build; now 2,290 cases in 75 countries). Colour is the kind of event, paler dots are single reports, the glow is density of reporting.</sub>
</p>

---

## Wildlife crime is a security risk. How strong is the evidence?

The Oxford Agile Initiative's *Environment and National Security: Exploring the Risk Pathways*
(September 2026) maps how environmental damage reaches national security, and notes that its
pathway diagrams "could be linked to a database showing relevant evidence for each link". Wildlife
crime appears in its agenda mainly as a revenue source for hostile actors and organised crime
(R1.37). WildTrace supplies the evidence for that pathway, link by link:

| Link | Open evidence in WildTrace |
| --- | --- |
| Nature is taken | strong: cases, 24,786 CITES seizures, 19,346 US port seizures |
| It moves through routes and hubs | partial: CITES transit, multi-country cases |
| It reaches the border | strong: CITES and US inspection records (US-heavy) |
| It funds crime and corrupts institutions | **a gap**: many seizures, few convictions, no open financial data |
| It carries disease risk | partial: VIRION viruses in traded groups, WHO outbreak reports |
| It erodes ecosystems | partial: removals by functional group |
| It is fought with evidence or rumour | strong: every case graded |

Read [Risk pathways](https://tarunv13.github.io/wildtrace/pathways.html) for the numbers, rebuilt
daily, and the [open research agenda](docs/RESEARCH_AGENDA.md) for the questions that would close the
gaps, from open event-extraction benchmarks to court-outcome data. WildTrace takes the security frame
on one condition: **security without militarisation**. Claims carry their evidence, enforcement is
counted and never glorified, and no accused person is named (see [how WildTrace speaks](docs/VOICE.md)).

## What WildTrace sees that others do not

**Offered online, rarely caught.** [ECO-SOLVE](https://www.ecosolve.eco/dashboard) (Global Initiative
Against Transnational Organized Crime) records wildlife adverts online: 30,934 adverts for 440 species
through 11 regional hubs, 14 April 2024 to 24 September 2026, three in five on Facebook, and no plants.
WildTrace records where trade met enforcement. Set side by side for the same species, country and period,
they show where wildlife is sold openly while almost nothing reaches the public record of seizures:

| Country | Group | Adverts (ECO-SOLVE) | Cases (WildTrace) |
| --- | --- | --- | --- |
| Thailand | Bears | 1,303 | 0 |
| Thailand | Parrots & songbirds | 1,046 | 0 |
| Indonesia | Parrots & songbirds | 859 | 0 |
| Colombia | Parrots & songbirds | 1,180 | 1 |
| Thailand | Tiger | 2,232 | 3 |
| Thailand | Elephant (ivory) | 2,917 | 4 |

It is not a detection rate (the sources watch different things with different effort), and part of the
gap was WildTrace's own: 10,313 of the adverts are in Thai, so WildTrace now reads Thai news too. Only
aggregated counts are published ([`online_gap.csv`](https://tarunv13.github.io/wildtrace/data/online_gap.csv)),
with attribution; the advert rows are not redistributed. Species offered online but in no WildTrace group
yet (pirarucu, otters, small wild cats, serows) are listed for the next groups. Side-by-side coverage:
[docs/OBSERVATORIES.md](docs/OBSERVATORIES.md).

**Caught online.** Every case records the platforms its reports name (Facebook, Instagram, WhatsApp,
Telegram, TikTok, OLX, Mercado Livre, Shopee ...), never a seller, and daily searches look for online
wildlife crime that reached police, customs or courts in nine languages.

**Captive-bred claims.** Declaring wild-caught animals as captive-bred is a documented laundering route
(Lyons & Natusch 2011). [`captive_claims.csv`](https://tarunv13.github.io/wildtrace/data/captive_claims.csv)
shows, per exporter and animal group, how the captive-bred share of commercial CITES exports moved between
2015-2018 and 2020-2023. A rise is a question to ask, never a finding: genuine breeding produces it too.

**No word thrown away.** Words that name a traded species and also mean something else ("monitor", "horn",
"python", Thai "เหี้ย") are kept and counted only with supporting context nearby; every hit is logged for
review, and a picture can settle it: local OCR ([LiteParse](https://github.com/run-llama/liteparse)) reads
the text in an image and [BioCLIP](https://huggingface.co/imageomics/bioclip) recognises the species
(`wildtrace vision`). Every vocabulary decision is recorded with its evidence in the
[curation log](docs/CURATION.md), after *Scrub Data* (Kay, Bar & Beery 2026). Tools evaluated and adopted:
[docs/TOOLING.md](docs/TOOLING.md).

**Reptiles and amphibians.** A new group covers axolotls, dart frogs, salamanders and frog legs, following
Vora et al. (2026, *Nature*): more than half of traded reptiles and two in five traded amphibians are taken
from the wild, and legal and illegal animals are hard to tell apart.

## Why WildTrace

- **Every case says how well it is evidenced.** Validated, official, corroborated or single
  report, shown on the map, in the case panel and in the CSV. A case built on one local news
  story never looks like a case confirmed by a customs release.
- **It is honest about its gaps.** The map says how many cases it could not place, and states
  plainly that counts show where wildlife crime is *reported*, not where it happens.
- **Fauna and flora.** Ivory, pangolin and rhino horn, but also rosewood, agarwood and red
  sanders, in 31 species groups and nine languages.
- **Anyone can challenge a case.** Every case panel has a Report a correction link. Reviewers
  record the outcome in a file in this repository, and rejected cases disappear at the next build.
- **The data is yours.** One CSV, CC BY 4.0, with the JSON behind the map beside it. No account,
  no API key, no account. Usage is measured with Microsoft Clarity, which is stated on the site.
- **Nobody accused is named.** No names, phone numbers, addresses or seller identities are ever
  published. The build fails if one gets through, and CI checks again.

|  | WildTrace | Commercial and closed IWT dashboards |
| --- | --- | --- |
| Cost | Free | Licence, subscription or membership |
| Source code | Open (MIT) | Closed |
| Case-level data | CSV and JSON, CC BY 4.0 | Aggregates or on request |
| Evidence grading per case | Yes, four levels | Rare; usually one confidence figure or none |
| Link analysis | In the browser, free | i2 Analyst's Notebook and similar, paid |
| Your own data | Stays in your browser | Uploaded to a server |
| Scope | Global, fauna and flora | Often one region or one taxon |

WildTrace is young, and it does not replace the field's reference datasets. It points to them
instead: the [observatory network](docs/OBSERVATORIES.md) lists 33 datasets, dashboards and
codebooks, with what each holds and its access terms. The CITES Trade Database, ETIS, LEMIS,
UNODC World WISE and TRAFFIC's portal hold records WildTrace will never match.

## Who it's for

| You are | What WildTrace gives you |
| --- | --- |
| Investigative journalism | A searchable base of public seizures with every source link, and a link chart to find what connects them |
| Enforcement and customs analysis | Reported routes, transport modes, commodities and the agencies named, exportable as CSV, GraphML or JSON |
| NGOs and conservation programmes | A global picture with country and species filters, free to embed, fork or re-host |
| Researchers and students | A citable dataset with a DOI, an open method, and a classifier trained on a published labelled set |
| Policy and CITES work | Where trade in a listed species is being reported, and how strong that reporting is |
| Anyone with their own spreadsheet | Import CSV, Excel or JSON into the workbench and chart it against the public data, all in your browser |

## The Atlas

**New here? [Watch the 2-minute guide](https://tarunv13.github.io/wildtrace/#guide)** ([MP4](web/media/guide.mp4)).
It is a real recording of the Atlas answering three research questions.

Everything happens on one globe. The other surfaces float over it, so you can wander without
losing your place.

| Surface | What it does |
| --- | --- |
| **Globe** | Cases by kind, a density glow, reported routes as arcs, observatories. Globe or flat, slow rotation, legend toggle |
| **Flows** | Where wildlife is taken, where it passes through and where it is seized, from 24,786 seized shipments reported to CITES and imports seized at US ports (LEMIS). You build the view: follow a species or a country, choose source and market countries, how many routes, which evidence (CITES seized, seized at US ports, declared legal trade, news routes), and colour lines by region, role or species. Every route can be switched off; a story sentence rewrites itself from what is on; the whole view lives in the link |
| **Who supplies whom** | A heatmap of source countries (or regions) against the countries that seized them, for plants, animals or both, with or without the United States; click a cell to draw it |
| **Zoonoses** | A separate lens: 2,116 WHO outbreak reports of animal-borne disease, grouped by how they reach people, with WildTrace cases as rings over them, and a table of the viruses confirmed in each traded species group (VIRION). A shared map, not a cause |
| **Analysis** | What the evidence shows on one sheet: cases per month, events, species, source or market, transport, CITES seizures per year |
| **Search** (`/`) | Cases, species, countries and observatories in one box |
| **Pulse** | A live summary of what is in view; every bar is a filter |
| **Inspector** | A written account of the case, then the documented facts, analytical context and limits of the evidence, with every source listed. Back, forward and a shareable link |
| **Timeline** | Cases per week. Drag to pick a period; ▶ glides through them in time order |
| **Why this matters** | A collapsible trivia box: the scale of the trade, each figure from a named report you can open, plus facts counted from WildTrace's own cases |
| **Tour** | A one-minute walkthrough that spotlights each part of the live interface. Runs once for a new reader, replayable from the Tour button |
| **Table** | Every case, sortable and filterable, with CSV download |
| **Investigate** | A link chart of cases, species, places and agencies, plus your own imported data |
| **Network** | The 33 observatories, databases and codebooks, each checked, with how WildTrace uses them |
| **Methods** and **About** | Pipeline, classifier, evidence definitions, coverage, licence and citation |

<p align="center">
  <img src="docs/img/case.png" alt="A case panel for a seizure in Bengaluru: an Official source badge, CITES-listed species chips, and sections for documented facts, analytical context and limits of the evidence" width="100%">
  <br>
  <sub>A case record keeps documented facts, analytical context and the limits of the evidence apart. Arrests are counts only; no person is named.</sub>
</p>

<p align="center">
  <img src="docs/img/investigate.png" alt="The Investigate link chart showing the best-connected 175 entities: cases as red squares joined to species, places and agencies" width="100%">
  <br>
  <sub>Investigate opens on the best-connected part of the network. Isolate, expand, find the shortest path between two entities, then export to PNG, GraphML, CSV or JSON.</sub>
</p>

<p align="center">
  <img src="docs/img/flows.png" alt="The Flows view: plant products seized on the way from North America and South Asia to East Asia, lines shading from the source region's colour to the market's, with a list of routes, each with flags and an Evidence button" width="100%">
  <br>
  <sub>Flows: you choose the species, countries, evidence and colours; every route can be switched off and has its evidence one click away. The whole view lives in the link.</sub>
</p>

<p align="center">
  <img src="docs/img/route.png" alt="The evidence page for the route Austria to United States: three seized shipments of ivory carvings, trophies and leather products, 2019 to 2021, all reported by the United States as personal items" width="100%">
  <br>
  <sub>Every route shows the records behind it: what was seized, when, who reported it and why it moved, the matching news cases, and how to check it in the CITES database.</sub>
</p>

<p align="center">
  <img src="docs/img/zoonoses.png" alt="The Zoonoses view: WHO outbreak reports as bubbles coloured by how the disease reaches people, WildTrace cases as rings, and a list of countries with both" width="100%">
  <br>
  <sub>Zoonoses: animal-borne outbreaks beside the trade, stated on every surface as a shared map, not a cause.</sub>
</p>

<p align="center">
  <img src="docs/img/table.png" alt="The All cases table: date, case, evidence badge, country and number of reports, with a Download CSV button" width="100%">
  <br>
  <sub>Every case as a table, sortable by any column, with the evidence grade beside it and "not mapped" stated rather than hidden.</sub>
</p>

## How much to trust a case

Every case carries one status:

| Status | Meaning |
| --- | --- |
| **Validated** | A person checked it against its sources, recorded in [`validations.yaml`](pipeline/wildtrace/resources/validations.yaml) with reviewer, date and note |
| **Official** | At least one report is a government, customs, police, prosecutor or court release |
| **Corroborated** | Two or more independent outlets report it |
| **Single report** | One outlet only: a lead, not a finding |

As of 29 September 2026: **255 official, 317 corroborated, 1,718 single report**. Three in four
cases still rest on one outlet, and **1,056 of 2,290 cases name no place** at all. Those numbers are
on the site, not buried here, because a map that hides them would be misleading.

Found a mistake? Use **Report a correction** on any case, which opens a pre-filled issue.

## Data, licence and citation

- **Download:** [`cases.csv`](https://tarunv13.github.io/wildtrace/data/cases.csv), one row per
  case, with status, place, species and source links. The JSON behind the map sits beside it in
  [`web/data/`](web/data).
- **More downloads:** [`cites_seized_flows.csv`](https://tarunv13.github.io/wildtrace/data/cites_seized_flows.csv)
  (origin, exporter, importer, seized shipments per species group),
  [`cites_declared_flows.csv`](https://tarunv13.github.io/wildtrace/data/cites_declared_flows.csv),
  [`lemis_seized_flows.csv`](https://tarunv13.github.io/wildtrace/data/lemis_seized_flows.csv)
  (imports seized at US ports per species group and origin, CC BY 4.0),
  [`online_gap.csv`](https://tarunv13.github.io/wildtrace/data/online_gap.csv)
  (ECO-SOLVE adverts against WildTrace cases per group and country; aggregated, with attribution),
  [`captive_claims.csv`](https://tarunv13.github.io/wildtrace/data/captive_claims.csv)
  (commercial CITES exports declared captive-bred, per exporter and group, 2015-18 vs 2020-23; CITES terms),
  [`zoonotic_outbreak_reports.csv`](https://tarunv13.github.io/wildtrace/data/zoonotic_outbreak_reports.csv)
  (2,116 WHO reports with disease, pathway and countries) and
  [`species_viruses.csv`](https://tarunv13.github.io/wildtrace/data/species_viruses.csv).
- **Licence:** case data CC BY 4.0, code MIT. `flows.json` is derived from the CITES Trade Database
  and shared under its terms (non-commercial, with attribution); the virus counts in
  `zoonoses.json` come from VIRION under ODbL 1.0.
- **Coverage:** 2,290 cases, 75 countries, 3,319 public reports, 2024-01-15 to 2026-09-28; 24,786
  seized and 7 million declared CITES shipments since 2015; 2,116 zoonotic WHO outbreak reports.

## How it fits together

Collection feeds the case pipeline; only privacy-checked data reaches `web/data`, and the Atlas
and the Investigate workbench read nothing else. CITES and WHO data enter as published aggregates.

```mermaid
flowchart TD

subgraph group_g_collect["Collection"]
  node_cli["Pipeline CLI<br/>[cli.py]"]
  node_collectors["Report collectors"]
  node_literature["Literature miner<br/>[literature.py]"]
end

subgraph group_g_pipeline["Case pipeline"]
  node_classifier["Relevance classifier<br/>[train.py]"]
  node_event_extract["Event extraction<br/>[events.py]"]
  node_place_extract["Place resolution<br/>[cases.py]"]
  node_case_schema["Case model<br/>[schema.py]"]
  node_privacy["Privacy checks<br/>[privacy.py]"]
end

subgraph group_g_publish["Public data"]
  node_publisher["Data publisher<br/>[publish.py]"]
  node_graph_builder["Link graph builder<br/>[build.py]"]
  node_web_data[("Published atlas data")]
end

subgraph group_g_atlas["Atlas interface"]
  node_app["Atlas application<br/>[main.js]"]
  node_state["Atlas state<br/>[store.js]"]
  node_globe["Globe map<br/>[globe.js]"]
  node_inspector["Case inspector<br/>[inspector.js]"]
  node_search["Unified search<br/>[search.js]"]
  node_surfaces["Atlas surfaces"]
end

subgraph group_g_analysis["Analysis workbench"]
  node_investigate["Investigate workbench<br/>[investigate.js]"]
  node_local_data[("Imported local data")]
end

node_user(("Atlas user"))
node_public_sources(("Public reports"))
node_cites[("CITES trade data")]
node_who[("WHO reports")]
node_browser(("Browser reader"))

node_public_sources -->|"provide reports"| node_collectors
node_cli -->|"collect records"| node_collectors
node_cli -->|"mine literature"| node_literature
node_collectors -->|"supply records"| node_event_extract
node_literature -->|"supply records"| node_event_extract
node_cli -->|"score listings"| node_classifier
node_cli -->|"extract events"| node_event_extract
node_event_extract -->|"resolve locations"| node_place_extract
node_place_extract -->|"form cases"| node_case_schema
node_case_schema -->|"check public fields"| node_privacy
node_privacy -->|"authorize publication"| node_publisher
node_cites -.->|"published route data"| node_web_data
node_who -.->|"published outbreak data"| node_web_data
node_publisher -->|"write atlas data"| node_web_data
node_case_schema -->|"build entity links"| node_graph_builder
node_graph_builder -->|"export graph"| node_web_data
node_browser -->|"open atlas"| node_app
node_app -->|"load data"| node_web_data
node_app -->|"navigate and filter"| node_state
node_app -->|"render map"| node_globe
node_app -->|"show selected case"| node_inspector
node_app -->|"mount search"| node_search
node_app -->|"show analysis views"| node_surfaces
node_user -->|"open workbench"| node_investigate
node_app -->|"open investigation"| node_investigate
node_investigate -->|"read public graph"| node_web_data
node_user -->|"select spreadsheet"| node_local_data
node_investigate -->|"read in browser"| node_local_data

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_cli,node_collectors,node_literature,node_user,node_browser toneBlue
class node_classifier,node_event_extract,node_place_extract,node_case_schema,node_privacy,node_cites,node_who toneAmber
class node_publisher,node_graph_builder,node_web_data toneMint
class node_app,node_state,node_globe,node_inspector,node_search,node_surfaces toneRose
class node_investigate,node_local_data,node_public_sources toneIndigo
```

<sub>Architecture map generated by <a href="https://gitdiagram.com/tarunv13/wildtrace">GitDiagram</a>
on 23 September 2026. The <a href="https://gitdiagram.com/tarunv13/wildtrace">interactive version</a>
links each box to its source file.</sub>

## How it stays current

A GitHub Actions workflow refreshes the site **every day** (03:17 UTC): new news reports, WHO
outbreak reports and VIRION, then a rebuild and redeploy if anything changed. Government and court
domains and GDELT are swept on Mondays. The collected records are kept in a private archive
repository, because news feed terms allow publishing derived facts only; a build that would
publish over 10% fewer cases than are live stops instead of shrinking the site. CITES flows follow
the CITES release cycle and are refreshed once a year.

## Run it yourself

```bash
pip install -e ".[dev,video]"
wildtrace collect --official --gnews --countries ALL   # official releases + global news
wildtrace collect --history 12 --no-gdelt              # one-off: backfill 12 months
wildtrace build                                        # cases, graph, CSV, site data (privacy gate)
wildtrace cites path/to/Trade_database_download_v2026.1 # yearly: CITES supply -> demand flows
wildtrace lemis data/raw/lemis --taxonomy path/to/codebook # US port seizures (LEMIS, CC BY)
wildtrace captive path/to/Trade_database_download_v2026.1 # yearly: captive-bred claims in CITES trade
wildtrace ecosolve data/raw/ecosolve/adverts-data.csv  # ECO-SOLVE adverts vs WildTrace cases
wildtrace vision path/to/images                        # OCR + BioCLIP species evidence (pip install -e ".[vision]")
wildtrace zoonoses                                     # weekly: VIRION + WHO outbreak reports
python scripts/make_og.py                              # redraw the share card with the new counts
python -m http.server -d web 8000                      # open http://localhost:8000
```

Optional: `export WILDTRACE_WCS_OWT_DIR=/path/to/OWT` trains the listing classifier on the OWT
labelled set. Other commands: `gazetteer` rebuilds the place index, `codebook <zip>` merges the
PMC8579131 names, `cites <folder>` loads the CITES Trade Database, `lemis <folder>` loads the
US LEMIS seizure records (Marshall et al. 2025, Zenodo 14982583; Eskew et al. 2020, Zenodo 3565869),
`relabel` merges classifier
corrections, `doctor` checks tools and sources.

## How a report becomes a case

```
collect ─► screen ─► extract ─► merge ─► link ─► publish
official,   species ×   species, place,   one case per      entity–link     privacy gate,
news,       enforcement route, quantity,  incident, across  graph with      static JSON
listings    cues, minus arrests (count),  languages and     centrality      and CSV
            false cues  agency, mode      story days
```

- **Screening** rejects look-alikes: an ivory-smuggling *film*, "Kasturi" liquor, the Ivory Park
  township.
- **Places** come from the report. Hindi words such as कुशीनगर are transliterated and matched by
  consonant skeleton, and homonyms are settled by the country the text names. Google News links
  are not decoded, because its robots.txt forbids it.
- **Merging** keeps one incident as one case even when Hindi and English reports share no words.
- **Sources** are tiered by domain, so an official release is recognised as one.

[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) has the data contracts and design choices.

## Findable without JavaScript

The Atlas is an application; search engines and AI answer engines need text. Every build also
writes a plain HTML layer from the same data — a page per
[species group](https://tarunv13.github.io/wildtrace/species/pangolin.html), per
[country](https://tarunv13.github.io/wildtrace/country/in.html) and per case, all indexed from
[browse.html](https://tarunv13.github.io/wildtrace/browse.html) — plus `sitemap.xml`, a `robots.txt`
that welcomes AI crawlers, and [`llms.txt`](https://tarunv13.github.io/wildtrace/llms.txt), a plain-text
brief so an answer engine quoting the figures also carries the caveats. Each page states its numbers
in text, names its licence, links its sources, and repeats the line that matters: these counts show
where wildlife crime is *reported*, not where it happens.

## Mining the research literature

News under-reports plants. `wildtrace mine` searches Europe PMC and OpenAlex for trade research and
extracts three things: species names (checked against the GBIF backbone, so a plant is recognisably a
plant), candidate trade names and code words (only from sentences where a paper says a name is used in
trade), and datasets other researchers have published. Nothing is merged automatically: the results
land in `data/interim/*.csv` for a person to accept or reject.

```bash
wildtrace mine --topics flora          # or: codewords, fauna, datasets, all
```

## Coverage

- **39 species groups**, animals and plants: pangolin, ivory, rhino horn, tiger, leopard, jaguar,
  lion bone, African grey parrots, totoaba, glass eels, abalone, plus orchids, cacti and succulents,
  cycads, carnivorous plants, medicinal and aromatic plants, sandalwood, plant resins, wild bulbs,
  rosewood, agarwood and red sanders, in
  English, Hindi, Telugu, Portuguese, Spanish, French, Vietnamese, Thai and Indonesian/Malay,
  plus 2,376 names in 66 languages from the open seized-wildlife codebook (Stringham et al. 2021).
- **46,000 places**: every town above 15,000 people worldwide, every town above 1,000 in South
  and Southeast Asia, every Indian district, key trafficking airports, and native-script names.
- **Sources**: 25 government, enforcement and judicial domains worldwide, 23 Google News editions
  with a month-by-month backfill, GDELT, and YouTube listings collected locally.

## The classifier

Trained on the OWT labelled set (1,274 labelled online listings), evaluated on a test set split by
seller channel. At the target of keeping 98% of trade listings it rejects about half of the
irrelevant ones. Contradictory labels, not the model, set the ceiling.
[`data/labels/README.md`](data/labels/README.md) has the codebook and the relabel loop.

## Privacy

WildTrace never publishes a person's name, a phone number, an e-mail address or a seller
identity; the build fails if one slips through, and CI checks again. Imported data stays in your
browser's local storage and is never uploaded. There are no accounts, and fonts are self-hosted.

The site does measure how it is used, with **Microsoft Clarity**: clicks, scrolling and session
replays, which set cookies and send data to Microsoft. The search box and the whole panel that
renders imported files are marked `data-clarity-mask`, so a typed query and anyone's own
spreadsheet never reach a replay; advertising storage is denied; and Clarity is skipped entirely
for browsers sending a Global Privacy Control signal. Remove `data-clarity` from
`web/index.html` in a fork and nothing loads.
See [`docs/ETHICS_PRIVACY.md`](docs/ETHICS_PRIVACY.md) and Microsoft's
[privacy statement](https://privacy.microsoft.com/privacystatement).

## Roadmap

Ideas, not promises. Discuss them in [Issues](https://github.com/tarunv13/wildtrace/issues).

- [ ] Court judgments and prosecution outcomes (SHERLOC, Indian Kanoon)
- [ ] More history: backfill beyond 12 months, and official archives before 2024
- [ ] More validated cases, and a published reviewer log
- [ ] Better placement of country-only cases
- [ ] Seizure quantities normalised to comparable units
- [ ] A shareable saved view (filters and period in one link)

## Known limitations

- Three in four cases rest on a single report, and 1,056 of 2,290 name no place.
- Platform names come from headlines only for Google News records: Google's robots.txt forbids fetching
  its article links, and WildTrace respects that.
- Image evidence (`wildtrace vision`) runs locally on images you supply; the daily build does not yet
  collect images.
- Coverage is thinner before late 2025, and reporting is uneven between countries and languages,
  so the map reflects newsrooms and government sites as much as the trade.
- Only two cases so far state a route, because reports rarely name origin and destination.
- Google News links are not decoded, so some sources show the aggregator rather than the outlet.

## How to cite

If WildTrace helps your work, please cite it. Use the **Cite this repository** button
(it reads [`CITATION.cff`](CITATION.cff)) or copy one of these.

**APA 7**

> Verma, T. K. (2026). *WildTrace: the open atlas of illegal wildlife trade* (Version 1.10.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22902819

**BibTeX**

```bibtex
@software{verma_wildtrace_2026,
  author  = {Verma, Tarun Kumar},
  title   = {WildTrace: the open atlas of illegal wildlife trade},
  year    = {2026},
  version = {1.10.0},
  doi     = {10.5281/zenodo.22902819},
  url     = {https://github.com/tarunv13/wildtrace},
  license = {MIT}
}
```

The concept DOI [10.5281/zenodo.22902819](https://doi.org/10.5281/zenodo.22902819) always resolves to the
latest version. To cite the exact data you used, cite its version DOI:

| Version | Date | What it added | DOI |
| --- | --- | --- | --- |
| 1.10.0 | 2026-09-29 | ECO-SOLVE comparison, ambiguous words, image evidence, Thai, amphibians | being minted by Zenodo (listed on the [concept record](https://doi.org/10.5281/zenodo.22902819) when ready) |
| 1.9.0 | 2026-09-29 | caught online, captive-bred claims, 2,126 cases | [10.5281/zenodo.23025869](https://doi.org/10.5281/zenodo.23025869) |
| 1.8.0 | 2026-09-29 | Risk pathways, research agenda | [10.5281/zenodo.23024232](https://doi.org/10.5281/zenodo.23024232) |
| 1.7.0 | 2026-09-28 | US port seizures (LEMIS) | [10.5281/zenodo.23023112](https://doi.org/10.5281/zenodo.23023112) |
| 1.6.2 | 2026-09-23 | video guide | [10.5281/zenodo.22923626](https://doi.org/10.5281/zenodo.22923626) |
| 1.6.1 | 2026-09-23 | satellite view | [10.5281/zenodo.22922540](https://doi.org/10.5281/zenodo.22922540) |
| 1.6.0 | 2026-09-23 | route evidence, icons | [10.5281/zenodo.22921009](https://doi.org/10.5281/zenodo.22921009) |
| 1.5.0 | 2026-09-23 | Flows, Zoonoses, Analysis | [10.5281/zenodo.22913379](https://doi.org/10.5281/zenodo.22913379) |

Please also cite the data WildTrace builds on when you use those layers: the CITES Trade Database
(UNEP-WCMC), Marshall et al. 2025 and Eskew et al. 2020 (LEMIS), Carlson et al. 2022 (VIRION), Stringham
et al. 2021 (seized-wildlife codebook) and ECO-SOLVE (Global Initiative Against Transnational Organized Crime).

## Repository

```
pipeline/wildtrace/  collectors, classifier, extraction, graph, publishing (CLI: wildtrace)
web/                 the portal: index.html, css/, js/, data/
docs/                ARCHITECTURE, ETHICS_PRIVACY, OBSERVATORIES, screenshots
.github/workflows/   tests + privacy gate; weekly refresh; Pages deploy
```

## Credits

Code MIT; data CC BY 4.0. Places: GeoNames (CC BY 4.0). Names codebook: Stringham et al. 2021
(CC BY 4.0). News index: GDELT. Basemap: OpenFreeMap / OpenStreetMap contributors. Motion
vocabulary adapted from OpenHiggsfield. Inspired by WCS Brasil's Global Wildlife Trafficking
Observatory, C4ADS, TRAFFIC, #WildEye and i2 Analyst's Notebook.
