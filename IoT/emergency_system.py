from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple, Union

CURRENT_DIR = Path(__file__).resolve().parent
UTILITES_DIR = CURRENT_DIR / "utilites"
if str(UTILITES_DIR) not in sys.path:
    sys.path.insert(0, str(UTILITES_DIR))

from intrusion_detection import (  # type: ignore[import-not-found]
    ROOM_TYPE_LIVING_ROOM,
    detect_intrusion,
)


PacketLike = Union[Sequence[object], Mapping[str, object]]
FLOOD_SENSOR_CODE = 300
FIRE_SENSOR_CODE = 100
LEAK_SENSOR_CODE = 200
ROOM_ID_START = 1000

FIRE_SENSOR_TYPES = {
    "fire",
    "smoke",
    "temperature",
    "temp",
    "co2",
    "tvoc",
    "eco2",
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
}
LEAK_SENSOR_TYPES = {
    "leak",
    "water_leak",
    "pipe_pressure",
    "flow",
    "flow_rate",
    "press_pipe_bar",
    "flow_rate_lps",
    "temp_pipe_c",
}
FLOOD_SENSOR_TYPES = {
    "flood",
    "water_level",
    "waterlevel",
    "rain",
    "drain",
}


@dataclass(frozen=True)
class SensorPacket:
    sensor_type: Union[int, str]
    sensor_id: int
    room: Union[int, str]
    reading: float


def _normalize_packets(raw_packets: Iterable[PacketLike]) -> List[SensorPacket]:
    packets: List[SensorPacket] = []
    for item in raw_packets:
        if isinstance(item, Mapping):
            required = ("sensor_type", "sensor_id", "room", "reading")
            missing = [k for k in required if k not in item]
            if missing:
                raise ValueError(f"Missing required fields: {missing}")

            sensor_type = item["sensor_type"]
            sensor_id = int(item["sensor_id"])
            room = item["room"]
            reading = float(item["reading"])
        else:
            if len(item) != 4:
                raise ValueError("Each sensor vector must contain exactly 4 values.")
            sensor_type, sensor_id, room, reading = item
            sensor_id = int(sensor_id)
            reading = float(reading)

        if isinstance(room, str) and room.isdigit():
            room = int(room)

        packets.append(
            SensorPacket(
                sensor_type=sensor_type,
                sensor_id=sensor_id,
                room=room,
                reading=reading,
            )
        )
    return packets


def _sensor_key(sensor_type: Union[int, str]) -> str:
    return str(sensor_type).strip().lower()


def detect_flood_threshold(packets: List[SensorPacket], threshold: float = 0.9) -> int:
    readings = [
        p.reading
        for p in packets
        if _sensor_key(p.sensor_type) in FLOOD_SENSOR_TYPES or p.sensor_type == FLOOD_SENSOR_CODE
    ]
    if not readings:
        return 0

    max_reading = max(readings)
    return int(max_reading >= threshold)


def detect_fire(packets: List[SensorPacket], threshold: float = 0.7) -> int:
    readings = [
        p.reading
        for p in packets
        if _sensor_key(p.sensor_type) in FIRE_SENSOR_TYPES or p.sensor_type == FIRE_SENSOR_CODE
    ]
    if not readings:
        return 0
    return int(max(readings) >= threshold)


def detect_water_leak(packets: List[SensorPacket], threshold: float = 0.7) -> int:
    readings = [
        p.reading
        for p in packets
        if _sensor_key(p.sensor_type) in LEAK_SENSOR_TYPES or p.sensor_type == LEAK_SENSOR_CODE
    ]
    if not readings:
        return 0
    return int(max(readings) >= threshold)


def detect_intrusion_alarm(packets: List[SensorPacket]) -> int:
    intrusion_type_map = {
        "ir_motion": 0,
        "door_break": 1,
        "window_open": 2,
        "0": 0,
        "1": 1,
        "2": 2,
    }

    room_map: Dict[str, int] = {}
    next_room_id = ROOM_ID_START
    vectors: List[Tuple[int, int, int, int]] = []

    for p in packets:
        st = _sensor_key(p.sensor_type)
        if st not in intrusion_type_map and p.sensor_type not in (0, 1, 2):
            continue
        if p.reading <= 0:
            continue

        if isinstance(p.room, int):
            room_id = p.room
        else:
            if p.room not in room_map:
                room_map[p.room] = next_room_id
                next_room_id += 1
            room_id = room_map[p.room]

        sensor_type = int(p.sensor_type) if p.sensor_type in (0, 1, 2) else intrusion_type_map[st]
        vectors.append((sensor_type, p.sensor_id, room_id, ROOM_TYPE_LIVING_ROOM))

    return int(detect_intrusion(vectors, strict=False))


def process_sensor_batch(raw_packets: Iterable[PacketLike]) -> List[int]:
    packets = _normalize_packets(raw_packets)

    with ThreadPoolExecutor(max_workers=4) as pool:
        future_map = {
            "flood": pool.submit(detect_flood_threshold, packets),
            "fire": pool.submit(detect_fire, packets),
            "leak": pool.submit(detect_water_leak, packets),
            "intrusion": pool.submit(detect_intrusion_alarm, packets),
        }

        return [
            future_map["flood"].result(),
            future_map["fire"].result(),
            future_map["leak"].result(),
            future_map["intrusion"].result(),
        ]


def main() -> None:
    data = json.load(sys.stdin)
    result = process_sensor_batch(data)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
