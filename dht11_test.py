import time
import board
import adafruit_dht

sensor = adafruit_dht.DHT11(board.D4, use_pulseio=False)

try:
    for attempt in range(10):
        try:
            temperature = sensor.temperature
            humidity = sensor.humidity

            print(
                f"Temperatur: {temperature:.1f} °C | "
                f"Luftfeuchtigkeit: {humidity:.1f} %"
            )
        except RuntimeError as error:
            print(f"Messversuch {attempt + 1}: {error}")

        time.sleep(3)
finally:
    sensor.exit()
