import time
import lgpio
import DHT

chip = lgpio.gpiochip_open(0)
sensor = None

try:
    sensor = DHT.sensor(chip, 4, model=DHT.DHT11)

    for attempt in range(1, 6):
        timestamp, gpio, status, temperature, humidity = sensor.read()

        if status == DHT.DHT_GOOD:
            print(
                f"Messung {attempt}: "
                f"{temperature:.1f} °C, "
                f"{humidity:.1f} % RH"
            )
        else:
            print(f"Messung {attempt}: Fehlerstatus {status}")

        time.sleep(3)

finally:
    if sensor is not None:
        sensor.cancel()
    lgpio.gpiochip_close(chip)
