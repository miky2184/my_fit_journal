#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterable

from sqlalchemy import create_engine, text

# Permette import app.* anche quando lo script viene eseguito da /scripts.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings


STRENGTH_KEYWORDS = {
    "bench",
    "press",
    "squat",
    "deadlift",
    "lunge",
    "row",
    "curl",
    "pull_up",
    "push_up",
    "triceps",
    "biceps",
    "lateral_raise",
    "front_raise",
    "hip_raise",
    "leg_curl",
    "leg_extension",
    "leg_press",
    "calf_raise",
    "shoulder_press",
    "hyperextension",
    "flye",
    "dip",
    "crunch",
    "plank",
    "core",
}

EXCLUDE_KEYWORDS = {
    "pose",
    "warm_up",
    "cardio",
    "indoor_row",
    "elliptical",
    "walk",
    "run",
    "jump_rope",
}

ZONE_RULES = [
    ("chest", "chest"),
    ("bench", "chest"),
    ("flye", "chest"),
    ("shoulder", "shoulders"),
    ("deltoid", "shoulders"),
    ("lateral_raise", "shoulders"),
    ("front_raise", "shoulders"),
    ("triceps", "arms"),
    ("biceps", "arms"),
    ("curl", "arms"),
    ("arm", "arms"),
    ("row", "back"),
    ("pull", "back"),
    ("lat", "back"),
    ("back", "back"),
    ("deadlift", "hamstrings"),
    ("hamstring", "hamstrings"),
    ("glute", "glutes"),
    ("hip", "glutes"),
    ("squat", "quads"),
    ("leg_press", "quads"),
    ("leg_extension", "quads"),
    ("lunge", "quads"),
    ("calf", "calves"),
    ("plank", "core"),
    ("crunch", "core"),
    ("core", "core"),
    ("ab", "core"),
]

ESSENTIAL_CATEGORIES = {
    "bench_press",
    "shoulder_press",
    "row",
    "curl",
    "triceps_extension",
    "deadlift",
    "squat",
    "lunge",
    "leg_curl",
    "calf_raise",
    "hip_raise",
    "pull_up",
    "push_up",
    "lateral_raise",
    "hyperextension",
}

ESSENTIAL_INCLUDE_TOKENS = {
    "bench_press",
    "chest_press",
    "shoulder_press",
    "lat_pulldown",
    "row",
    "deadlift",
    "squat",
    "lunge",
    "leg_curl",
    "leg_extension",
    "leg_press",
    "calf_raise",
    "hip_thrust",
    "hip_raise",
    "triceps_extension",
    "biceps_curl",
    "push_up",
    "pull_up",
    "hyperextension",
}

ESSENTIAL_EXCLUDE_TOKENS = {
    "swiss_ball",
    "bosu",
    "band",
    "kipping",
    "jump",
    "plyo",
    "wheelchair",
    "medicine_ball",
    "single_leg",
    "single_arm",
    "alternating",
    "twist",
    "burpee",
    "clean",
    "snatch",
    "partner",
    "trx",
    "ring",
    "towel",
    "explosive",
    "clapping",
    "hindu",
    "judo",
    "with_reach",
    "with_rotation",
    "tabletop",
}


@dataclass(frozen=True)
class GarminExercise:
    exercise_key: str
    exercise_label: str
    category_key: str
    category_label: str


@dataclass(frozen=True)
class CatalogExercise:
    name: str
    body_zone: str
    source_key: str
    category_key: str



