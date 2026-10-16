# Sensorlab – Raumklima-Monitoring

## Projektziel

Kontinuierliche Dokumentation von Raumtemperatur und relativer
Luftfeuchtigkeit im Zusammenhang mit einem gemeldeten Feuchtigkeitsschaden.

Das Projekt dient der nachvollziehbaren Erfassung zeitlicher Veränderungen
des Raumklimas. Die Messwerte stellen keinen unmittelbaren Nachweis für
Bauteilfeuchtigkeit oder mikrobiellen Befall dar.

## Messhardware

- Raspberry Pi 3 Model B Rev 1.2
- Debian GNU/Linux 13 (Trixie)
- DHT11 Temperatur- und Feuchtesensor
- Versorgung: 3,3 V
- Datenleitung: BCM GPIO4
- Gemeinsame Masse (GND)

## Messsoftware

- Python 3.13
- lgpio
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

Tabelle: measurements

Spalten:
- id
- timestamp: ISO-8601 mit Zeitzonenoffset
- sensor
- temperature_c: Temperatur in Grad Celsius
- humidity_pct: relative Luftfeuchtigkeit in Prozent
- status: 0 bedeutet erfolgreiche Sensorauslesung

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

## Rechtlicher Kontext

Die Aufzeichnungen dienen der Dokumentation von
Raumklimabedingungen. Aussagen über Ursachen eines
Gebäudefeuchteschadens bedürfen zusätzlicher Untersuchungen.
