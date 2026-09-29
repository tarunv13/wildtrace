# Changelog

All notable changes to WildTrace. Dates are the release date, newest first.

## 1.11.0 — 2026-09-29

### Added
- **Ask it a question.** The Atlas opens with "What do you want to know?": eleven live answers, filtered for
  journalists, researchers, policy and everyone. Each answer gives the answer and its number, a chart, who answers
  (the sources and their standing), what the number cannot tell you, and where to explore it; each has a citable
  page (`answers.html`, `answers/<slug>.html`, QAPage and FAQ structured data).
- **Measured accuracy.** `wildtrace accuracy sample|score`: blind audits of random samples of published cases.
  Four audits on fresh samples took precision from 81.5% to **95.5%** (191/200, 95% interval 91.7-97.6%); species
  right in 99.0% of genuine cases. The 98% target is not reached and the site says so (`docs/ACCURACY.md`, the
  "How accurate is WildTrace?" answer).
- **Brand.** A new mark in which the trail runs from source (green) through transit (blue) to market (amber); motto
  "Follow the trade."; favicons, app icons, web manifest, lockup and a GitHub social preview (`docs/BRAND.md`).
- **Funding** (`docs/FUNDING.md`, Sponsor button): what support buys and the routes being pursued.

### Changed
- **A case needs an event.** Topic words ("trafficking", "tráfico", "तस्करी") no longer make a case on their own; an
  event verb does. Features, commentary, programmes, reports, tenders, political statements and period statistics
  are held back; rescue-only stories need a trade link or a count of 10+. Masks blank phrases that only look like
  wildlife (Tiger Strike Force, Costa do Marfim, arrêtés préfectoraux, human trafficking, a town named Araras).
  Cases: 2,290 -> **1,871**, each more likely to be real. Every rule and its evidence: `docs/CURATION.md`.
- **Species matching** is leftmost-longest ("red sandalwood smuggling" is red sanders only); generic codebook names
  never map to a narrower group; "चंदन" (also a first name), "denuncia", "बाघ", "बंदर" and Thai "กบ" are
  context-checked, not deleted.
- **Daily run** rotates the English-language news editions over three days (each still covered every three days),
  with a 180-minute limit and unbuffered logs, after collection outgrew the old limit.

## 1.10.0 — 2026-09-29

### Added
- **Offered online, rarely caught** (`wildtrace ecosolve`, `online_gap.csv`, Analysis): ECO-SOLVE's public
  advert data (30,934 adverts, 440 species, 11 hubs, April 2024 to September 2026) mapped to WildTrace groups
  and set against WildTrace cases for the same group, country and period. Bears in Thailand: 1,303 adverts,
  0 cases. Aggregates only, with attribution; the advert rows stay private.
- **Ambiguous words are kept, not deleted.** Words that name a traded species or an enforcement act and also
  mean something else ("monitor", "horn", "python", "coral", "ivory", "crackdown", Thai "เหี้ย" and "กบ") count
  only with supporting context nearby, take precedence over strong lists, and every hit is logged for review
  (`data/labels/ambiguous_review.csv`, private). Codebook common words are kept the same way.
- **Image evidence** (`wildtrace vision`): local OCR with LiteParse and zero-shot species recognition with
  BioCLIP. A picture can confirm an ambiguous word or flag a conflict for review; nothing is published.
- **Thai.** Species and enforcement words, a Thai-language news edition and online query, and Thai place names
  matched without word spaces (Thailand cases 25 -> 48). A third of ECO-SOLVE's adverts are in Thai.
- **Amphibians** (axolotls, dart frogs, salamanders, frog legs) in cases, CITES, LEMIS and captive-bred claims,
  after Vora et al. (2026, *Nature*).
- **Curation log** (`docs/CURATION.md`): every vocabulary decision with its evidence and effect, after
  *Scrub Data* (Kay, Bar & Beery 2026). **Tooling** (`docs/TOOLING.md`): tools used and evaluated, including
  the awesome-ai-apps collection.
- Cases: 2,126 -> **2,290** in 75 countries; no report from the previous build lost.

### Changed
- Plural species terms also match the singular ("parakeets" finds "parakeet"), except where the singular is
  an ambiguous word.