def normalize_key(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_")


def is_strength_row(row: GarminExercise) -> bool:
    hay = " ".join(
        [
            normalize_key(row.category_key),
            normalize_key(row.exercise_key),
            normalize_key(row.exercise_label).replace(" ", "_"),
        ]
    )

    if any(k in hay for k in EXCLUDE_KEYWORDS):
        return False
    return any(k in hay for k in STRENGTH_KEYWORDS)


def infer_body_zone(row: GarminExercise) -> str:
    hay = " ".join(
        [
            normalize_key(row.category_key),
            normalize_key(row.exercise_key),
            normalize_key(row.exercise_label).replace(" ", "_"),
        ]
    )

    for token, zone in ZONE_RULES:
        if token in hay:
            return zone
    return "full_body"


def to_catalog_exercise(row: GarminExercise) -> CatalogExercise:
    name = row.exercise_label.strip()
    zone = infer_body_zone(row)
    return CatalogExercise(
        name=name,
        body_zone=zone,
        source_key=row.exercise_key,
        category_key=row.category_key,
    )


def read_rows(path: Path) -> list[GarminExercise]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        out: list[GarminExercise] = []
        for r in reader:
            out.append(
                GarminExercise(
                    exercise_key=(r.get("exercise_key") or "").strip(),
                    exercise_label=(r.get("exercise_label") or "").strip(),
                    category_key=(r.get("category_key") or "").strip(),
                    category_label=(r.get("category_label") or "").strip(),
                )
            )
    return out


def dedupe_by_exercise_key(rows: Iterable[GarminExercise]) -> list[GarminExercise]:
    seen: set[str] = set()
    out: list[GarminExercise] = []
    for r in rows:
        key = normalize_key(r.exercise_key)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def select_subset(rows: list[GarminExercise], max_total: int, max_per_category: int) -> list[CatalogExercise]:
    strength = [r for r in rows if is_strength_row(r)]

    by_cat: dict[str, list[GarminExercise]] = defaultdict(list)
    for r in strength:
        by_cat[normalize_key(r.category_key)].append(r)

    for cat in by_cat:
        by_cat[cat].sort(key=lambda x: x.exercise_label.lower())

    selected: list[CatalogExercise] = []
    per_cat_counter: Counter[str] = Counter()

    # round-robin categories per bilanciare copertura
    categories = sorted(by_cat.keys())
    idx = 0
    while len(selected) < max_total and categories:
        cat = categories[idx % len(categories)]
        if per_cat_counter[cat] >= max_per_category or not by_cat[cat]:
            categories = [c for c in categories if per_cat_counter[c] < max_per_category and by_cat[c]]
            if not categories:
                break
            idx = 0
            continue

        row = by_cat[cat].pop(0)
        selected.append(to_catalog_exercise(row))
        per_cat_counter[cat] += 1
        idx += 1

    # de-dup by name case-insensitive
    name_seen: set[str] = set()
    deduped: list[CatalogExercise] = []
    for ex in selected:
        nkey = ex.name.strip().lower()
        if not nkey or nkey in name_seen:
            continue
        name_seen.add(nkey)
        deduped.append(ex)

    return deduped


def _complexity_score(exercise_key: str) -> tuple[int, int, str]:
    key = normalize_key(exercise_key)
    token_count = len([t for t in key.split("_") if t])
    excluded_hits = sum(1 for t in ESSENTIAL_EXCLUDE_TOKENS if t in key)
    return (excluded_hits, token_count, key)


def select_gym_essential(rows: list[GarminExercise], max_total: int, max_per_category: int) -> list[CatalogExercise]:
    unique = dedupe_by_exercise_key(rows)
    filtered: list[GarminExercise] = []
    for r in unique:
        category = normalize_key(r.category_key)
        if category not in ESSENTIAL_CATEGORIES:
            continue
        key = normalize_key(r.exercise_key)
        if not any(tok in key for tok in ESSENTIAL_INCLUDE_TOKENS):
            continue
        if any(tok in key for tok in ESSENTIAL_EXCLUDE_TOKENS):
            continue
        filtered.append(r)

    by_cat: dict[str, list[GarminExercise]] = defaultdict(list)
    for r in filtered:
        by_cat[normalize_key(r.category_key)].append(r)

    selected_rows: list[GarminExercise] = []
    for cat in sorted(by_cat.keys()):
        arr = sorted(by_cat[cat], key=lambda x: _complexity_score(x.exercise_key))
        selected_rows.extend(arr[:max_per_category])

    # cap totale, mantenendo ordine per categoria e semplicità
    selected_rows = selected_rows[:max_total]

    # dedup label case-insensitive
    seen_names: set[str] = set()
    out: list[CatalogExercise] = []
    for r in selected_rows:
        name_key = r.exercise_label.strip().lower()
        if not name_key or name_key in seen_names:
            continue
        seen_names.add(name_key)
        out.append(to_catalog_exercise(r))
    return out


def print_summary(all_rows: list[GarminExercise], unique_rows: list[GarminExercise], subset: list[CatalogExercise]) -> None:
    print(f"Righe CSV: {len(all_rows)}")
    print(f"Uniche per exercise_key: {len(unique_rows)}")

    cat_count = Counter(ex.category_key for ex in subset)
    zone_count = Counter(ex.body_zone for ex in subset)

    print(f"Selezionati per import: {len(subset)}")
    print("Top categorie selezionate:")
    for cat, n in cat_count.most_common(12):
        print(f"  - {cat}: {n}")

    print("Distribuzione body_zone:")
    for z, n in zone_count.most_common():
        print(f"  - {z}: {n}")

    print("Esempi:")
    for ex in subset[:12]:
        print(f"  - {ex.name} ({ex.body_zone})")


def apply_import(subset: list[CatalogExercise], sport_type: str) -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlalchemy_url, future=True)
    schema = settings.db_schema

    upsert = text(
        f"""
        INSERT INTO {schema}.exercise_catalog (sport_type, name, body_zone, active, created_at)
        VALUES (:sport_type, :name, :body_zone, TRUE, NOW())
        ON CONFLICT (sport_type, name)
        DO UPDATE SET
            body_zone = EXCLUDED.body_zone,
            active = TRUE
        """
    )

    with engine.begin() as conn:
        for ex in subset:
            conn.execute(
                upsert,
                {
                    "sport_type": sport_type,
                    "name": ex.name,
                    "body_zone": ex.body_zone,
                },
            )

    print(f"Import completato: {len(subset)} esercizi su sport_type='{sport_type}'")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Import curato esercizi Garmin nel catalogo MyFit.")
    p.add_argument("--csv", required=True, help="Path CSV Garmin")
    p.add_argument("--sport-type", default="gym", help="sport_type target (default: gym)")
    p.add_argument("--max-total", type=int, default=350, help="Numero massimo esercizi da importare")
    p.add_argument("--max-per-category", type=int, default=20, help="Cap per categoria")
    p.add_argument(
        "--profile",
        choices=["balanced", "gym_essential"],
        default="gym_essential",
        help="Profilo selezione esercizi",
    )
    p.add_argument("--apply", action="store_true", help="Esegue import su DB (default: dry-run)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).expanduser()
    if not csv_path.exists():
        raise SystemExit(f"File non trovato: {csv_path}")

    all_rows = read_rows(csv_path)
    unique_rows = dedupe_by_exercise_key(all_rows)
    if args.profile == "gym_essential":
        subset = select_gym_essential(unique_rows, max_total=args.max_total, max_per_category=args.max_per_category)
    else:
        subset = select_subset(unique_rows, max_total=args.max_total, max_per_category=args.max_per_category)

    print_summary(all_rows, unique_rows, subset)

    if args.apply:
        apply_import(subset, sport_type=args.sport_type)
    else:
        print("Dry-run completato. Usa --apply per scrivere su DB.")


if __name__ == "__main__":
    main()
