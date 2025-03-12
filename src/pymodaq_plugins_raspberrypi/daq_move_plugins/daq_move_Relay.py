import RPi.GPIO as GPIO
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, DataActuator
)
from pymodaq.utils.daq_utils import ThreadCommand

class RelayController:
    """Simple class to control a relay via GPIO on a Raspberry Pi."""
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_off()  # Ensure relay is OFF initially

    def turn_on(self):
        GPIO.output(self.pin, GPIO.LOW)  # Activate relay

    def turn_off(self):
        GPIO.output(self.pin, GPIO.HIGH)  # Deactivate relay

    def get_status(self):
        return GPIO.input(self.pin) == GPIO.LOW  # True if ON, False if OFF

    def cleanup(self):
        GPIO.cleanup(self.pin)


class DAQ_Move_Relay(DAQ_Move_base):
    """Plugin for controlling a relay actuator."""
    is_multiaxes = False
    _axis_names = ['Relay']
    _controller_units = 'State'
    data_actuator_type = DataActuatorType['DataActuator']

    params = [
        {"title": "GPIO Pin:", "name": "gpio_pin", "type": "int", "value": 26, "min": 0, "max": 40, "step": 1},
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names)

    def ini_stage(self, controller=None):
        """Initialize the relay controller."""
        gpio_pin = self.settings['gpio_pin']
        self.controller = RelayController(pin=gpio_pin)
        info = f"Relay initialized on GPIO pin {gpio_pin}."
        return info, True

    def move_abs(self, value: DataActuator):
        """Move the relay to an absolute state (1 = ON, 0 = OFF)."""
        if value.data > 0:
            self.controller.turn_on()
            self.emit_status(ThreadCommand("Update_Status", ["Relay turned ON."]))
        else:
            self.controller.turn_off()
            self.emit_status(ThreadCommand("Update_Status", ["Relay turned OFF."]))
        self.target_value = DataActuator(data=value.data, units=self._controller_units)

    def move_home(self):
        """Turn the relay OFF (home position)."""
        self.controller.turn_off()
        self.emit_status(ThreadCommand("Update_Status", ["Relay returned to OFF state (home)."]))
        self.target_value = DataActuator(data=0, units=self._controller_units)

    def stop_motion(self):
        """Emergency stop: Turn relay OFF."""
        self.controller.turn_off()
        self.emit_status(ThreadCommand("Update_Status", ["Emergency stop: Relay turned OFF."]))

    def get_actuator_value(self):
        """Get the current relay status (ON=1, OFF=0)."""
        status = 1 if self.controller.get_status() else 0
        return DataActuator(data=status, units=self._controller_units)

    def close(self):
        """Cleanup GPIO on exit."""
        self.controller.cleanup()
        self.emit_status(ThreadCommand("Update_Status", ["Relay controller closed."]))


if __name__ == '__main__':
    main(__file__)
