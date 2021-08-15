#!/usr/bin/env python3

import os.path
import time
import unittest

# Configuration
THERMAL_ZONE = 0
PWM_CHIP = 0
PWM_CHANNEL = 0
MIN_TEMPERATURE = 40
MAX_TEMPERATURE = 55
MIN_SPEED = 30
MAX_SPEED = 100


def get_temperature() -> float:
    """Reads the temperature."""
    with open("/sys/class/thermal/thermal_zone%d/temp" % THERMAL_ZONE) as f:
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

    def __init__(self, min_temperature: float, max_temperature: float, min_speed: float, max_speed: float) -> None:
        assert max_temperature > min_temperature
        assert max_speed > min_speed
        self._min_temperature = min_temperature
        self._max_temperature = max_temperature
        self._min_speed = min_speed
        self._max_speed = max_speed
        self._ratio = (max_speed - min_speed) / (max_temperature - min_temperature)

    def get_speed(self, temperature: float) -> float:
        """Converts a temperature to a fan speed."""
        if temperature < self._min_temperature:
            return self._min_speed
        if temperature > self._max_temperature:
            return self._max_speed
        return self._min_speed + self._ratio * (temperature - self._min_temperature)


class TestController(unittest.TestCase):
    """Controller unit tests."""

    def test_get_speed(self) -> None:
        controller = Controller(min_temperature=40, max_temperature=60, min_speed=50, max_speed=100)
        self.assertEqual(controller.get_speed(temperature=30), 50)
        self.assertEqual(controller.get_speed(temperature=40), 50)
        self.assertEqual(controller.get_speed(temperature=50), 75)
        self.assertEqual(controller.get_speed(temperature=60), 100)
        self.assertEqual(controller.get_speed(temperature=70), 100)


if __name__ == "__main__":
    controller = Controller(MIN_TEMPERATURE, MAX_TEMPERATURE, MIN_SPEED, MAX_SPEED)
    pwm = PWM(chip=PWM_CHIP, channel=PWM_CHANNEL, period=40000)
    pwm.init()
    while True:
        temperature = get_temperature()
        percent = controller.get_speed(temperature)
        pwm.update(percent)
        time.sleep(1)
