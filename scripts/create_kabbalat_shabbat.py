#!/usr/bin/env python3
"""Descarga Kabalat Shabat de Sefaria y crea una colección interlineal nueva.

Cada fila conserva el menor segmento de Sefaria que puede leerse como español
natural. La traducción inglesa de Sefaria es el texto puente hacia el español.
"""
import csv, html, json, re, time
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "texts" / "sidur" / "ashekenaz" / "shabat" / "kabalat_shabat"
BASE = "Siddur Ashkenaz, Shabbat, Kabbalat Shabbat, "
PARTS = [
    ("01_yedid_nefesh", "Yedid Nefesh"), ("02_salmo_95", "Psalm 95"),
    ("03_salmo_96", "Psalm 96"), ("04_salmo_97", "Psalm 97"),
    ("05_salmo_98", "Psalm 98"), ("06_salmo_99", "Psalm 99"),
    ("07_salmo_29", "Psalm 29"), ("08_ana_bekoaj", "Ana Bekoach"),
    ("09_leja_dodi", "Lekha Dodi"), ("10_salmo_92", "Psalm 92"),
    ("11_salmo_93", "Psalm 93"), ("12_kadish_del_doliente", "Mourner's Kaddish"),
    ("13_bameh_madlikin", "Bameh Madlikin"), ("14_kadish_derabanan", "Kaddish DeRabbanan"),
]
TITLES = {"Yedid Nefesh": "YEDID NÉFESH", "Lekha Dodi": "LEJÁ DODÍ", "Ana Bekoach": "ANÁ BEJÓAJ", "Mourner's Kaddish": "KADISH DEL DOLIENTE", "Bameh Madlikin": "BAMEH MADLIKIN", "Kaddish DeRabbanan": "KADISH DERABANÁN"}

def get_json(url):
    with urlopen(url, timeout=30) as response:
        return json.load(response)

def source_segments(part):
    ref = BASE + part
    url = "https://www.sefaria.org/api/v3/texts/" + quote(ref, safe="") + "?version=source&version=english&return_format=text_only"
    data = get_json(url)
    hebrew = next(version for version in data["versions"] if version["language"] == "he")
    english = next(version for version in data["versions"] if version["language"] == "en")
    if len(hebrew["text"]) != len(english["text"]):
        raise RuntimeError(f"{part}: Sefaria devolvió segmentos hebreo/inglés desalineados")
    return hebrew, english

def translate_contextual(source, bridge, cache):
    requests = [("en", english) if english else ("he", hebrew) for hebrew, english in zip(source, bridge)]
    missing = list(dict.fromkeys(request for request in requests if request not in cache))
    for language, segment in missing:
        url = "https://translate.googleapis.com/translate_a/single?" + urlencode([( "client", "gtx"), ("sl", language), ("tl", "es"), ("dt", "t"), ("q", segment)])
        data = get_json(url)
        cache[(language, segment)] = "".join(piece[0] or "" for piece in data[0]).strip()
        time.sleep(0.05)
    return [cache[request] for request in requests]

def split_sentences(segment):
    return [piece.strip() for piece in re.split(r"(?<=[.:!?])\s+", segment) if piece.strip()]

def smallest_aligned_segments(source, bridge):
    aligned_source, aligned_bridge = [], []
    for hebrew, english in zip(source, bridge):
        hebrew_parts, english_parts = split_sentences(hebrew), split_sentences(english)
        if len(hebrew_parts) == len(english_parts):
            aligned_source.extend(hebrew_parts)
            aligned_bridge.extend(english_parts)
        else:
            aligned_source.append(hebrew)
            aligned_bridge.append(english)
    return aligned_source, aligned_bridge

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = {}
    for filename, part in PARTS:
        hebrew, english = source_segments(part)
        source = [re.sub(r"<[^>]+>", "", html.unescape(segment)).strip() for segment in hebrew["text"]]
        bridge = [re.sub(r"<[^>]+>", "", html.unescape(segment)).strip() for segment in english["text"]]
        source, bridge = smallest_aligned_segments(source, bridge)
        translations = translate_contextual(source, bridge, cache)
        title = TITLES.get(part, part.upper().replace("PSALM", "SALMO"))
        rows = [
            ["original", "translation", "phonetics", "format", "notes"],
            [title, title, "", "part", ""],
            [f"Fuente hebrea: Sefaria, {hebrew['versionTitle']}, {hebrew['versionSource']}, licencia {hebrew['license']}", f"Fuente hebrea: Sefaria, {hebrew['versionTitle']}, licencia {hebrew['license']}", "", "license", ""],
            [f"Fuente auxiliar inglesa: Sefaria, {english['versionTitle']}, {english['versionSource']}, licencia {english['license']}", f"Fuente auxiliar inglesa: Sefaria, {english['versionTitle']}, licencia {english['license']}", "", "license", ""],
        ]
        rows.extend([[original, translation, "", "", ""] for original, translation in zip(source, translations) if original])
        with (OUT / f"{filename}.csv").open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle, lineterminator="\n").writerows(rows)
        print(f"{filename}: {len(source)} segmentos")

if __name__ == "__main__":
    main()
