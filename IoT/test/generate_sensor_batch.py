from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import random
import time
from typing import Dict, List, Mapping, Union

DEFAULT_ROOM_ID = 101
# SensorVector format: [sensor_type, sensor_id, room, reading]
SensorVector = List[Union[str, int, float]]
BASE_DIR = Path(__file__).resolve().parents[1]
UNIFIED_DATASET_PATH = BASE_DIR / "test" / "unified_test_clean.csv"
SAFE_DATASET_PATH = BASE_DIR / "test" / "safe_unified_test_clean.csv"

DATASET_SENSOR_COLUMNS = [
    "temp_ambient_c",
    "humidity_pct",
    "tvoc_ppb",
    "eco2_ppm",
    "raw_h2",
    "raw_ethanol",
    "press_ambient_bar",
    "pm1_0",
    "pm2_5",
    "nc0_5",
    "nc1_0",
    "nc2_5",
    "press_pipe_bar",
    "flow_rate_lps",
    "temp_pipe_c",
]


def _r(rng: random.Random, lo: float, hi: float) -> float:
    return round(rng.uniform(lo, hi), 4)


def _normalize_reading(value: float, col: str) -> float:
    scales = {
        "temp_ambient_c": 80.0,
        "humidity_pct": 100.0,
        "tvoc_ppb": 1200.0,
        "eco2_ppm": 2000.0,
        "raw_h2": 20000.0,
        "raw_ethanol": 25000.0,
        "press_ambient_bar": 2.0,
        "pm1_0": 15.0,
        "pm2_5": 20.0,
        "nc0_5": 120.0,
        "nc1_0": 20.0,
        "nc2_5": 2.0,
        "press_pipe_bar": 5.0,
        "flow_rate_lps": 250.0,
        "temp_pipe_c": 80.0,
    }
    scale = scales.get(col, 1.0)
    if scale == 0:
        return 0.0
    normalized = float(value) / scale
    return max(0.0, min(1.5, round(normalized, 4)))


def dataframe_row_to_batch(row: Mapping[str, object], room: int = DEFAULT_ROOM_ID) -> List[SensorVector]:
    batch: List[SensorVector] = []
    sensor_id = 1000
    for col in DATASET_SENSOR_COLUMNS:
        if col not in row:
            continue
        raw_value = row[col]
        if raw_value in ("", None):
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        batch.append([col, sensor_id, room, _normalize_reading(value, col)])
        sensor_id += 1
    return batch


def load_dataset_row(source: str, seed: int) -> Dict[str, str]:
    if source == "full":
        path = UNIFIED_DATASET_PATH
    elif source == "safe":
        path = SAFE_DATASET_PATH
    else:
        raise ValueError("source must be 'full' or 'safe'")

    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        raise ValueError(f"Dataset is empty: {path}")
    rng = random.Random(seed)
    row_idx = rng.randrange(len(rows))
    return rows[row_idx]


def generate_synthetic_batch(target_alarm: int, seed: int) -> List[SensorVector]:
    rng = random.Random(seed)

    if target_alarm not in (0, 1):
        raise ValueError("target_alarm must be 0 or 1")

    room = DEFAULT_ROOM_ID
    if target_alarm == 1:
        return [
            ["flood", 3001, room, _r(rng, 0.92, 1.25)],
            ["smoke", 1001, room, _r(rng, 0.72, 1.10)],
            ["leak", 2001, room, _r(rng, 0.72, 1.10)],
            ["temp_ambient_c", 1101, room, _r(rng, 0.75, 1.05)],
            ["tvoc_ppb", 1102, room, _r(rng, 0.75, 1.10)],
            ["eco2_ppm", 1103, room, _r(rng, 0.72, 1.00)],
            ["flow_rate_lps", 2101, room, _r(rng, 0.80, 1.10)],
            ["press_pipe_bar", 2102, room, _r(rng, 0.72, 1.00)],
            ["door_break", 1, room, 1.0],
            ["ir_motion", 2, room, 1.0],
        ]

    return [
        ["flood", 3001, room, _r(rng, 0.01, 0.89)],
        ["smoke", 1001, room, _r(rng, 0.01, 0.69)],
        ["leak", 2001, room, _r(rng, 0.01, 0.69)],
        ["temp_ambient_c", 1101, room, _r(rng, 0.05, 0.68)],
        ["tvoc_ppb", 1102, room, _r(rng, 0.05, 0.65)],
        ["eco2_ppm", 1103, room, _r(rng, 0.05, 0.60)],
        ["flow_rate_lps", 2101, room, _r(rng, 0.05, 0.68)],
        ["press_pipe_bar", 2102, room, _r(rng, 0.05, 0.60)],
        ["door_break", 1, room, 0.0],
        ["ir_motion", 2, room, 0.0],
    ]


def generate_batch(target_alarm: int, seed: int, source: str = "synthetic") -> List[SensorVector]:
    if source == "synthetic":
        return generate_synthetic_batch(target_alarm, seed)

    row = load_dataset_row(source, seed)
    batch = dataframe_row_to_batch(row)
    if target_alarm == 1:
        batch.extend(
            [
                ["door_break", 1, DEFAULT_ROOM_ID, 1.0],
                ["ir_motion", 2, DEFAULT_ROOM_ID, 1.0],
            ]
        )
    else:
        batch.extend(
            [
                ["door_break", 1, DEFAULT_ROOM_ID, 0.0],
                ["ir_motion", 2, DEFAULT_ROOM_ID, 0.0],
            ]
        )
    return batch


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate sensor batch: synthetic or from datasets. "
            "1 => alarm-oriented batch, 0 => normal-oriented batch."
        )
    )
    parser.add_argument("target_alarm", type=int, choices=[0, 1], help="1=alarm batch, 0=normal batch")
    parser.add_argument(
        "--source",
        choices=["synthetic", "safe", "full"],
        default="synthetic",
        help="synthetic generation or random row from safe/full unified dataset",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional fixed random seed")
    parser.add_argument("--with-meta", action="store_true", help="Print object with seed and target metadata")
    args = parser.parse_args()

    seed = args.seed if args.seed is not None else int(time.time())
    batch = generate_batch(args.target_alarm, seed, source=args.source)

    if args.with_meta:
        print(
            json.dumps(
                {
                    "seed": seed,
                    "source": args.source,
                    "target_alarm": args.target_alarm,
                    "sensor_types_count": len({item[0] for item in batch}),
                    "batch": batch,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(json.dumps(batch, ensure_ascii=False))


if __name__ == "__main__":
    main()