- Context checks use word-sequence lookups instead of one large regex (27 times faster; same decisions).

## 1.9.0 — 2026-09-29

### Added
- **Caught online: the enforcement end of online wildlife trade.** Every case now records the platforms its
  reports name (Facebook, WhatsApp, Telegram, TikTok, OLX, Mercado Livre, Shopee and others; never a seller,
  handle or link), in the case panel, `cases.csv` (`platforms` column) and `stats.json` (`by_platform`,
  `online`). Analysis gains "Caught online" and "What was sold online". Risk pathways link 2 reports it.
- **Online-crime searches in eight languages** (`collect --online`, now in the daily run): wildlife words
  with platform and social-media words in English, Portuguese, Spanish, French, Hindi, Vietnamese and
  Indonesian/Malay. A one-year backfill added 582 reports. Platform names come from headlines only: Google News
  forbids fetching its article links (robots.txt), and WildTrace respects that.
- **WildTrace and ECO-SOLVE** (docs/OBSERVATORIES.md): a side-by-side of coverage. ECO-SOLVE records adverts
  (offer); WildTrace records interception and outcome. Read together they show where wildlife is offered
  online but rarely reaches enforcement.

- **Wider screening vocabulary**, each word taken from a real missed report: generic wildlife phrases
  ("endangered wildlife", "wildlife specimens", "wildlife racket"), enforcement verbs ("busts", "foils", "raid",
  "charged", "pleaded guilty") and their Hindi, Vietnamese, Indonesian, Portuguese, Spanish and French
  equivalents (दबोचा, बरामद, khởi tố, thu giữ, diringkus, diamankan, autuado, aseguran, démantelé).
- **Cases: 1,373 -> 2,126** in 74 countries (from 3,126 reports), after the backfill and vocabulary fixes.
  A sample of new cases was read by hand; "crackdown" was dropped as a cue because it pulled in policy announcements.

- **Captive-bred claims** (`wildtrace captive`, `captive_claims.csv`, Analysis): for animal groups, the share
  of commercial CITES exports declared captive-bred per exporter, 2015-2018 against 2020-2023. Declaring
  wild-caught animals as bred is a documented laundering route (Lyons & Natusch 2011); a rise is a question to
  ask, never a finding, since genuine breeding, ranching and coral mariculture produce it too. Neither
  ECO-SOLVE nor WildTrace looked at the legal trade this way before.

### Fixed
- **Line separators in records.** Headlines containing U+2028/U+2029 were split mid-record when read back,
  which crashed the build; records are now written with those characters escaped and read by newline only.
- **Google News time windows.** `--gnews-window 12m` was read by Google News as twelve *minutes* and returned
  almost nothing; months are now converted (12m -> 1y, 3m -> 90d). Targeted backfills made with a months
  window before this release collected little; a one-year backfill of every species group was re-run.

## 1.8.0 — 2026-09-29

### Added
- **Risk pathways** (`pathways.html`): wildlife crime as an environment-to-security risk, in seven links from
  extraction to crime revenue, disease risk and ecosystem loss. Each link carries a number from the live data,
  a rating of the open evidence (strong, partial, a gap), the limit of that number, and the research question it
  answers in the Oxford Agile Initiative's *Environment and National Security: Exploring the Risk Pathways*
  (2026; R1.37, R5.2-R5.3). It states where the evidence runs out (who profits) and commits to security without
  militarisation. Rebuilt with every build; Article and FAQ structured data; a tappable list on phones.
- **Open research agenda** (`docs/RESEARCH_AGENDA.md`): questions that would close the gaps, each tied to data
  WildTrace already holds, from an open event-extraction benchmark and stance detection for listings to court
  outcomes, reporting-effort correction and ports.
- **How WildTrace speaks** (`docs/VOICE.md`): seven writing rules for readers, researchers and answer engines.
- Links to Risk pathways from About, Methods, Analysis and Browse; a security section in `llms.txt`; the US port
  seizure CSV in About.

## 1.7.0 — 2026-09-28

