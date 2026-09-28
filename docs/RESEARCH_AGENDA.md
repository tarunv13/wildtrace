# WildTrace open research agenda

WildTrace is an open, evidence-graded record of illegal wildlife trade: cases from public reports,
seizures reported to CITES, and imports seized at US ports. This agenda sets out what that record can
already answer, where it stops, and the research questions that would move it forward. Each question
names the data WildTrace already holds, so a student, a lab or a newsroom can start this week.

It is written against one frame: **wildlife crime as an environment-to-security risk**. The Oxford
Agile Initiative's *Environment and National Security: Exploring the Risk Pathways* (September 2026)
maps how environmental damage reaches national security and lists almost 200 research questions.
Wildlife crime appears in only a few of them: environmental crime as revenue for hostile actors and
organised crime (R1.37), and whether "animal life" and "revenue-generating uses" belong in the
weaponisation of nature (R5.2, R5.3). The report also notes that its pathway diagrams "could be linked
to a database showing relevant evidence for each link". WildTrace's
[Risk pathways](https://tarunv13.github.io/wildtrace/pathways.html) page does that for the
wildlife-crime pathway, and this agenda covers the links it cannot yet evidence.

## Principles

1. **Evidence before frame.** A security frame brings attention and money. It has also justified
   militarised conservation that harmed the people who live alongside wildlife (Duffy 2015;
   Lunstrum 2014; Massé et al. 2020). Every claim here carries its evidence and its limits.
2. **Reported is not happened.** Every count in WildTrace measures reporting and inspection effort as
   well as trade. The United States accounts for about four in five CITES seizure records in the data.
3. **No person is named.** Arrests are counts. Research that needs identities belongs with the
   authorities, not in open data.
4. **Plants count.** Plants make up about 15% of CITES seizures but about 10% of news cases
   (Margulies et al. 2019 call this "plant blindness").

## The seven links and where the evidence stops

| Link | Open evidence | What is missing |
| --- | --- | --- |
| 1. Extraction | strong: cases, CITES and US seizures | how much is taken, not just seized |
| 2. Routes and transit | partial: CITES transit, multi-country cases | routes named in reporting (2 news cases) |
| 3. Borders and inspection | strong: CITES source I, LEMIS disposition S | inspection effort outside the US |
| 4. Crime revenue and corruption | **a gap** | who profits, how much, and how cases end in court |
| 5. Disease risk | partial: VIRION viruses, WHO outbreaks | sampling effort; co-location is not cause |
| 6. Ecosystem function | partial: removals by functional group | the ecological effect of removals |
| 7. Evidence and trust | strong: every case graded | automated claim checking at scale |

## Questions to take up

### A. Language technology for wildlife-crime evidence

Most evidence of wildlife crime is text: news reports, court records, marketplace listings. Recent
natural language processing research addresses the exact problems WildTrace's pipeline hits.

- **A1. An open event-extraction benchmark for wildlife seizures.** One report often describes several
  seizures, arrests and court outcomes. Document-level multi-event extraction (Wang, Gui & He 2023)
  handles this; WildTrace's merged cases, each traceable to phrases in its sources, are weak labels for
  a benchmark in the style of PHEE for pharmacovigilance (Sun et al. 2022). *Data:* `cases.json`,
  the private record archive. *Output:* a public dataset and a baseline.
- **A2. Selling, condemning or reporting? Stance for online listings.** WildTrace's listing classifier
  plateaued because annotators disagreed on what counts as "trade". Framing the task as stance toward
  the sale of a species makes the definition explicit, and zero-shot stance detection (Liang et al.
  2022a, 2022b) transfers to species never labelled. *Data:* the OWT labelled set (available to
  researchers under its own terms; it contains personal data and is never published).
- **A3. New species, new code words.** Open event extraction (Wang, Zhou & He 2019) and neural topic
  models (Wang, Zhou & He 2019, ATM) can surface emerging trade themes and code words in unlabelled
  news and listings, for human review before any code word is trusted.
- **A4. Checking claims against evidence.** Claims about wildlife trade and disease travel fast.
  Evidence-based claim verification (Dougrez-Lewis et al. 2025) and systems like PANACEA (Zhao et al.
  2023) could grade claims against WildTrace's sources and the literature, extending the case grades
  (official, corroborated, single report) to claims.
- **A5. Narratives of trafficking.** How reports tell the story (who is blamed, who is absent) shapes
  policy. Narrative understanding (Zhu et al. 2023) applied to seizure reporting could measure how
  often local communities, victims and corruption appear.

### B. Crime, money and justice

- **B1. From seizure to sentence.** WildTrace holds far more seizures than convictions. How much of the
  drop is real attrition and how much is reporting? Court records (open judgments where they exist)
  are the missing source.
- **B2. Who profits.** Financial flows are not in open data. What open signals (company registries,
  sanctions lists, trade mis-invoicing) can responsibly be linked to wildlife cases without naming
  individuals in public?
- **B3. Harms of enforcement.** Which enforcement responses reduce trade without harming local people?
  Open evidence on the human costs of anti-poaching is scarce and belongs on the same map.

- **B4. When is "captive-bred" true?** `captive_claims.csv` lists exporter-group pairs whose commercial CITES
  exports switched towards captive-bred declarations. Which of them match real breeding capacity (facility
  counts, species biology, production maths as in Lyons & Natusch 2011), and which do not?

### C. Correcting for who reports

- **C1. Reporting and inspection effort.** Model the probability that a seizure is recorded, by
  country and year, so that routes can be compared without the US dominating (the bias is visible in
  CITES and LEMIS alike).
- **C2. Plant blindness, measured.** Compare plant seizures in trade records with news and online
  attention, species by species.

### D. Security and systems

- **D1. Wildlife crime in the weaponisation of nature.** Where does revenue-generating wildlife
  exploitation by armed groups sit in the typology the report calls for (R5.1-R5.5)? Which cases in
  the literature meet which criteria (Douglas & Alie 2014)?
- **D2. Ports and chokepoints.** Which ports and airports concentrate seizures, and do they coincide
  with the shipping chokepoints the report maps for trade resilience?
- **D3. Removals and ecosystem services.** Link seizure volumes by functional group (seed dispersers,
  predators, reef builders, timber trees) to the ecosystem services the report treats as critical
  natural infrastructure.

## Data you can use today

| File | What | Licence |
| --- | --- | --- |
| `web/data/cases.csv` | cases from public reports, graded | CC BY 4.0 |
| `web/data/cites_seized_flows.csv` | CITES seized shipments by origin, exporter, importer | CITES terms (non-commercial) |
| `web/data/lemis_seized_flows.csv` | imports seized at US ports by origin | CC BY 4.0 |
| `web/data/captive_claims.csv` | captive-bred share of commercial CITES exports, per exporter and group | CITES terms (non-commercial) |
| `web/data/zoonoses.json` | VIRION viruses per group, WHO outbreak reports | ODbL 1.0 |
| `pipeline/wildtrace/resources/lexicon*.yaml` | multilingual species and trade vocabulary | CC BY 4.0 |

Cite the data as: Verma, T. K. (2026). *WildTrace: the open atlas of illegal wildlife trade.* Zenodo.
https://doi.org/10.5281/zenodo.22902819

## How to contribute

Open an issue titled with the question number (for example "A2: stance for listings"), say what you
plan to do, and link your preprint or notebook when it exists. Results that change the published data
go through a pull request with tests. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## References

- Agile Initiative (2026). *Environment and National Security: Exploring the Risk Pathways.* Forward-looking research agenda. Oxford Martin School, University of Oxford.
- Carlson, C. J. et al. (2022). The Global Virome in One Network (VIRION). *mBio* 13, e02985-21. https://doi.org/10.1128/mbio.02985-21
- Dougrez-Lewis, J. et al. (2025). Assessing the reasoning capabilities of LLMs in the context of evidence-based claim verification. *Findings of ACL 2025.* https://doi.org/10.18653/v1/2025.findings-acl.1059
- Douglas, L. R. & Alie, K. (2014). High-value natural resources: linking wildlife conservation to international conflict, insecurity, and development concerns. *Biological Conservation* 171, 270-277. https://doi.org/10.1016/j.biocon.2014.01.031
- Duffy, R. (2015). War, by conservation. *Geoforum* 69, 238-248. https://doi.org/10.1016/j.geoforum.2015.09.014
- Eskew, E. A. et al. (2020). United States wildlife and wildlife product imports from 2000-2014. *Scientific Data* 7, 22. https://doi.org/10.1038/s41597-020-0354-5
- Kurland, J. et al. (2017). Wildlife crime: a conceptual integration, literature review, and methodological critique. *Crime Science* 6, 4. https://doi.org/10.1186/s40163-017-0066-0
- Liang, B. et al. (2022a). Zero-shot stance detection via contrastive learning. *Proceedings of the ACM Web Conference 2022.* https://doi.org/10.1145/3485447.3511994
- Liang, B. et al. (2022b). JointCL: a joint contrastive learning framework for zero-shot stance detection. *ACL 2022.* https://doi.org/10.18653/v1/2022.acl-long.7
- Lunstrum, E. (2014). Green militarization: anti-poaching efforts and the spatial contours of Kruger National Park. *Annals of the Association of American Geographers* 104, 816-832. https://doi.org/10.1080/00045608.2014.912545
- Lyons, J. A. & Natusch, D. J. D. (2011). Wildlife laundering through breeding farms: illegal harvest, population declines and a means of regulating the trade of green pythons (*Morelia viridis*) from Indonesia. *Biological Conservation* 144, 3073-3081. https://doi.org/10.1016/j.biocon.2011.10.002
- Margulies, J. D. et al. (2019). Illegal wildlife trade and the persistence of "plant blindness". *Plants, People, Planet* 1, 173-182. https://doi.org/10.1002/ppp3.10053
- Marshall, B. M. et al. (2025). Tracing trade: mapping the global dimensions of US wildlife imports. *Current Biology* 35, 3959-3972. https://doi.org/10.1016/j.cub.2025.07.012
- Massé, F. et al. (2020). Conservation and crime convergence? Situating the 2018 London Illegal Wildlife Trade Conference. *Journal of Political Ecology* 27, 23-42. https://doi.org/10.2458/v27i1.23543
- Scheffers, B. R. et al. (2019). Global wildlife trade across the tree of life. *Science* 366, 71-76. https://doi.org/10.1126/science.aav5327
- Stringham, O. C. et al. (2021). Dataset of seized wildlife and their intended uses. *Data in Brief* 39, 107531. https://doi.org/10.1016/j.dib.2021.107531
- Sun, Z. et al. (2022). PHEE: a dataset for pharmacovigilance event extraction from text. *EMNLP 2022.* https://doi.org/10.18653/v1/2022.emnlp-main.376
- 't Sas-Rolfes, M. et al. (2019). Illegal wildlife trade: scale, processes, and governance. *Annual Review of Environment and Resources* 44, 201-228. https://doi.org/10.1146/annurev-environ-101718-033253
- Wang, R., Zhou, D. & He, Y. (2019). Open event extraction from online text using a generative adversarial network. *EMNLP-IJCNLP 2019.* https://doi.org/10.18653/v1/d19-1027
- Wang, R., Zhou, D. & He, Y. (2019). ATM: adversarial-neural topic model. *Information Processing & Management* 56, 102098. https://doi.org/10.1016/j.ipm.2019.102098
- Wang, X., Gui, L. & He, Y. (2023). Document-level multi-event extraction with event proxy nodes and Hausdorff distance minimization. *ACL 2023.* https://doi.org/10.18653/v1/2023.acl-long.563
- Wittemyer, G. et al. (2014). Illegal killing for ivory drives global decline in African elephants. *PNAS* 111, 13117-13121. https://doi.org/10.1073/pnas.1403984111
- Zhao, R. et al. (2023). PANACEA: an automated misinformation detection system on COVID-19. *EACL 2023 System Demonstrations.* https://doi.org/10.18653/v1/2023.eacl-demo.9
- Zhu, L., Zhao, R., Gui, L. & He, Y. (2023). Are NLP models good at tracing thoughts: an overview of narrative understanding. *Findings of EMNLP 2023.* https://doi.org/10.18653/v1/2023.findings-emnlp.677
