import json

import pytest

from wildtrace import lexicon
from wildtrace.extract.cases import cluster, summarise
from wildtrace.extract.events import extract, find_places, is_enforcement_candidate
from wildtrace.privacy import assert_public_safe, find_pii, scrub
from wildtrace.schema import Record


def rec(title, **kw):
    return Record(url=f"https://example.org/{abs(hash(title))}", title=title, **kw)


# ------------------------------------------------------------------ lexicon
def test_lexicon_parses_and_has_groups():
    lex = lexicon.load()
    assert len(lex["groups"]) >= 15
    for gid, g in lex["groups"].items():
        assert g["label"] and g["terms"], gid


@pytest.mark.parametrize("text,group", [
    ("Asli kasturi ki kimat", "musk_deer"),
    ("Original Hatha Jodi test", "monitor_lizard"),
    ("दोमुंहा सांप बेचने वाले गिरफ्तार", "sand_boa"),
    ("12 kg pangolin scales seized", "pangolin"),
    ("Polisi sita sisik trenggiling", "pangolin"),
    ("Thu giữ sừng tê giác", "rhino"),
    ("ఎర్రచందనం smuggling", "red_sanders"),
])
def test_multilingual_species_match(text, group):
    assert group in lexicon.species_groups(text)


def test_no_false_species_from_substrings():
    assert lexicon.species_groups("The tigerish mood of the market") == []


# ------------------------------------------------------------------ privacy
@pytest.mark.parametrize("s", ["call 8010363896", "+91 98348 18574", "wa.me/919999999999", "mail x.y@z.com"])
def test_scrub_removes_contacts(s):
    assert not find_pii(scrub(s))


def test_publish_gate_blocks_pii_and_identity_fields():
    with pytest.raises(ValueError):
        assert_public_safe([{"summary": "Seizure · call 9876543210"}])
    with pytest.raises(ValueError):
        assert_public_safe([{"summary": "ok", "channel": "seller"}])
    assert_public_safe([{"summary": "Seizure · Pangolin · 12 kg · Odisha"}])


# --------------------------------------------------------------- extraction
def test_extract_full_event():
    e = extract(rec("DRI seizes 12 kg of pangolin scales worth Rs 1.2 crore at Imphal; two persons arrested. "
                    "The consignment was bound for Myanmar by truck.", country_hint="IN"))
    assert e.species == ["pangolin"]
    assert e.place["name"] == "Imphal" and e.place["admin1"] == "Manipur"
    assert e.route == ["Imphal", "Myanmar"]
    assert {"value": 12.0, "unit": "kg"} in e.quantities
    assert e.value_inr == 1.2e7
    assert e.people_arrested == 2
    assert "DRI" in e.agencies and "road" in e.modes
    assert {"seizure", "arrest"} <= set(e.event_types)


def test_place_longest_match_wins():
    names = [p.name for _, p in find_places("Seized near New Delhi and in West Bengal")]
    assert "Delhi" in names and "West Bengal" in names


def test_candidate_needs_species_and_enforcement():
    assert is_enforcement_candidate("Tiger skin seized in Nagpur")
    assert not is_enforcement_candidate("Tiger census shows rise in Nagpur")
    assert not is_enforcement_candidate("Gold seized at Chennai airport")


# --------------------------------------------------------------- clustering
def test_same_incident_merges_and_summary_has_no_headline_names():
    a = extract(rec("Ramesh Kumar held with 5 kg pangolin scales in Bhubaneswar", published="2026-08-01", outlet="a.in"))
    b = extract(rec("Pangolin scales 5 kg seized in Bhubaneswar, one held", published="2026-08-02", outlet="b.in"))
    c = extract(rec("Tiger skin seized in Nagpur", published="2026-08-01", outlet="c.in"))
    groups = cluster([a, b, c])
    assert sorted(len(g) for g in groups) == [1, 2]
    merged = summarise(next(g for g in groups if len(g) == 2))
    assert merged["n_sources"] == 2
    assert "Ramesh" not in json.dumps(merged["summary"])
    assert merged["place"]["name"] == "Bhubaneswar"


# ------------------------------------------------ real headlines (GDELT, Sep 2026)
@pytest.mark.parametrize("title,place,qty,arrested", [
    ("352 Pangolin Scales Seized in Malkangiri Forest , Six Arrested", "Malkangiri", (352.0, "scales"), 6),
    ("2 Held in Pudukkottai for Poaching Monitor Lizards", "Pudukkottai", None, 2),
    ("3 arrested with 4 monitor lizards in Paonta Sahib", "Pāonta Sāhib", (4.0, "lizards"), 3),
])
def test_real_headlines(title, place, qty, arrested):
    e = extract(rec(title, country_hint="IN"))
    assert e.place and e.place["name"] == place
    if qty:
        assert {"value": qty[0], "unit": qty[1]} in e.quantities
    assert e.people_arrested == arrested