### Added
- **Seized at US ports.** A new evidence layer in Flows draws imports the US Fish and Wildlife
  Service seized (LEMIS disposition S), from the country of origin to the US, with its own route
  page: products, taxa, years, declared purpose and source, and transit countries. Species pages
  gain a "Seized at US ports" block with the top origins and products. Data: Marshall et al. 2025
  (Current Biology; 2000-2022, land vertebrates and arachnids) and Eskew et al. 2020 (Scientific
  Data; 2000-2014, fish, invertebrates and plants), both CC BY 4.0. Genera are placed in families with the GBIF key
  of the seized-wildlife codebook (Stringham et al. 2021). New command `wildtrace lemis`; new
  download `lemis_seized_flows.csv`.

### Changed
- **Wider taxon matching for trade records.** CITES and LEMIS rows now also match on the ranks a
  group's label implies (turtles = Testudines, monitor lizards = *Varanus*, bears = Ursidae,
  elephants = Elephantidae, rhinos = Rhinocerotidae, parrots = Psittaciformes, crocodilian skins,
  primates, eels, black corals), not only the Indian species each group lists. CITES seized
  shipments in Flows rise from 15,512 to 24,719 (turtles 17 to 1,611, bears 129 to 741). News
  matching is unchanged. Most of the gain is US-reported (US-bound routes are about 83% of CITES
  seizure records), which the default "Spread across markets" view and Methods make explicit.
- **Methods** gains "Seized at US ports": sources, the disposition filter, and three limits (paperwork
  seizures, US inspection effort, and overlap with US-reported CITES seizures: compare, never add).

### Changed
- **The video guide comes first.** A first-time visitor sees the 2-minute video before anything else
  (muted autoplay, captions on screen). It ends with a choice: take the guided tour or explore on
  their own. Phones get it too, although the guided tour needs a wider screen.
- **Easy to find again.** A "New here? Watch the 2-minute guide" card with a thumbnail sits at the
  top of Pulse. The top-bar "Tour" button is now **▶ Guide**, and its menu opens with the video.
- The site citation is now "Verma, T. K. (2026) … (Version …) … Zenodo DOI", built from
  `CITATION.cff`. The Zenodo metadata now gives each data file its correct licence.

## 1.6.2 — 2026-09-23

### Added
- **A 2-minute video guide** (Tour menu, the welcome card, About, or `#guide` in the address).
  It is a real recording of the live Atlas, not generated footage, and it answers three research
  questions: where the pangolin evidence in India comes from, where seized red sanders goes, and
  where animal-borne outbreaks and trafficking overlap. It also shows Investigate, Analysis and the
  tours. Captions are burned into the picture and also provided as a text track. To regenerate it,
  run `scripts/make_guide.py`, which writes `web/media/guide.mp4`, `.jpg` and `.vtt`.

## 1.6.1 — 2026-09-23

### Added
- **Satellite view.** A map button switches to EOxCloudless 2024 imagery (Copernicus Sentinel-2,
  CC BY-NC-SA 4.0, credited on the map), so forests, deserts, mountains and coasts can be read.
  Place names turn white on a dark halo over imagery. The choice is remembered; nothing loads from
  EOX unless it is switched on.

### Changed
- **Flows spreads routes across markets by default**: the busiest routes, but at most two into any
  one country. The default view went from 12 of 14 routes ending in the United States (an artefact of
  how completely it reports seizures) to routes into ten markets across Asia, the Gulf, Europe and
  North America. Switch it off for the raw ranking; it is kept in the link.
- The rotate button and the idle spin are gone: the spin stopped at the first touch and did nothing
  outside Cases, so the button looked broken.
- Deeper water on the map, so land and sea separate at a glance.
- The two routes named in news reports are no longer drawn on the opening map, where "Routes 2"
  suggested wildlife moves along two routes. The legend now links to Flows (15,000+ seized
  shipments reported to CITES); the news routes remain an evidence layer there.

## 1.6.0 — 2026-09-23

### Added
- **Evidence behind every route.** Each Flows route has an Evidence button, and clicking a line on
  the map opens the same page: what was seized (species and products such as ivory carvings, skins,
  timber or live animals), the years, which country reported it, the declared purpose, any transit
  countries, a plain answer to "where is the article?" (CITES records are government reports, not
  news, and are anonymised shipment by shipment) with a link to check the CITES Trade Database, and
  the WildTrace news cases involving the same species in those countries, with their outlets.
