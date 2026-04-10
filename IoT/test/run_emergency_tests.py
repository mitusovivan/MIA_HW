from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List

from generate_sensor_batch import dataframe_row_to_batch, generate_batch

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from emergency_system import process_sensor_batch, reset_state  # type: ignore[import-not-found]

UNIFIED_DATASET_PATH = BASE_DIR / "test" / "unified_test_clean.csv"
SAFE_DATASET_PATH = BASE_DIR / "test" / "safe_unified_test_clean.csv"


def run_emergency_system(batch: List[List[object]]) -> List[int]:
    return process_sensor_batch(batch)


def dataset_path(dataset: str) -> Path:
    if dataset == "full":
        return UNIFIED_DATASET_PATH
    if dataset == "safe":
        return SAFE_DATASET_PATH
    raise ValueError("dataset must be safe or full")


def evaluate_dataset(dataset: str, limit: int) -> None:
    reset_state()
    path = dataset_path(dataset)
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        raise ValueError("Dataset is empty")
    if "smoke_label" not in rows[0]:
        raise ValueError("Dataset must contain smoke_label")
    if limit > 0:
        rows = rows[:limit]

    fire_hits = 0
    for row in rows:
        batch = dataframe_row_to_batch(row)
        batch.extend(
            [
                ["door_break", 1, 101, 0.0],
                ["ir_motion", 2, 101, 0.0],
            ]
        )
        result = run_emergency_system(batch)
        fire_hits += int(result[1] == int(float(row["smoke_label"])))

    total = len(rows)
    print(f"Dataset: {dataset}, rows: {total}")
    print(f"Fire label match: {fire_hits}/{total} ({fire_hits / total:.3f})")
    print("Затопление/Утечка газа/Проникновение: отсутствуют ground-truth метки в датасете, строгая оценка пропущена.")


def evaluate_generator() -> None:
    reset_state()
    alarm_batch = generate_batch(target_alarm=1, seed=123456, source="synthetic")
    normal_batch = generate_batch(target_alarm=0, seed=123457, source="synthetic")
    normal_result = run_emergency_system(normal_batch)
    alarm_result = run_emergency_system(alarm_batch)
    print(f"Synthetic normal batch result: {normal_result}")
    print(f"Synthetic alarm batch result: {alarm_result}")


def evaluate_intrusion_apartment() -> None:
    reset_state()
    base_batch = [
        ["ir_motion", 11, "living_room", 0.0],
        ["ir_motion", 12, "living_room", 0.0],
        ["ir_motion", 21, "bedroom", 0.0],
        ["ir_motion", 22, "bedroom", 0.0],
        ["ir_motion", 31, "corridor", 0.0],
        ["ir_motion", 32, "corridor", 0.0],
        ["ir_motion", 41, "kitchen", 0.0],
        ["ir_motion", 42, "kitchen", 0.0],
        ["door_break", 1, "corridor", 0.0],  # входная дверь
    ]
    intrusion_batch = [
        ["ir_motion", 11, "living_room", 0.0],
        ["ir_motion", 12, "living_room", 0.0],
        ["ir_motion", 21, "bedroom", 0.0],
        ["ir_motion", 22, "bedroom", 0.0],
        ["ir_motion", 31, "corridor", 1.0],
        ["ir_motion", 32, "corridor", 1.0],
        ["ir_motion", 41, "kitchen", 0.0],
        ["ir_motion", 42, "kitchen", 0.0],
        ["door_break", 1, "corridor", 1.0],  # взлом входной двери
    ]

    base_result = run_emergency_system(base_batch)
    intrusion_result = run_emergency_system(intrusion_batch)
    if base_result[3] != 0:
        raise RuntimeError(f"Expected no intrusion for base apartment scenario, got: {base_result}")
    if intrusion_result[3] != 1:
        raise RuntimeError(
            f"Expected intrusion alarm for apartment intrusion scenario, got: {intrusion_result}"
        )
    print(f"Apartment intrusion baseline result: {base_result}")
    print(f"Apartment intrusion alarm result: {intrusion_result}")


def evaluate_gas_leak_scenario() -> None:
    reset_state()
    baseline_batch = [
        ["gas_leak", 500, 101, 0.05],
        ["tvoc_ppb", 501, 101, 40.0],
        ["eco2_ppm", 502, 101, 550.0],
        ["raw_h2", 503, 101, 12700.0],
        ["raw_ethanol", 504, 101, 20600.0],
        ["door_break", 1, 101, 0.0],
        ["ir_motion", 2, 101, 0.0],
    ]
    gas_leak_batch = [
        ["gas_leak", 500, 101, 0.95],
        ["tvoc_ppb", 501, 101, 1200.0],
        ["eco2_ppm", 502, 101, 2600.0],
        ["raw_h2", 503, 101, 22000.0],
        ["raw_ethanol", 504, 101, 28000.0],
        ["door_break", 1, 101, 0.0],
        ["ir_motion", 2, 101, 0.0],
    ]

    baseline_result = run_emergency_system(baseline_batch)
    leak_result = run_emergency_system(gas_leak_batch)
    if baseline_result[2] != 0:
        raise RuntimeError(f"Expected no gas leak alarm for baseline gas scenario, got: {baseline_result}")
    if leak_result[2] != 1:
        raise RuntimeError(f"Expected gas leak alarm for gas leak scenario, got: {leak_result}")
    print(f"Gas leak baseline result: {baseline_result}")
    print(f"Gas leak alarm result: {leak_result}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Runs emergency_system against dataset-derived and generated batches."
    )
    parser.add_argument("--dataset", choices=["safe", "full"], default="safe")
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Rows to test from dataset (default: 200, 0 means all rows)",
    )
    parser.add_argument("--skip-dataset", action="store_true")
    parser.add_argument("--skip-generator", action="store_true")
    parser.add_argument("--skip-intrusion", action="store_true")
    parser.add_argument("--skip-gas-leak", action="store_true")
    args = parser.parse_args()

    if not args.skip_generator:
        evaluate_generator()
    if not args.skip_intrusion:
        evaluate_intrusion_apartment()
    if not args.skip_gas_leak:
        evaluate_gas_leak_scenario()
    if not args.skip_dataset:
        evaluate_dataset(args.dataset, args.limit)


if __name__ == "__main__":
    main()
