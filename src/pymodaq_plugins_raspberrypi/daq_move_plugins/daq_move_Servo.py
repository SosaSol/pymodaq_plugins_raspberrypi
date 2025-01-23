from typing import Union
from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base, comon_parameters_fun, main, DataActuatorType, DataActuator
)
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory


VALID_GPIO_PINS = [
    2, 3, 4, 17, 18, 27, 22, 23, 24, 25, 5, 6, 12, 13, 19, 20, 21, 26, 16
]  # Excludes power, ground, and reserved pins

class ServoWrapper:
    """Wrapper class to control an SG90 servo motor via GPIO on a Raspberry Pi."""

    def __init__(self, pin: int, default_angle: float):
        try:
            self.factory = PiGPIOFactory()  # Set up PiGPIO for precise control
            self.servo = Servo(pin, min_pulse_width=0.0005, max_pulse_width=0.0025, pin_factory=self.factory)
            self.current_angle = default_angle  # Default position is the neutral position (90 degrees)
            self.move_to_angle(default_angle)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize servo on GPIO pin {pin}: {e}")

    def move_to_angle(self, angle: float):
        """Move the servo to a specific angle (0 to 180 degrees)."""
        if not 0 <= angle <= 180:
            raise ValueError("Angle must be between 0 and 180 degrees.")

        try:
            servo_value = (angle / 90) - 1  # Convert angle to servo value (-1 to 1)
            self.servo.value = servo_value
            self.current_angle = angle
        except Exception as e:
            raise RuntimeError(f"Failed to move servo to angle {angle}: {e}")

    def get_current_angle(self) -> float:
        """Get the current angle of the servo."""
        return self.current_angle


class DAQ_Move_Servo(DAQ_Move_base):
    """Instrument plugin class for controlling a single SG90 servo motor."""
    
    is_multiaxes = False  # Single-axis servo
    _axis_names = ['Servo']
    _controller_units = 'deg'
    _epsilon: Union[float, list] = 0.1
    data_actuator_type = DataActuatorType["DataActuator"]

    # Define parameters for the servo plugin
    params = [
        {"title": "GPIO Pin:", "name": "gpio_pin", "type": "int", "value": 17, "min": 0, "max": 40, "step": 1},
        {"title": "Home Position:", "name": "home_position", "type": "float", "value": 0.0, "min": 0.0, "max": 180.0},
        {"title": "Default Angle:", "name": "default_angle", "type": "float", "value": 90.0, "min": 0.0, "max": 180.0, "step": 1.0},
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        """Initialize attributes, including the servo controller."""
        self.controller: ServoWrapper = None  # Servo controller object

    def ini_stage(self, controller=None):
        """Initialize the servo and communication."""
        gpio_pin = self.settings["gpio_pin"]            # Get GPIO pin from settings
        default_angle = self.settings["default_angle"]  # Get Dfault Angle pin from settings

        if gpio_pin not in VALID_GPIO_PINS:
            info = f"Invalid GPIO pin: {gpio_pin}. Please choose a valid GPIO pin."
            self.emit_status(ThreadCommand("Update_Status", [info]))
            return info, False
    
        try:
            self.controller = ServoWrapper(pin=gpio_pin, default_angle=default_angle)  # Initialize the servo
            info = f"Servo initialized successfully on GPIO pin {gpio_pin}."
            initialized = True
        except RuntimeError as e:
            info = f"Failed to initialize servo on GPIO pin {gpio_pin}: {e}"
            initialized = False

        return info, initialized

    def move_abs(self, value: DataActuator):
        """Move the servo to an absolute position (angle in degrees)."""
        target_angle = self.check_bound(value.value())  # Enforce angle limits
        self.target_value = target_angle

        try:
            self.controller.move_to_angle(target_angle)
            self.emit_status(ThreadCommand("Update_Status", [f"Servo moved to {target_angle:.2f} degrees."]))
        except RuntimeError as e:
            self.emit_status(ThreadCommand("Update_Status", [f"Error moving servo: {e}"]))

    def move_rel(self, value: DataActuator):
        """Move the servo to a position relative to its current position."""
        current_angle = self.controller.get_current_angle()
        target_angle = self.check_bound(current_angle + value.value())  # Enforce limits
        self.target_value = target_angle

        try:
            self.controller.move_to_angle(target_angle)
            self.emit_status(ThreadCommand("Update_Status", [
                f"Servo moved by {value.value():.2f} degrees to {target_angle:.2f} degrees."
            ]))
        except RuntimeError as e:
            self.emit_status(ThreadCommand("Update_Status", [f"Error moving servo: {e}"]))

    def move_home(self):
        """Move the servo to the home position (0 degrees)."""
        home = self.settings['home_position']
        self.target_value = home
        try:
            self.controller.move_to_angle(home)
            self.emit_status(ThreadCommand("Update_Status", [f"Servo moved to home position ({home:.2f} degrees)."]))
        except RuntimeError as e:
            self.emit_status(ThreadCommand("Update_Status", [f"Error moving servo to home position: {e}"]))

    def stop_motion(self):
        """Stop any ongoing motion of the servo."""
        self.controller.move_to_angle(self.controller.get_current_angle())  # Hold position
        self.emit_status(ThreadCommand("Update_Status", ["Servo motion stopped."]))


    def get_actuator_value(self):
        """Get the current value of the servo (angle in degrees)."""
        current_angle = self.controller.get_current_angle()
        return DataActuator(data=current_angle)

    def close(self):
        """Terminate the communication protocol."""
        self.emit_status(ThreadCommand("Update_Status", ["Servo communication closed."]))


if __name__ == '__main__':
    main(__file__)
