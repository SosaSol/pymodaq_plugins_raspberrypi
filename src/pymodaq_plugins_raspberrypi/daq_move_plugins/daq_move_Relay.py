from typing import Union, List, Dict

import RPi.GPIO as GPIO
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, DataActuator
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter


class DAQ_Move_Relay(DAQ_Move_base):
    """PyMoDAQ plugin to control a relay using GPIO on a Raspberry Pi.

    This plugin allows switching a relay ON/OFF through GPIO pin 26.
    """

    is_multiaxes = False
    _axis_names: Union[List[str], Dict[str, int]] = ['relay']
    _controller_units: Union[str, List[str]] = ''
    _epsilon: Union[float, List[float]] = 0
    data_actuator_type = DataActuatorType.DataActuator  # Controls an ON/OFF device

    # Define GPIO pin for the relay
    RELAY_PIN = 26

    params = [
        {'title': 'Relay State', 'name': 'relay_state', 'type': 'list', 'limits': ['OFF', 'ON'], 'value': 'OFF'}
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        """Initialize attributes"""
        self.controller = None  # Not needed for GPIO, but kept for consistency

    def ini_stage(self, controller=None):
        """Initialize GPIO pin"""
        self.ini_stage_init(slave_controller=controller)

        if self.is_master:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.RELAY_PIN, GPIO.OUT)
            GPIO.output(self.RELAY_PIN, GPIO.HIGH)  # Default to OFF

        info = "Relay control initialized"
        initialized = True
        return info, initialized

    def get_actuator_value(self):
        """Get the current relay state (0 = OFF, 1 = ON)."""
        state = GPIO.input(self.RELAY_PIN)
        return DataActuator(data=int(not state))  # Relay is ACTIVE LOW (0 = ON, 1 = OFF)

    def move_abs(self, value: DataActuator):
        """Switch relay ON/OFF based on the provided value (1 = ON, 0 = OFF)."""

        value = int(value.value())  # Ensure value is an integer (0 or 1)
        GPIO.output(self.RELAY_PIN, GPIO.LOW if value == 1 else GPIO.HIGH)

        state_str = "ON" if value == 1 else "OFF"
        self.settings.child('relay_state').setValue(state_str)  # Update UI

        self.emit_status(ThreadCommand('Update_Status', [f'Relay turned {state_str}']))

    def move_home(self):
        """Set relay to OFF (safe home position)."""
        GPIO.output(self.RELAY_PIN, GPIO.HIGH)  # Ensure relay is OFF
        self.settings.child('relay_state').setValue('OFF')  # Update UI
        self.emit_status(ThreadCommand('Update_Status', ['Relay moved to HOME (OFF)']))

    def stop_motion(self):
        """Turn relay OFF (safe stop)."""
        GPIO.output(self.RELAY_PIN, GPIO.HIGH)
        self.emit_status(ThreadCommand('Update_Status', ['Relay turned OFF (Safe Stop)']))

    def commit_settings(self, param: Parameter):
        """Handle setting changes (not needed for simple ON/OFF relay)."""
        pass

    def close(self):
        """Clean up GPIO when the plugin is closed."""
        GPIO.cleanup()
        self.emit_status(ThreadCommand('Update_Status', ['GPIO cleanup done']))


if __name__ == '__main__':
    main(__file__)
