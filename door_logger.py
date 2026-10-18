#!/usr/bin/env python3

import signal
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import gpiod
from gpiod.line import Direction, Value, Edge
from gpiod.edge_event import EdgeEvent


BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "sensors.db"

CHIP = "/dev/gpiochip0"
TRIG = 23
ECHO = 24

SAMPLE_INTERVAL = 0.5
CONFIRM_SECONDS = 30.0

OPEN_THRESHOLD_CM = 50.0
CLOSED_THRESHOLD_CM = 80.0
SOUND_SPEED_CM_S = 34300.0


def timestamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def classify(distance):
    if distance is None:
        return None
    if distance < OPEN_THRESHOLD_CM:
        return "OPEN"
    if distance > CLOSED_THRESHOLD_CM:
        return "CLOSED"
    return None


def measure_distance(request):
    # Bewährte Messroutine aus ultraschall_raw.py
    request.set_value(TRIG, Value.INACTIVE)
    time.sleep(0.01)

    # Alte Flanken entfernen
    if request.wait_edge_events(timeout=0):
        request.read_edge_events()

    request.set_value(TRIG, Value.ACTIVE)
    time.sleep(0.00002)
    request.set_value(TRIG, Value.INACTIVE)

    deadline = time.monotonic() + 0.04
    events = []

    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if request.wait_edge_events(timeout=remaining):
            events.extend(request.read_edge_events())

    # Nur ein vollständiges, eindeutiges Echo akzeptieren.
    if len(events) != 2:
        return None

    rising, falling = events

    if rising.event_type != EdgeEvent.Type.RISING_EDGE:
        return None
    if falling.event_type != EdgeEvent.Type.FALLING_EDGE:
        return None

    duration = (falling.timestamp_ns - rising.timestamp_ns) / 1e9
    distance = duration * SOUND_SPEED_CM_S / 2

    if not 2.0 <= distance <= 400.0:
        return None

    return distance


def initialize_database():
    DB.parent.mkdir(exist_ok=True)

    with sqlite3.connect(DB, timeout=10) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS door_events (
                id INTEGER PRIMARY KEY,
                sensor TEXT NOT NULL DEFAULT 'HC-SR04',
                state TEXT NOT NULL
                    CHECK (state IN ('OPEN', 'CLOSED')),
                detected_at TEXT NOT NULL,
                confirmed_at TEXT NOT NULL,
                distance_cm REAL NOT NULL
            )
        """)


def log_event(state, detected_at, distance):
    confirmed_at = timestamp()

    with sqlite3.connect(DB, timeout=10) as conn:
        conn.execute("""
            INSERT INTO door_events
                (sensor, state, detected_at, confirmed_at, distance_cm)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "HC-SR04",
            state,
            detected_at,
            confirmed_at,
            distance,
        ))

    print(
        f"{confirmed_at} | CONFIRMED {state} | "
        f"{distance:.1f} cm | detected_at={detected_at}",
        flush=True,
    )


def stop_handler(signum, frame):
    raise SystemExit(0)


def main():
    initialize_database()

    settings = {
        TRIG: gpiod.LineSettings(
            direction=Direction.OUTPUT,
            output_value=Value.INACTIVE,
        ),
        ECHO: gpiod.LineSettings(
            direction=Direction.INPUT,
            edge_detection=Edge.BOTH,
        ),
    }

    confirmed_state = None
    candidate_state = None
    candidate_since = None
    candidate_detected_at = None

    print(
        f"{timestamp()} | Door logger started | "
        f"confirmation > {CONFIRM_SECONDS:.0f} s",
        flush=True,
    )

    with gpiod.request_lines(
        CHIP,
        consumer="sensorlab-door",
        config=settings,
    ) as request:

        while True:
            distance = measure_distance(request)
            observed_state = classify(distance)
            now = time.monotonic()

            # Messfehler oder unklarer Abstand:
            # keine Bestätigung möglich.
            if observed_state is None:
                if candidate_state is not None:
                    print(
                        f"{timestamp()} | Candidate cancelled "
                        f"(invalid/intermediate measurement)",
                        flush=True,
                    )
                candidate_state = None
                candidate_since = None
                candidate_detected_at = None

            # Bereits bestätigter Zustand:
            # ein eventuell laufender Wechsel ist hinfällig.
            elif observed_state == confirmed_state:
                if candidate_state is not None:
                    print(
                        f"{timestamp()} | Candidate cancelled "
                        f"(returned to {confirmed_state})",
                        flush=True,
                    )
                candidate_state = None
                candidate_since = None
                candidate_detected_at = None

            # Ein neuer Zustandskandidat beginnt.
            elif observed_state != candidate_state:
                candidate_state = observed_state
                candidate_since = now
                candidate_detected_at = timestamp()

                print(
                    f"{candidate_detected_at} | Candidate "
                    f"{candidate_state} | {distance:.1f} cm",
                    flush=True,
                )

            # Der Kandidat besteht weiterhin.
            elif now - candidate_since > CONFIRM_SECONDS:

                if confirmed_state is None:
                    # Startkalibrierung: kein Türereignis
                    confirmed_state = candidate_state
                    print(
                        f"{timestamp()} | INITIAL "
                        f"{confirmed_state} | {distance:.1f} cm",
                        flush=True,
                    )
                else:
                    # Erst nach erfolgreichem DB-Schreiben
                    # wird der neue Zustand intern übernommen.
                    log_event(
                        candidate_state,
                        candidate_detected_at,
                        distance,
                    )
                    confirmed_state = candidate_state

                candidate_state = None
                candidate_since = None
                candidate_detected_at = None

            time.sleep(SAMPLE_INTERVAL)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    main()
