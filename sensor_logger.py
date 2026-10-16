#!/usr/bin/env python3

import sqlite3
import time
from datetime import datetime
from pathlib import Path

import DHT
import lgpio

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "sensors.db"


def main():
    (BASE / "data").mkdir(exist_ok=True)

    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                sensor TEXT NOT NULL,
                temperature_c REAL,
                humidity_pct REAL,
                status INTEGER NOT NULL
            )
        """)

    chip = lgpio.gpiochip_open(0)
    sensor = None

    try:
        sensor = DHT.sensor(chip, 4, model=DHT.DHT11)

        for attempt in range(5):
            _, _, status, temperature, humidity = sensor.read()

            if status == DHT.DHT_GOOD:
                break

            if attempt < 4:
                time.sleep(3)

    finally:
        if sensor is not None:
            sensor.cancel()
        lgpio.gpiochip_close(chip)

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

    with sqlite3.connect(DB) as conn:
        conn.execute("""
            INSERT INTO measurements
            (timestamp, sensor, temperature_c, humidity_pct, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            timestamp,
            "DHT11",
            temperature if status == DHT.DHT_GOOD else None,
            humidity if status == DHT.DHT_GOOD else None,
            status
        ))

    if status == DHT.DHT_GOOD:
        print(f"{timestamp} | {temperature:.1f} °C | {humidity:.1f} % RH")
    else:
        print(f"{timestamp} | DHT11-Messfehler: Status {status}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
