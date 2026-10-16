# DHT11-Treiber – Herkunft und Anpassungen

## Ursprung

Datei: DHT.py
Autor: Joan (lgpio-Projekt)
Datum der Originalfassung: 2020-12-01
Kennzeichnung im Quellcode: Public Domain

Quelle:
https://github.com/joan2937/lg/blob/master/EXAMPLES/py_lgpio/DHT.py

## Lokale Anpassung

Der ursprüngliche Treiber erwartet beim DHT11 zwei
Nachkommabytes mit dem Wert 0.

Der verwendete Sensor übermittelt dagegen nicht-null
Nachkommabytes für die Temperatur.

Beispiel der empfangenen Rohdaten:

RAW: 59 03 18 00 3E

Interpretation:
- Relative Luftfeuchtigkeit: 62 %
- Temperatur: 24,3 °C
- Prüfsumme: korrekt

Die Funktion _validate_DHT11 wurde deshalb angepasst,
um Nachkommabytes von 0 bis 9 zu akzeptieren und
als Zehntelwerte zu interpretieren.

## Einschränkungen

Die Anpassung verbessert nicht die Messgenauigkeit
des DHT11.

Die Sensordaten wurden bislang nicht gegen ein
kalibriertes Referenzmessgerät geprüft.

Die früher beobachteten 38–39 erfassten Flanken
sollten bei einer späteren Treiberprüfung
gesondert untersucht werden.
