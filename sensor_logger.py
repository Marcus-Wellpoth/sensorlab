#!/usr/bin/env python3

import math
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import DHT
import lgpio

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "sensors.db"



def absolute_humidity_g_m3(temperature_c: float, humidity_pct: float) -> float:
    """Berechnet die absolute Luftfeuchtigkeit in g/m³."""
    saturation_pressure = 6.112 * math.exp(
        (17.62 * temperature_c) / (243.12 + temperature_c)
    )
    return (
        216.7 * saturation_pressure * (humidity_pct / 100.0)
        / (temperature_c + 273.15)
    )


def migrate_database(conn):
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(measurements)")
    }

    if "absolute_humidity_g_m3" not in columns:
        conn.execute(
            "ALTER TABLE measurements "
            "ADD COLUMN absolute_humidity_g_m3 REAL"
        )

    rows = conn.execute("""
        SELECT id, temperature_c, humidity_pct
        FROM measurements
        WHERE absolute_humidity_g_m3 IS NULL
          AND status = 0
          AND temperature_c IS NOT NULL
          AND humidity_pct IS NOT NULL
    """).fetchall()

    conn.executemany("""
        UPDATE measurements
        SET absolute_humidity_g_m3 = ?
        WHERE id = ?
    """, [
        (absolute_humidity_g_m3(t, rh), row_id)
        for row_id, t, rh in rows
    ])


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
        migrate_database(conn)

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
            (timestamp, sensor, temperature_c, humidity_pct,
             absolute_humidity_g_m3, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            "DHT11",
            temperature if status == DHT.DHT_GOOD else None,
            humidity if status == DHT.DHT_GOOD else None,
            absolute_humidity_g_m3(temperature, humidity)
            if status == DHT.DHT_GOOD else None,
            status
        ))

    if status == DHT.DHT_GOOD:
        print(f"{timestamp} | {temperature:.1f} °C | {humidity:.1f} % RH")
    else:
        print(f"{timestamp} | DHT11-Messfehler: Status {status}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