- **Icons and logos throughout.** Species silhouettes from PhyloPic (public domain, CC0 or CC BY,
  credited on each species page) for 37 of 38 groups; product and case-kind icons from Tabler Icons
  (MIT); case kinds as glyphs inside the map points; outlet logos beside every source (570 outlets)
  and organisation logos on the Network cards. Logos are fetched once at build time and served from
  the site, so a reader's browser never contacts a third party for them.
- `web/data/flows_detail.json`: per-route taxa, products, years, reporters, purposes and transit.
- **Country flags** wherever a country is named: country pages, case chips, Pulse, search, Flows
  routes and pickers, the route evidence page, the heatmap, the Zoonoses and Analysis lists
  (flag-icons, MIT, self-hosted).
- **Tours for every section.** The main tour now covers the three modes and every menu, with a
  full Investigate step and buttons that jump straight into the Flows or Investigate tours. Flows,
  Zoonoses, Investigate, its import tab, Analysis, the heatmap, Network, Table and Methods each have
  a short tour that runs the first time they open. Every card has a "Don't show section tips"
  switch, and the Tour button opens a menu: full tour, tour this section, tips on or off, reset.
- Pulse links straight into Investigate.

### Changed
- The timeline is drawn at the dock's real size (it was stretched), with years marking January and
  month labels thinned on narrow screens; it redraws when the dock resizes.
- The map-layer switches (cases, routes, observatories, your data) moved from the top bar into the
  legend beside the map, so the top bar fits every desktop width and Investigate is never cut off.

## 1.5.1 — 2026-09-23

### Changed
- **Daily refresh.** The update workflow now runs every day at 03:17 UTC: Google News for the last
  three days, WHO outbreak reports and VIRION every day; government and court domains and GDELT on
  Mondays. The collected records live in a private archive repository that the workflow restores
  and extends, so every build sees the full history. The site is redeployed only when the data
  changed.
- **Shrink guard.** A build that would publish more than 10% fewer cases than are live stops instead.

## 1.5.0 — 2026-09-23

### Added
- **Cases · Flows · Zoonoses.** The Atlas now answers three questions on the same map, switched
  from the top bar. Each mode brings its own left panel, and Flows and Zoonoses switch to the flat
  map so both ends of a route are in view.
- **Flows: supply, transit and demand.** 15,512 seized shipments reported to CITES since 2015
  (source code I, CITES Trade Database 2026.1), drawn from where a specimen was taken to where it
  was seized. The reader builds the view: follow a species or a country, pick source and market
  countries, the number of routes and the evidence (seized, declared legal trade, routes named in
  cases), and colour lines by region (eight UN M49 regions, colour-blind-safe palette), role
  (source, transit hub, market) or species. Lines shade from the source region's colour to the
  market's, arrowheads and moving dashes show direction, and a glow under each market grows with
  what arrives. Every route is a checkbox; a story sentence is written from what is on; the whole
  view is kept in the link.
- **Who supplies whom**: a source × market heatmap by country or region, plants, animals or both,
  with or without the United States. Clicking a cell draws that route.
- **Zoonoses**: 2,116 WHO Disease Outbreak News reports of diseases with an animal reservoir,
  grouped by how they reach people (wildlife contact, birds, livestock, insects and ticks), with
  WildTrace cases overlaid; a "countries with both" list; and a table of the viruses confirmed by
  sequencing or isolation in each traded species group (VIRION), same species as in people and
  close relatives, by virus family. Literature notes found with Consensus (Gippet et al. 2026,
  Shivaprakash et al. 2021, Lee et al. 2020, Gibb et al. 2024).
- **Analysis sheet**: cases per month, events, species, source or market, transport and CITES
  seizures per year, each with what it can and cannot show.
- Species records show a Sankey of seized shipments (taken from, shipped from, seized in) and the
  species' viruses; country records show a source / transit / market bar and outbreak counts.
- Species pages for groups the news rarely covers (orchids, cacti, cycads and others) now exist,
  built from their CITES seizure records.
- `wildtrace cites` now covers every country (it was limited to South and Southeast Asia) and
  `wildtrace zoonoses` refreshes VIRION and WHO data weekly in CI.

