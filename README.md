# Sensorlab – Raumklima- und Balkontürmonitoring

## Projektziel

Kontinuierliche Dokumentation von Raumtemperatur und relativer
Luftfeuchtigkeit im Zusammenhang mit einem gemeldeten Feuchtigkeitsschaden.

Das Projekt dient der nachvollziehbaren Erfassung zeitlicher Veränderungen
des Raumklimas sowie der Öffnungs- und Schließzustände der Balkontür. Die Messwerte stellen keinen unmittelbaren Nachweis für
Bauteilfeuchtigkeit oder mikrobiellen Befall dar.

## Messhardware

- Raspberry Pi 3 Model B Rev 1.2
- DHT11 Temperatur- und Feuchtesensor
- HC-SR04 Ultraschall-Abstandssensor für die Balkontür
- Versorgung: 3,3 V
- Datenleitung: BCM GPIO4

## Messsoftware

- Debian GNU/Linux 13 (Trixie)

- Python 3.13
- lgpio für den DHT11
- libgpiod 2.2.0 für den HC-SR04
- Angepasster DHT-Referenztreiber
- SQLite
- systemd-Service und systemd-Timer

## Messintervall

Alle drei Stunden:

00:00, 03:00, 06:00, 09:00,
12:00, 15:00, 18:00 und 21:00 Uhr.

Zusätzliche manuelle Messungen sind möglich.

## Datenspeicherung

SQLite-Datenbank: data/sensors.db

Tabellen:
- measurements: Raumklimamessungen
- door_events: bestätigte Balkontür-Zustandswechsel

Spalten:
- id
- timestamp: ISO-8601 mit Zeitzonenoffset
- sensor
- temperature_c: Temperatur in Grad Celsius
- humidity_pct: relative Luftfeuchtigkeit in Prozent
- absolute_humidity_g_m3: berechnete absolute Luftfeuchtigkeit in g/m³
- status: 0 bedeutet erfolgreiche Sensorauslesung

Die absolute Luftfeuchtigkeit wird aus Temperatur und relativer
Luftfeuchtigkeit mithilfe der Magnus-Formel berechnet.
Der verwendete Sättigungsdampfdruck lautet:

    e_s(T) = 6.112 * exp(17.62 * T / (243.12 + T))

Die absolute Luftfeuchtigkeit ergibt sich aus:

    rho_v = 216.7 * e_s(T) * (RH / 100) / (T + 273.15)

T wird in °C, RH in Prozent und rho_v in g/m³ angegeben.
Der berechnete Wert ist kein unabhängiger Sensormesswert.
Die Unsicherheit der DHT11-Messungen überträgt sich auf das Ergebnis.

Bestehende Datensätze werden beim nächsten Logger-Lauf automatisch
ergänzt. Das Messintervall bleibt unverändert bei drei Stunden.

Messdaten werden nicht im öffentlichen Git-Repository veröffentlicht.

## Einschränkungen

Der DHT11 ist kein geeichtes Messgerät.

Die spezifizierte Genauigkeit älterer DHT11-Varianten liegt
typischerweise bei etwa ±2 °C und ±5 Prozentpunkten
relativer Luftfeuchtigkeit.

Der verwendete Referenztreiber wurde angepasst, da das
angeschlossene Sensorexemplar nicht-null Nachkommabytes
im DHT11-Datenformat überträgt.

Die Genauigkeit der Messwerte wurde bislang nicht durch
eine unabhängige Referenzmessung überprüft.

## Balkontürüberwachung

Der HC-SR04 misst kontinuierlich den Abstand zu reflektierenden
Oberflächen im Bereich der Balkontür.

### GPIO-Belegung

- TRIG: BCM GPIO23, physischer Pin 16
- ECHO: BCM GPIO24, physischer Pin 18
- VCC: 5 V
- GND: gemeinsame Masse

Das 5-V-ECHO-Signal wird über einen Widerstands-Spannungsteiler
auf einen für den Raspberry Pi geeigneten Logikpegel reduziert.
Ein direkter Anschluss von ECHO an GPIO24 ist nicht zulässig.

### Kalibrierung

Referenzwerte am installierten Standort:

- Balkontür offen: ca. 28,9 cm
- Balkontür geschlossen: ca. 107 cm

Schwellwerte:

- Abstand < 50 cm: OPEN
- Abstand > 80 cm: CLOSED
- Zwischen 50 und 80 cm: unklarer Zustand

### Zustandsbestätigung

Der Logger misst ungefähr alle 0,5 Sekunden.

Ein Zustandswechsel wird nur bestätigt, wenn der neue Zustand
ununterbrochen länger als 30 Sekunden erkannt wird:

    delta_t > 30.0 s

Die Zeitmessung erfolgt mit time.monotonic().

Bei ungültigem Echo, unklarem Abstand oder Rückwechsel wird
die laufende Bestätigung abgebrochen.

Beim Programmstart wird der aktuelle Zustand zunächst neu
bestimmt. Die Initialisierung erzeugt keinen Türwechsel-Eintrag.

### Speicherung

Bestätigte Zustandsänderungen werden in der SQLite-Tabelle
door_events gespeichert.

Spalten:

- id
- sensor
- state: OPEN oder CLOSED
- detected_at: Beginn der Zustandserkennung
- confirmed_at: Zeitpunkt der Bestätigung
- distance_cm: Entfernung bei Bestätigung

Es werden ausschließlich bestätigte Zustandswechsel gespeichert,
keine kontinuierlichen Rohmessungen des HC-SR04.

### Dauerbetrieb

Der Türlogger läuft unabhängig vom DHT11-Timer als systemd-Dienst:

    sensorlab-door.service

Service-Vorlage:

    systemd/sensorlab-door.service

Installation:

    sudo cp systemd/sensorlab-door.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now sensorlab-door.service

Status:

    systemctl status sensorlab-door.service

Protokoll:

    journalctl -u sensorlab-door.service -f

Datenbankabfrage:

    sqlite3 -header -column data/sensors.db       'SELECT * FROM door_events ORDER BY id DESC LIMIT 20;'

### Einschränkungen

Der HC-SR04 erkennt Abstände, keine Objektidentitäten.
Eine länger als 30 Sekunden anhaltende Verdeckung kann einen
Türzustandswechsel vortäuschen.

Während eines Ausfalls können keine Türbewegungen erfasst werden.
Nach einem Neustart wird der Anfangszustand erneut bestimmt.

Die Langzeitzuverlässigkeit ist noch zu untersuchen.

## Rechtlicher Kontext

Die Aufzeichnungen dienen der Dokumentation von
Raumklimabedingungen. Aussagen über Ursachen eines
Gebäudefeuchteschadens bedürfen zusätzlicher Untersuchungen.
