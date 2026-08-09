#!/usr/bin/env python3
"""Regenera ``phonetics`` con fonética sefardí orientada al español.

Uso:
  python scripts/generate_sephardic_phonetics.py [--write] [ruta]

Sin ``--write`` solo informa los cambios. El análisis privilegia el
diccionario de kamatz, luego el carácter qamatz-qatan explícito, y después
taamim, meteg y makaf.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "texts"
HEBREW_LETTER = re.compile(r"[\u05d0-\u05ea]")
HEBREW_CLUSTER = re.compile(r"[\u05d0-\u05ea][\u0591-\u05c7]*")
HEBREW_WORD = re.compile(
    r"[\u05d0-\u05ea][\u0591-\u05c7]*(?:[\u05d0-\u05ea][\u0591-\u05c7]*)*"
    r"(?:[־-][\u05d0-\u05ea][\u0591-\u05c7]*(?:[\u05d0-\u05ea][\u0591-\u05c7]*)*)*"
)

MARK = {
    "sheva": "\u05b0", "hataf_segol": "\u05b1", "hataf_patah": "\u05b2",
    "hataf_qamats": "\u05b3", "hiriq": "\u05b4", "tsere": "\u05b5",
    "segol": "\u05b6", "patah": "\u05b7", "qamats": "\u05b8",
    "holam": "\u05b9", "qubuts": "\u05bb", "dagesh": "\u05bc",
    "sin_dot": "\u05c2", "qamats_qatan": "\u05c7", "meteg": "\u05bd",
}

# Prioridad absoluta: clave sin niqqud, valor = índice de consonante: vocal.
KAMATZ_OVERRIDES: dict[str, dict[int, str]] = {
    "כל": {0: "o"}, "בכל": {1: "o"}, "לכל": {1: "o"},
    "חכמה": {0: "o"}, "אמנם": {0: "o"},
}
FINALS = str.maketrans({"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"})
ACCENTED = str.maketrans({"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú"})


@dataclass(frozen=True)
class Cluster:
    letter: str
    marks: str

    def has(self, mark: str) -> bool:
        return mark in self.marks


def clusters_for(word: str) -> list[Cluster]:
    return [Cluster(match.group()[0], match.group()[1:]) for match in HEBREW_CLUSTER.finditer(unicodedata.normalize("NFC", word))]


def bare_hebrew(clusters: list[Cluster]) -> str:
    return "".join(cluster.letter for cluster in clusters).translate(FINALS)


def has_vowel_mark(cluster: Cluster) -> bool:
    return re.search(r"[\u05b1-\u05bb\u05c7]", cluster.marks) is not None


def has_accent_or_meteg(cluster: Cluster) -> bool:
    return re.search(r"[\u0591-\u05af]", cluster.marks) is not None or cluster.has(MARK["meteg"])


def is_mater_ei(cluster: Cluster, index: int, clusters: list[Cluster]) -> bool:
    previous = clusters[index - 1] if index else None
    return bool(
        cluster.letter == "י" and not has_vowel_mark(cluster) and previous
        and (previous.has(MARK["tsere"]) or previous.has(MARK["segol"]))
    )


def vowel_of(cluster: Cluster, index: int, clusters: list[Cluster], bare: str, has_following_maqaf: bool) -> str:
    shuruk = cluster.letter == "ו" and cluster.has(MARK["dagesh"]) and not has_vowel_mark(cluster)
    if shuruk:
        return "u"
    previous = clusters[index - 1] if index else None
    if cluster.letter == "י" and not has_vowel_mark(cluster) and previous:
        if previous.has(MARK["tsere"]) or previous.has(MARK["segol"]):
            return "i"
    for name, value in (
        ("hataf_patah", "a"), ("hataf_segol", "e"), ("hataf_qamats", "o"),
        ("patah", "a"), ("tsere", "e"), ("segol", "e"), ("hiriq", "i"),
        ("holam", "o"), ("qubuts", "u"),
    ):
        if cluster.has(MARK[name]):
            return value

    forced = KAMATZ_OVERRIDES.get(bare, {}).get(index)
    if forced:
        return forced
    if cluster.has(MARK["qamats_qatan"]):
        return "o"
    if not cluster.has(MARK["qamats"]):
        return ""

    following = clusters[index + 1] if index + 1 < len(clusters) else None
    if following and following.has(MARK["sheva"]) and not has_accent_or_meteg(cluster):
        return "o"
    if has_following_maqaf and following and index == len(clusters) - 2 and not has_vowel_mark(following) and not has_accent_or_meteg(cluster):
        return "o"
    return "a"


def vocal_sheva(cluster: Cluster, index: int, clusters: list[Cluster]) -> bool:
    if index == 0 or cluster.has(MARK["meteg"]):
        return True
    previous = clusters[index - 1]
    if has_accent_or_meteg(previous):
        return True
    previous_is_shuruk = previous.letter == "ו" and previous.has(MARK["dagesh"]) and not has_vowel_mark(previous)
    return previous_is_shuruk or previous.has(MARK["sheva"]) or cluster.has(MARK["dagesh"])


def consonant_of(cluster: Cluster, index: int, clusters: list[Cluster]) -> str:
    shuruk = cluster.letter == "ו" and cluster.has(MARK["dagesh"]) and not has_vowel_mark(cluster)
    if cluster.letter == "ו" and (cluster.has(MARK["holam"]) or shuruk):
        return ""
    if cluster.letter in {"א", "ע"}:
        return ""
    if cluster.letter == "ה" and index == len(clusters) - 1 and not cluster.has(MARK["dagesh"]):
        return ""
    if cluster.letter == "י" and not has_vowel_mark(cluster) and index:
        previous = clusters[index - 1]
        if previous.has(MARK["hiriq"]) or previous.has(MARK["tsere"]) or previous.has(MARK["segol"]):
            return ""

    dotted = cluster.has(MARK["dagesh"])
    return {
        "ב": "b" if dotted else "v", "ג": "g", "ד": "d", "ה": "h", "ו": "v", "ז": "z",
        "ח": "j", "ט": "t", "י": "y", "כ": "k" if dotted else "j", "ך": "k" if dotted else "j",
        "ל": "l", "מ": "m", "ם": "m", "נ": "n", "ן": "n", "ס": "s",
        "פ": "p" if dotted else "f", "ף": "p" if dotted else "f", "צ": "tz", "ץ": "tz",
        "ק": "k", "ר": "r", "ש": "s" if cluster.has(MARK["sin_dot"]) else "sh", "ת": "t",
    }.get(cluster.letter, cluster.letter)


def transliterate_hebrew_word(word: str, has_following_maqaf: bool = False) -> str:
    clusters = clusters_for(word)
    if not clusters:
        return word
    bare = bare_hebrew(clusters)
    units: list[dict[str, object]] = []
    for index, cluster in enumerate(clusters):
        silent_sheva = cluster.has(MARK["sheva"]) and not vocal_sheva(cluster, index, clusters)
        vowel = "" if silent_sheva else ("e" if cluster.has(MARK["sheva"]) else vowel_of(cluster, index, clusters, bare, has_following_maqaf))
        units.append({
            "text": consonant_of(cluster, index, clusters) + vowel,
            "vowel": vowel,
            "nucleus": bool(vowel) and not is_mater_ei(cluster, index, clusters),
            "stressed": has_accent_or_meteg(cluster),
        })

    accent_index = next((index for index in range(len(units) - 1, -1, -1) if units[index]["stressed"]), -1)
    if accent_index >= 0:
        stress_index = next((index for index in range(accent_index, -1, -1) if units[index]["nucleus"]), -1)
    else:
        stress_index = next((index for index in range(len(units) - 1, -1, -1) if units[index]["nucleus"]), -1)
    nuclei = [index for index, unit in enumerate(units) if unit["nucleus"]]
    output = "".join(str(unit["text"]) for unit in units)
    default_stress = nuclei[-2] if len(nuclei) > 1 and re.search(r"[aeiouáéíóúnñs]$", output, re.IGNORECASE) else (nuclei[-1] if nuclei else -1)
    if stress_index >= 0 and stress_index != default_stress:
        vowel = str(units[stress_index]["vowel"])
        units[stress_index]["text"] = str(units[stress_index]["text"]).replace(vowel, vowel.translate(ACCENTED), 1)
    return "".join(str(unit["text"]) for unit in units)


def transliterate_text(text: str) -> str:
    def replace_word(match: re.Match[str]) -> str:
        parts = re.split(r"[־-]", match.group())
        return "-".join(transliterate_hebrew_word(part, index < len(parts) - 1) for index, part in enumerate(parts))
    return HEBREW_WORD.sub(replace_word, text)


def csv_files(source: Path) -> list[Path]:
    return [source] if source.is_file() else sorted(source.rglob("*.csv"))


def process_file(file: Path, write: bool) -> int:
    with file.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return 0
    headers = rows[0]
    try:
        original_index, phonetics_index = headers.index("original"), headers.index("phonetics")
    except ValueError as error:
        raise ValueError(f"{file}: faltan columnas original o phonetics") from error
    format_index = headers.index("format") if "format" in headers else None
    changed = 0
    for row in rows[1:]:
        row.extend([""] * (len(headers) - len(row)))
        original = row[original_index]
        if (format_index is not None and row[format_index]) or not HEBREW_LETTER.search(original):
            continue
        generated = transliterate_text(original)
        if row[phonetics_index] != generated:
            row[phonetics_index] = generated
            changed += 1
    if write and changed:
        with file.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle, lineterminator="\n").writerows(rows)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="reemplaza la columna phonetics")
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_INPUT, help="archivo CSV o carpeta texts")
    args = parser.parse_args()
    source = args.path if args.path.is_absolute() else (Path.cwd() / args.path).resolve()
    if not source.exists():
        parser.error(f"no existe: {source}")
    files = csv_files(source)
    changed = sum(process_file(file, args.write) for file in files)
    action = "Actualizadas" if args.write else "Vista previa:"
    print(f"{action} {changed} filas en {len(files)} archivo(s).")
    if not args.write:
        print("No se escribió ningún CSV. Agregá --write para reemplazar la columna phonetics.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
