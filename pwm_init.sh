#!/usr/bin/env bash

DIRS=(
  "/sys/class/pwm/pwmchip0/"
  "/sys/class/pwm/pwmchip0/pwm0/"
  "/sys/class/pwm/pwmchip0/pwm1/"
)

for dir in ${DIRS[@]}; do
  if [[ -d ${dir} ]]; then
    find ${dir} -maxdepth 1 -type f -exec chown pwm: {} \;
  fi
done