## 1.4.0 — 2026-09-23

### Added
- **A crawlable layer.** A static page for every case, species group and country, an index at
  `/browse.html`, `sitemap.xml`, a `robots.txt` that names the AI crawlers explicitly, and
  `llms.txt`. Schema.org Dataset, WebSite and FAQPage structured data on the Atlas; Dataset and
  Report structured data on the static pages. Every page carries the reporting caveat with its
  numbers, so a quoted figure arrives with its limits.
- **Literature miner** (`wildtrace mine`): Europe PMC and OpenAlex searches for trade research,
  with species names resolved against the GBIF backbone, candidate trade names and code words
  taken only from sentences that say a name is used in trade, and dataset links. Output is CSV
  for review; nothing merges itself into the lexicon.
- **Eight flora groups**: orchids, cacti and succulents, cycads, carnivorous plants, medicinal and
  aromatic plants, sandalwood, resins and gums, wild bulbs and ornamentals. 39 groups in all.

### Changed
- Phones: the lens bar scrolls with a fade instead of clipping Tour and Investigate, and the
  trivia box appears folded above the summary panel instead of being hidden.

## 1.3.0 — 2026-09-23

### Added
- **Guided walkthrough.** Nine steps that spotlight the live interface, run once for a new
  reader and replayable from the Tour button. Keyboard-driven and escapable at any step.
- **"Why this matters" trivia box.** Collapsible, one card at a time, with a diagram drawn to
  the figure it illustrates. Report figures carry their source, year and a link; cards counted
  from WildTrace's own data are generated at build time and labelled as such, with their bias
  stated. A test checks the derived numbers against the published cases.
- **A written account on every case.** What was reported, where, how much, who acted and how
  well it is evidenced, in prose, above the documented facts, analytical context and limits.
  The documented facts are now a scannable strip, and repeated quantity readings are shown once.
- **Microsoft Clarity** usage analytics, with text masking, Global Privacy Control honoured, and
  the project id in one HTML attribute so a fork can remove it. Documented in About,
  ETHICS_PRIVACY and SECURITY.

### Changed
- The link chart opens on the best-connected core rather than the whole network.
- The walkthrough and trivia box follow the OpenHiggsfield motion vocabulary already in the CSS:
  cards arrive on `--ease`, the overlay leaves faster than it enters on `--ease-exit`, and the
  spotlight travels on `--ease-slide`.

### Fixed
- The tour spotlight never highlighted anything, because `offsetParent` is null for every
  fixed-position panel.

## 1.2.1 — 2026-09-22

First release archived on Zenodo ([10.5281/zenodo.22902819](https://doi.org/10.5281/zenodo.22902819)).

### Added
- **Evidence grading.** Each case is validated, official, corroborated or single report, shown on
  the map, in the case panel, in the table and in the CSV. Reviewers record checks in
  `validations.yaml`; rejected cases are dropped at the next build.
- **Official sources.** A collector for 25 government, enforcement and judicial domains, searched
  in their own language, plus source tiering by domain.
- **History backfill.** Month-by-month collection (`--history N`), so the timeline shows real
  history instead of a single recent spike.
- **Open data.** `cases.csv` per-case export, CC BY 4.0, with a citation line and DOI.
- **Table** and **About** panels; focus moves into a case when it opens.
- **Report a correction** on every case, opening a pre-filled issue.
- Social preview image, redrawn from the live site by `scripts/make_og.py` on every weekly
  refresh so its counts stay current; self-hosted fonts; `CITATION.cff` and `.zenodo.json`.

### Changed
- The map shows a density glow, pales single-report cases, rings approximate places, scales
  clusters with zoom, and hides the Routes toggle until a report states a route.
- Investigate opens on the best-connected part of the network instead of the whole graph, and
  loads its libraries only when opened.
- Renamed throughout to the **OWT labelled set**.

### Data
1,251 cases, 59 countries, 1,752 public reports, 2024-01-15 to 2026-09-22.
187 official, 140 corroborated, 924 single report. 559 mapped, 135 country-only, 557 unmapped.

## 1.1.0 — 2026-09-22

Rebranded to WildTrace: one global map, no page tabs, light glass design, 33-entry observatory
network, in-browser link-analysis workbench.
