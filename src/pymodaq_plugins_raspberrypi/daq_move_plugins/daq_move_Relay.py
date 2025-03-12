from typing import Union, List, Dict
import RPi.GPIO as GPIO
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, DataActuator
)
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter


class GPIORelayWrapper:
    """Handles GPIO operations for controlling a relay."""
    
    def __init__(self, pin: int):
        """Initialize GPIO mode and setup relay pin."""
        self.pin = pin
        self._setup_gpio()

    def _setup_gpio(self):
        """Setup the GPIO pin for relay control."""
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()  # Reset all GPIOs to avoid conflicts
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH)  # Default to OFF

    def change_pin(self, new_pin: int):
        """Change the relay control pin dynamically."""
        if new_pin != self.pin:
            GPIO.cleanup()  # Clean up before changing
            self.pin = new_pin
            self._setup_gpio()

    def get_state(self) -> int:
        """Get the current relay state (0 = OFF, 1 = ON)."""
        return int(not GPIO.input(self.pin))  # Relay is ACTIVE LOW (0 = ON, 1 = OFF)

    def set_state(self, state: int):
        """Set relay state (1 = ON, 0 = OFF)."""
        GPIO.output(self.pin, GPIO.LOW if state == 1 else GPIO.HIGH)

    def cleanup(self):
        """Cleanup GPIO when done."""
        GPIO.cleanup()


class DAQ_Move_Relay(DAQ_Move_base):
    """PyMoDAQ plugin to control a relay using GPIO on a Raspberry Pi."""

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
        self.gpio_relay = GPIORelayWrapper(self.relay_pin)  # Use wrapper class

    def ini_stage(self, controller=None):
        """Initialize GPIO pin"""
        self.ini_stage_init(slave_controller=controller)
        info = "Relay control initialized"
        initialized = True
        return info, initialized

    def get_actuator_value(self):
        """Get the current relay state (0 = OFF, 1 = ON)."""
        state = self.gpio_relay.get_state()
        return DataActuator(data=state)

    def move_abs(self, value: DataActuator):
        """Switch relay ON/OFF based on the provided value (1 = ON, 0 = OFF)."""
        value = int(value.value())  # Ensure value is an integer (0 or 1)
        self.gpio_relay.set_state(value)

        state_str = "ON" if value == 1 else "OFF"
        self.settings.child('relay_state').setValue(state_str)  # Update UI
        self.emit_status(ThreadCommand('Update_Status', [f'Relay turned {state_str}']))

    def move_home(self):
        """Set relay to OFF (safe home position)."""
        self.gpio_relay.set_state(0)  # Ensure relay is OFF
        self.settings.child('relay_state').setValue('OFF')  # Update UI
        self.emit_status(ThreadCommand('Update_Status', ['Relay moved to HOME (OFF)']))

    def stop_motion(self):
        """Turn relay OFF (safe stop)."""
        self.move_home()

    def commit_settings(self, param: Parameter):
        """Handle setting changes dynamically."""
        if param.name() == 'relay_pin':
            new_pin = param.value()
            self.gpio_relay.change_pin(new_pin)
            self.emit_status(ThreadCommand('Update_Status', [f'Relay pin changed to {new_pin}']))

    def close(self):
        """Clean up GPIO when the plugin is closed."""
        self.gpio_relay.cleanup()
        self.emit_status(ThreadCommand('Update_Status', ['GPIO cleanup done']))


if __name__ == '__main__':
    main(__file__)