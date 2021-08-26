#!/usr/bin/env python3

import os.path
import time

# Devices
THERMAL_ZONE = 0
PWM_CHIP = 0
PWM_CHANNEL = 0

# Fan curve
MIN_TEMP = 30
MAX_TEMP = 45
MIN_SPEED = 20
MAX_SPEED = 100

# EWMA filter coefficient
ALPHA = 0.1


class Sensor:
    """Temperature sensor."""

    def __init__(self, thermal_zone: int) -> None:
        self._thermal_zone = thermal_zone

    def read_temp(self) -> float:
        """Reads the temperature."""
        with open("/sys/class/thermal/thermal_zone%d/temp" % self._thermal_zone) as f:
            return int(f.readline()) / 1000


class PWM:
    """Controls a hardware PWM channel."""

    def __init__(self, chip: int, channel: int, period: int) -> None:
        self._chip = chip
        self._chip_path = "/sys/class/pwm/pwmchip%d" % chip
        self._channel = channel
        self._channel_path = "%s/pwm%d" % (self._chip_path, channel)
        self._period = period

    def _write_chip(self, name: str, value: str) -> None:
        """Writes the PWM chip configuration to a sysfs node."""
        filename = "%s/%s" % (self._chip_path, name)
        with open(filename, "w") as f:
            f.write(value)

    def _write_channel(self, name: str, value: str) -> None:
        """Writes the PWM channel configuration to a sysfs node."""
        filename = "%s/%s" % (self._channel_path, name)
        with open(filename, "w") as f:
            f.write(value)

    def init(self) -> None:
        """Initialises the PWM channel."""
        if not os.path.isdir(self._channel_path):
            self._write_chip("export", "%d" % self._channel)
            # Wait for the udev rules to run.
            time.sleep(1)
        self._write_channel("period", "%d" % self._period)
        self._write_channel("duty_cycle", "0")
        self._write_channel("enable", "1")

    def update(self, percent: float) -> None:
        """Updates the PWM channel duty cycle."""
        duty_cycle = "%d" % (percent / 100 * self._period)
        self._write_channel("duty_cycle", duty_cycle)


class Controller:
    """Converts temperatures to fan speeds. Uses a linear saturated fan curve."""

    def __init__(self, min_temp: float, max_temp: float, min_speed: float, max_speed: float, alpha: float) -> None:
        assert max_temp > min_temp
        assert max_speed > min_speed
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._min_speed = min_speed
        self._max_speed = max_speed
        self._ratio = (max_speed - min_speed) / (max_temp - min_temp)
        self._alpha = alpha

    def get_speed(self, temp: float) -> float:
        """Converts a temperature to a fan speed."""
        if not hasattr(self, "_temp"):
            self._temp = temp
        else:
            self._temp = self._alpha * temp + (1 - self._alpha) * self._temp
        if self._temp < self._min_temp:
            return self._min_speed
        if self._temp > self._max_temp:
            return self._max_speed
        return self._min_speed + self._ratio * (self._temp - self._min_temp)


if __name__ == "__main__":
    sensor = Sensor(THERMAL_ZONE)
    controller = Controller(MIN_TEMP, MAX_TEMP, MIN_SPEED, MAX_SPEED, ALPHA)
    pwm = PWM(chip=PWM_CHIP, channel=PWM_CHANNEL, period=40000)
    pwm.init()
    while True:
        temp = sensor.read_temp()
        percent = controller.get_speed(temp)
        pwm.update(percent)
        time.sleep(1)
