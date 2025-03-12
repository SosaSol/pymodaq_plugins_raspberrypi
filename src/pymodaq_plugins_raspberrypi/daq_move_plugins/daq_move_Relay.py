from typing import Union, List, Dict
import RPi.GPIO as GPIO
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, DataActuator
)
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter

# Optionally disable warnings if reinitialization is expected:
# GPIO.setwarnings(False)

class GPIORelayWrapper:
    """Handles GPIO operations for controlling a relay on fixed pin 26."""
    
    RELAY_PIN = 26  # Fixed GPIO pin for relay control

    def __init__(self):
        """Initialize GPIO mode and setup relay pin."""
        self._setup_gpio()

    def _setup_gpio(self):
        """Setup the GPIO pin for relay control."""
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        # Check if the pin is already set as an output to avoid reinitializing it:
        if GPIO.gpio_function(self.RELAY_PIN) != GPIO.OUT:
            GPIO.setup(self.RELAY_PIN, GPIO.OUT)
        # Set the default state to OFF (HIGH for an active low relay)
        GPIO.output(self.RELAY_PIN, GPIO.HIGH)

    def get_state(self) -> int:
        """Get the current relay state (0 = OFF, 1 = ON)."""
        # For an active low relay, GPIO.LOW means ON
        return int(not GPIO.input(self.RELAY_PIN))

    def set_state(self, state: int):
        """Set relay state (1 = ON, 0 = OFF)."""
        GPIO.output(self.RELAY_PIN, GPIO.LOW if state == 1 else GPIO.HIGH)

    def cleanup(self):
        """Cleanup GPIO when done."""
        GPIO.cleanup(self.RELAY_PIN)


class DAQ_Move_Relay(DAQ_Move_base):
    """PyMoDAQ plugin to control a relay using GPIO on a Raspberry Pi."""

    is_multiaxes = False
    _axis_names: Union[List[str], Dict[str, int]] = ['relay']
    _controller_units: Union[str, List[str]] = ''
    _epsilon: Union[float, List[float]] = 0
    data_actuator_type = DataActuatorType.DataActuator  # Controls an ON/OFF device

    params = [
        {'title': 'Relay State', 'name': 'relay_state', 'type': 'list', 'limits': ['OFF', 'ON'], 'value': 'OFF'}
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        """Initialize attributes"""
        self.controller = None  # Not needed for GPIO, but kept for consistency
        self.gpio_relay = GPIORelayWrapper()  # Use our wrapper class

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
        # The DataActuator’s value should be 0 or 1.
        value = int(value.value())
        self.gpio_relay.set_state(value)
        state_str = "ON" if value == 1 else "OFF"
        self.settings.child('relay_state').setValue(state_str)  # Update UI
        self.emit_status(ThreadCommand('Update_Status', [f'Relay turned {state_str}']))

    def move_home(self):
        """Set relay to OFF (safe home position)."""
        self.gpio_relay.set_state(0)  # Ensure relay is OFF
        self.settings.child('relay_state').setValue('OFF')
        self.emit_status(ThreadCommand('Update_Status', ['Relay moved to HOME (OFF)']))

    def stop_motion(self):
        """Turn relay OFF (safe stop)."""
        self.move_home()

    def close(self):
        """Clean up GPIO when the plugin is closed."""
        self.gpio_relay.cleanup()
        self.emit_status(ThreadCommand('Update_Status', ['GPIO cleanup done']))


if __name__ == '__main__':
    main(__file__)
