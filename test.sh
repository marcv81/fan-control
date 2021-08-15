#!/usr/bin/env bash

set -euo pipefail

black --line-length=120 fan_control.py
mypy --strict fan_control.py
python3 -m unittest fan_control.py
