# Fan control

This project controls a fan speed according to a temperature sensor. It relies on pwmchip sysfs to control the fan speed, and on thermal sysfs to read the temperature.

Tested on a Raspberry Pi 4 running Ubuntu Groovy.

## Configuration

### Enable PWM

The Raspberry Pi hardware PWM is not enabled by default.

Edit `/boot/firmware/config.txt`.

Add the following to enable PWM.

    dtoverlay=pwm-2chan

Reboot.

We can now access `/sys/class/pwm/pwmchip0`.

- `/sys/class/pwm/pwmchip0/pwm0` controls pin 18
- `/sys/class/pwm/pwmchip0/pwm1` controls pin 19

If using `pwm` instead of `pwm-2chan` we can still enable pwm1 but it does not control pin 19.

### Permissions

Create the pwm user.

    sudo groupadd -r pwm
    sudo useradd -r -M pwm -g pwm
    sudo usermod -L pwm

Copy `pwm_init.sh` to `/usr/local/bin/pwm_init.sh`.

Create `/etc/udev/rules.d/99-pwm.rules`.

    SUBSYSTEM=="pwm", RUN+="/usr/local/bin/pwm_init.sh"

Reboot.

## Installation

Copy `fan_control.py` to `/usr/local/bin/fan_control.py`.

Configure the thermal zone, the hardware PWM, and the fan curve directly in `/usr/local/bin/fan_control.py`.

The fan curve is
- constant for temperatures lower than MIN_TEMP
- constant for temperatures higher than MAX_TEMP
- linear for temperatures between MIN_TEMP and MAX_TEMP

Copy `fan-control.service` to `/etc/systemd/system/fan-control.service`.

Configure systemd.

    sudo systemctl daemon-reload
    sudo systemctl start fan-control
    sudo systemctl enable fan-control

## Hacking

Setup a virtualenv. This is only required for the dev tools, not to run the service.

    virtualenv -p python3 venv
    source venv/bin/activate
    pip3 install -r requirements.txt

Run the static analysis.

    ./test.sh

Run `fan_control.py` on the target outside of the systemd service.

    sudo su pwm --session-command "./fan_control.py"