def test_country_level_report_merges_with_district_report():
    a = extract(rec("30 tokay geckos seized in Golaghat, two held", published="2026-09-20", country_hint="IN"))
    b = extract(rec("India: 30 tokay geckos seized, two arrested", published="2026-09-20", country_hint="IN"))
    assert len(cluster([a, b])) == 1
    assert summarise(cluster([a, b])[0])["place"]["name"] == "Golaghat"


def test_developing_story_threads_within_state_but_not_across_states():
    a = extract(rec("Five orangutans rescued in Balasore forest, smuggling suspected", published="2026-09-08"))
    b = extract(rec("Odisha STF probes orangutan smuggling network after Balasore rescue", published="2026-09-16"))
    c = extract(rec("Orangutan seized in Ranchi, Jharkhand", published="2026-09-14"))
    groups = cluster([a, b, c])
    assert sorted(len(g) for g in groups) == [1, 2]


def test_codeword_hits_flag_but_do_not_make_species():
    from wildtrace import lexicon
    t = "Selling striped t-shirt, call now"
    assert [h["term"] for h in lexicon.codeword_hits(t)] == ["striped t-shirt"]
    assert lexicon.species_groups(t) == []


# ------------------------------------------- locations in Hindi / Google News headlines
@pytest.mark.parametrize("title,place", [
    ("ओडिशा में कछुआ तस्करी के रैकेट का भंडाफोड़, 55 जिंदा कछुओं का रेस्क्यू; 4 गिरफ्तार", "Odisha"),
    ("कुशीनगर में 270 तोते बरामद, एक तस्कर गिरफ्तार", "Kushinagar"),
    ("सीधी: वन्यजीव तस्करी गिरोह का पर्दाफाश, तेंदुए की खाल बरामद", "Sidhi"),
    ("मेघालय के री-भोई में पैंगोलिन के शल्क जब्त, दो गिरफ्तार", "Meghalaya"),
    ("Leopard Skin Smuggling Plot Foiled in Kandhamala; One Held", "Kandhamal"),
    ("2 leopard skins seized in pan-India raids", "India"),
])
def test_headline_locations(title, place):
    e = extract(rec(title, country_hint="IN"))
    assert e.place and e.place["name"] == place and e.place_basis == "text"


def test_hindi_loanword_is_not_a_town():
    # "रैकेट" (racket) skeleton-matches the town Raikot; the stoplist must stop it.
    names = [p.name for _, p in find_places("ओडिशा में कछुआ तस्करी के रैकेट का भंडाफोड़", "IN")]
    assert names == ["Odisha"]


@pytest.mark.parametrize("title", [
    "Kattalan - Malayalam ivory smuggling action thriller starring Antony Varghese premieres on SonyLIV",
    "430 पीस नेपाली कस्तूरी शराब जब्त, तस्कर धराया",
    "Six arrested in Ivory Park as traffic police recover stolen transformers",
])
def test_false_positives_are_rejected(title):
    assert not is_enforcement_candidate(title)


def test_publisher_region_is_a_labelled_fallback_only():
    e = extract(rec("13 Star Tortoise hatchlings seized, man arrested", outlet="ahmedabadmirror.com"))
    assert e.place["name"] == "Ahmedabad" and e.place_basis == "outlet"
    named = extract(rec("Star tortoises seized in Nagpur", outlet="ahmedabadmirror.com"))
    assert named.place["name"] == "Nagpur" and named.place_basis == "text"


def test_same_seizure_in_two_languages_merges():
    a = extract(rec("Six held with pangolin scales in Malkangiri, Odisha", published="2026-09-13", country_hint="IN"))
    b = extract(rec("ओडिशा : पैंगोलिन की खाल के साथ छह लोग गिरफ्तार", published="2026-09-14", country_hint="IN"))
    assert len(cluster([a, b])) == 1


def test_bharat_is_india_not_baraut():
    names = [p.name for _, p in find_places("ओडिशा के जंगल में मिले 5 Orangutan! भारत में कैसे पहुँचे?", "IN")]
    assert "Baraut" not in names and "India" in names


def test_case_place_is_the_most_cited_specific_place():
    evs = [extract(rec(f"Orangutans rescued in Balasore forest, report {i}", published="2026-09-08")) for i in range(3)]
    evs.append(extract(rec("Rescued orangutans shifted to Nandankanan zoo, smuggling probe on", published="2026-09-10")))
    assert summarise(evs)["place"]["name"] == "Balasore"


