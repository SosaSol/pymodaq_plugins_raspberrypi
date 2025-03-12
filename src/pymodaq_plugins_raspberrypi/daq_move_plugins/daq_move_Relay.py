from typing import Union, List, Dict

import RPi.GPIO as GPIO
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, DataActuator
)
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter


class DAQ_Move_Relay(DAQ_Move_base):
    """PyMoDAQ plugin to control a relay using GPIO on a Raspberry Pi.

    This plugin allows switching a relay ON/OFF through a user-selectable GPIO pin.
    """

    is_multiaxes = False
    _axis_names: Union[List[str], Dict[str, int]] = ['relay']
    _controller_units: Union[str, List[str]] = ''
    _epsilon: Union[float, List[float]] = 0
    data_actuator_type = DataActuatorType.DataActuator  # Controls an ON/OFF device

    params = [
        {'title': 'Relay Pin', 'name': 'relay_pin', 'type': 'int', 'value': 26, 'min': 0, 'max': 40},
        {'title': 'Relay State', 'name': 'relay_state', 'type': 'list', 'limits': ['OFF', 'ON'], 'value': 'OFF'}
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        """Initialize attributes"""
        self.controller = None  # Not needed for GPIO, but kept for consistency
        self.relay_pin = self.settings['relay_pin']  # Get initial relay pin

    def ini_stage(self, controller=None):
        """Initialize GPIO pin"""
        self.ini_stage_init(slave_controller=controller)

        if self.is_master:
            GPIO.setmode(GPIO.BCM)
            self.setup_gpio(self.relay_pin)

        info = "Relay control initialized"
        initialized = True
        return info, initialized

    def setup_gpio(self, pin):
        """Setup GPIO pin for relay control"""
        GPIO.cleanup()  # Reset all GPIOs to avoid conflicts
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)  # Default to OFF
        self.relay_pin = pin  # Update active pin

    def get_actuator_value(self):
        """Get the current relay state (0 = OFF, 1 = ON)."""
        state = GPIO.input(self.relay_pin)
        return DataActuator(data=int(not state))  # Relay is ACTIVE LOW (0 = ON, 1 = OFF)

    def move_abs(self, value: DataActuator):
        """Switch relay ON/OFF based on the provided value (1 = ON, 0 = OFF)."""

        value = int(value.value())  # Ensure value is an integer (0 or 1)
        GPIO.output(self.relay_pin, GPIO.LOW if value == 1 else GPIO.HIGH)

        state_str = "ON" if value == 1 else "OFF"
        self.settings.child('relay_state').setValue(state_str)  # Update UI

        self.emit_status(ThreadCommand('Update_Status', [f'Relay turned {state_str}']))

    def move_home(self):
        """Set relay to OFF (safe home position)."""
        GPIO.output(self.relay_pin, GPIO.HIGH)  # Ensure relay is OFF
        self.settings.child('relay_state').setValue('OFF')  # Update UI
        self.emit_status(ThreadCommand('Update_Status', ['Relay moved to HOME (OFF)']))

    def stop_motion(self):
        """Turn relay OFF (safe stop)."""
        self.move_home()

    def commit_settings(self, param: Parameter):
        """Handle setting changes dynamically."""
        if param.name() == 'relay_pin':
            new_pin = param.value()
            if new_pin != self.relay_pin:
                self.setup_gpio(new_pin)  # Update GPIO configuration
                self.emit_status(ThreadCommand('Update_Status', [f'Relay pin changed to {new_pin}']))

    def close(self):
        """Clean up GPIO when the plugin is closed."""
        GPIO.cleanup()
        self.emit_status(ThreadCommand('Update_Status', ['GPIO cleanup done']))


if __name__ == '__main__':
    main(__file__)