def test_hash_ids_are_not_mistaken_for_phone_numbers():
    assert_public_safe([{"id": "a6774353051b", "summary": "Seizure · Pangolin · Lagos"}])
    with pytest.raises(ValueError):
        assert_public_safe([{"id": "x", "summary": "call 6774353051"}])


def test_source_tiers():
    from wildtrace.sources_tier import tier
    assert tier("https://www.gov.br/pf/pt-br/assuntos/noticias/x") == "official"
    assert tier("https://www.justice.gov/usao-sdfl/pr/x") == "official"
    assert tier("https://pib.gov.in/PressReleasePage.aspx?PRID=1") == "official"
    assert tier("https://www.traffic.org/news/x") == "ngo"
    assert tier("https://timesofindia.indiatimes.com/x") == "media"
    # a look-alike domain is not a government one
    assert tier("https://govtnews.example.com/x") == "media"


def test_official_publisher_names():
    from wildtrace.sources_tier import tier
    assert tier("PIB") == "official" and tier("Polícia Federal") == "official"
    assert tier("Agence Ivoirienne de Presse (AIP)") == "media"  # a state news agency is not an enforcement body


def test_og_card_counts_are_one_argument():
    """The overlay takes a single object: two positional parameters silently
    rendered "1,251,59 cases - undefined countries" on the shared card."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "scripts" / "make_og.py").read_text(encoding="utf-8")
    assert "({ cases, countries }) =>" in src
    assert re.search(r"pg\.evaluate\(OVERLAY, \{", src)
    assert "${cases} cases" in src and "${countries} countries" in src


def test_trivia_cards_are_checkable():
    """Sourced cards must carry a source; derived cards must match the data they
    describe, since a trivia box is exactly where a wrong number goes unnoticed."""
    import json
    from pathlib import Path
    from wildtrace.publish import trivia
    web = Path(__file__).resolve().parents[1] / "web" / "data"
    cases = json.loads((web / "cases.json").read_text(encoding="utf-8"))
    species = json.loads((web / "species.json").read_text(encoding="utf-8"))
    cards = trivia(cases, species if isinstance(species, dict) else {})
    reported = [c for c in cards if c["kind"] == "reported"]
    assert len(reported) >= 8
    for c in reported:
        assert c["source"]["url"].startswith("https://") and c["source"]["year"] >= 2019
        assert c["fact"] and c["detail"]
    ours = {c["id"]: c for c in cards if c["kind"] == "ours"}
    n = len(cases)
    single = sum(1 for c in cases if c.get("verification") == "single")
    unmapped = sum(1 for c in cases if not c.get("place"))
    assert f"{single:,} of {n:,}" in ours["wt_single"]["detail"]
    assert str(round(100 * single / n)) + "%" in ours["wt_single"]["fact"]
    assert f"{unmapped:,} cases name no place" in ours["wt_unmapped"]["fact"]
    for c in ours.values():
        assert "reported, not where it happens" in c["caveat"]
    # the catch-all group is never the headline species
    assert "unspecified" not in ours.get("wt_top_species", {}).get("fact", "").lower()


def test_seo_pages_are_crawlable_and_honest(tmp_path):
    """The static layer is what a search engine and an answer engine actually read, so it must
    carry the numbers, the licence, the canonical URL and the reporting caveat."""
    from wildtrace.seo import build_pages, slug
    cases = [{"id": "abc123", "date": "2026-03-04", "kind": "seizure", "summary": "Seizure · Pangolin · Bengaluru",
              "species": ["pangolin"], "place": {"name": "Bengaluru", "admin1": "Karnataka", "country": "IN",
                                                 "lat": 12.97, "lon": 77.59, "type": "city"},
              "sources": [{"url": "https://example.gov.in/x", "outlet": "PIB", "date": "2026-03-04", "tier": "official"}],
              "n_sources": 3, "n_outlets": 2, "verification": "official", "people_arrested": 2, "agencies": ["DRI"]}]
    species = {"pangolin": {"label": "Pangolin", "cites": "I", "taxa": ["Manis javanica"]}}
    countries = {"IN": {"name": "India"}}
    meta = {"window": ["2024-01-15", "2026-09-22"], "verification": {"official": 1, "corroborated": 0, "single": 0},
            "coverage": {"mapped": 1, "country_only": 0, "unmapped": 0}}
    n = build_pages(cases, species, countries, meta, tmp_path)
    assert n >= 4
    case_html = (tmp_path / "case" / "abc123.html").read_text(encoding="utf-8")
    assert "<h1>" in case_html and "Bengaluru" in case_html
    assert "application/ld+json" in case_html and "creativecommons.org/licenses/by/4.0" in case_html
    assert 'rel="canonical"' in case_html
    assert "never names" in case_html or "never who they are" in case_html      # the privacy line survives
    assert "reported" in case_html
    sp_html = (tmp_path / "species" / f"{slug('pangolin')}.html").read_text(encoding="utf-8")
    assert "1</b> cases" in sp_html or "recorded <b>1</b>" in sp_html
    assert "not where it happens" in sp_html                                     # the caveat travels with the number
    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap:" in robots and "GPTBot" in robots and "ClaudeBot" in robots
    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>" in sitemap and "case/abc123.html" in sitemap
    llms = (tmp_path / "llms.txt").read_text(encoding="utf-8")
    assert "doi.org/10.5281/zenodo" in llms and "reported" in llms
    # internal links must be relative, so a fork or a local copy works
    assert 'href="../css/page.css"' in case_html


# ---------------------------------------------------------------- v1.5: flows and zoonoses
def test_cites_taxa_map_most_specific_first():
    from wildtrace.collect.cites import group_of, taxon_index
    sp, hi = taxon_index()
    assert group_of({"Taxon": "Pterocarpus santalinus"}, sp, hi) == "red_sanders"
    assert group_of({"Taxon": "Dalbergia latifolia", "Genus": "Dalbergia"}, sp, hi) == "rosewood"
    assert group_of({"Taxon": "Phataginus tricuspis", "Genus": "Phataginus", "Family": "Manidae"}, sp, hi) == "pangolin"
    assert group_of({"Taxon": "Dendrobium nobile", "Genus": "Dendrobium", "Family": "Orchidaceae"}, sp, hi) == "orchids"
    assert group_of({"Taxon": "Carcharhinus falciformis", "Class": "Elasmobranchii"}, sp, hi) == "shark_ray"
    assert group_of({"Taxon": "Canis lupus", "Genus": "Canis", "Family": "Canidae", "Order": "Carnivora"}, sp, hi) is None


def test_cites_aggregate_keeps_seized_apart_and_drops_domestic(tmp_path):
    from wildtrace.collect.cites import aggregate
    head = "Id,Year,Appendix,Taxon,Class,Order,Family,Genus,Term,Quantity,Unit,Importer,Exporter,Origin,Purpose,Source,Reporter.type\n"
    rows = ["1,2020,II,Pterocarpus santalinus,,,,Pterocarpus,timber,5,kg,CN,IN,,T,I,I",
            "2,2020,II,Pterocarpus santalinus,,,,Pterocarpus,timber,5,kg,CN,AE,IN,T,I,I",
            "3,2020,II,Pterocarpus santalinus,,,,Pterocarpus,timber,5,kg,CN,IN,,T,W,E",
            "4,2020,II,Pterocarpus santalinus,,,,Pterocarpus,timber,5,kg,IN,IN,,T,I,I",   # domestic: dropped
            "5,2010,II,Pterocarpus santalinus,,,,Pterocarpus,timber,5,kg,CN,IN,,T,I,I"]   # before 2015: dropped
    (tmp_path / "trade_db_1.csv").write_text(head + "\n".join(rows), encoding="utf-8")
    d = aggregate(tmp_path)
    assert sorted(map(tuple, d["seized"])) == [("red_sanders", "IN", "AE", "CN", 1), ("red_sanders", "IN", "IN", "CN", 1)]
    assert d["declared"]["red_sanders"] == [["IN", "CN", 1]]


def test_lemis_keeps_only_seized_imports_and_never_counts_twice(tmp_path):
    from wildtrace.collect.lemis import aggregate
    m = ("control_number,genus,species,description,country_origin,country_imp_exp,purpose,source,action,disposition,"
         "shipment_date,import_export,sYear,corrected,correctedGenus,orderCorrected,code_origin,code_imp\n")
    rows = ["1,MANIS,JAVANICA,SCA,Ctry_NG,Ctry_NG,T,W,R,S,2019-05-01,I,2019,Manis javanica,Manis,Pholidota,NG,NG",
            "2,MANIS,JAVANICA,SCA,Ctry_NG,Ctry_NG,T,W,C,C,2019-05-01,I,2019,Manis javanica,Manis,Pholidota,NG,NG",  # cleared
            "3,PYTHON,REGIUS,SKI,Ctry_GH,Ctry_IT,T,W,R,S,2018-01-01,I,2018,Python regius,Python,Squamata,GH,IT",
            "4,CANIS,LUPUS,TRO,Ctry_CA,Ctry_CA,H,W,R,S,2018-01-01,I,2018,Canis lupus,Canis,Carnivora,CA,CA"]      # no group
    (tmp_path / "LEMIS_distributionsAdded_Mammals.csv").write_text(m + "\n".join(rows), encoding="utf-8")
    e = "control_number,class,genus,species,description,country_origin,country_imp_exp,purpose,source,action,disposition,shipment_year,import_export\n"
    (tmp_path / "lemis_2000_2014_cleaned.csv").write_text(e + "\n".join([
        "9,Reptilia,Python,regius,SKI,GH,GH,T,W,R,S,2010,I",            # Marshall covers reptiles: skipped
        "8,Elasmobranchii,Carcharhinus,falciformis,FIN,MX,MX,T,W,R,S,2012,I"]), encoding="utf-8")
    tax = tmp_path / "codebook"
    tax.mkdir()
    (tax / "02_gbif_taxonomic_key.csv").write_text("genus,family,order,class\nManis,Manidae,Pholidota,Mammalia\n", encoding="utf-8")
    d = aggregate(tmp_path, tax)
    assert sorted(map(tuple, d["seized"])) == [("pangolin", "NG", "NG", "US", 1), ("pythons_reptiles", "GH", "IT", "US", 1),
                                               ("shark_ray", "MX", "MX", "US", 1)]
    assert d["detail"]["GH|US"]["via"] == [("IT", 1)]
    assert d["products"]["pangolin"] == [("SCA", 1)]


@pytest.mark.parametrize("title,disease,pathway,countries", [
    ("Ebola disease caused by Bundibugyo virus, Democratic Republic of the Congo & Uganda", "Ebola and Sudan virus disease", "wildlife", ["CD", "UG"]),
    ("Avian Influenza A(H5N1) - Cambodia", "Avian influenza", "birds", ["KH"]),
    ("Middle East respiratory syndrome coronavirus - Kingdom of Saudi Arabia", "MERS", "livestock", ["SA"]),
    ("Yellow fever in the Republic of Congo", "Yellow fever", "vector", ["CG"]),
    ("Lassa fever - Guinea", "Lassa fever", "wildlife", ["GN"]),
])
def test_who_titles_parse_to_disease_pathway_and_country(tmp_path, monkeypatch, title, disease, pathway, countries):
    from wildtrace.collect import zoonoses
    monkeypatch.setattr(zoonoses, "Z", tmp_path)
    (tmp_path / "who_don.json").write_text(json.dumps([{"Title": title, "PublicationDate": "2026-01-01T00:00:00Z", "UrlName": "x"}]), encoding="utf-8")
    [r] = zoonoses.outbreaks()
    assert (r["disease"], r["pathway"], r["countries"]) == (disease, pathway, countries)


def test_non_zoonotic_outbreaks_are_left_out(tmp_path, monkeypatch):
    from wildtrace.collect import zoonoses
    monkeypatch.setattr(zoonoses, "Z", tmp_path)
    (tmp_path / "who_don.json").write_text(json.dumps([{"Title": "Cholera - Haiti", "PublicationDate": "2026-01-01", "UrlName": "y"},
                                                       {"Title": "Poliomyelitis - Pakistan", "PublicationDate": "2026-01-01", "UrlName": "z"}]), encoding="utf-8")
    assert zoonoses.outbreaks() == []


def test_pathways_page_states_evidence_limits_and_gap(tmp_path):
    import json as _json
    from wildtrace import pathways
    from wildtrace.seo import SITE, esc, page
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "flows.json").write_text(_json.dumps({"seized": [["orchids", "TH", "TH", "US", 3], ["pangolin", "NG", "CM", "CN", 2]], "year_min": 2015}))
    cases = [{"kind": "seizure", "verification": "official", "species": ["pangolin"], "countries": ["NG", "CN"], "modes": ["air"]},
             {"kind": "conviction", "verification": "single", "species": ["orchids"], "people_arrested": 2}]
    species = {"pangolin": {"label": "Pangolin"}, "orchids": {"label": "Orchids", "kingdom": "plant"}}
    path, html_ = pathways.build(cases, species, {}, {}, tmp_path, page, esc, SITE)
    assert path == "pathways.html"
    assert "Open evidence: a gap" in html_ and "What the number cannot tell you" in html_
    assert '"@type": "FAQPage"' in html_ and "militarisation" in html_
    e = pathways.evidence(cases, species, tmp_path / "data")
    assert e["cites"] == 5 and e["cites_plants"] == 3 and e["cites_transit"] == 2 and e["cites_us"] == 3
