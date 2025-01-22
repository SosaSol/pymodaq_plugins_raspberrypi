from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter

# Import Libraries forSevo control
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory


# Define the Python wrapper for controlling the SG90 servo motor
class ServoWrapper:
    def __init__(self, pin: int):
        self.factory = PiGPIOFactory()
        self.servo = Servo(pin, min_pulse_width=0.0005, max_pulse_width=0.0025, pin_factory=self.factory)

    def move_to_angle(self, angle: float):
        """Move the servo to a specific angle (0 to 180 degrees)"""
        servo_value = (angle / 90) - 1  # Convert the angle to a value between -1 and 1
        self.servo.value = servo_value


class DAQ_Move_Servo(DAQ_Move_base):
    """ Instrument plugin class for controlling an SG90 servo motor.
    
    This class communicates with the Raspberry Pi's GPIO pins to control the servo motor.
    """

    is_multiaxes = False
    _axis_names: Union[List[str], Dict[str, int]] = ['Servo']
    _controller_units: Union[str, List[str]] = 'Degrees'
    _epsilon: Union[float, List[float]] = 0.1
    data_actuator_type = DataActuatorType.DataActuator  # Actuator type is a DataActuator

    # Define the parameters for controlling the servo
    params = [   
        {'name': 'angle', 'type': 'float', 'label': 'Angle', 'units': 'Degrees', 'min': 0, 'max': 180, 'initial': 90, 'set_cmd': 'move_to_angle'}
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        """ Initialize the controller attribute and other required settings """
        # Here we instantiate the servo controller (ServoWrapper)
        self.controller: ServoWrapper = ServoWrapper(pin=17)

    def get_actuator_value(self):
        """ Get the current value of the servo (angle) """
        # This is not as relevant for servo motors since they usually don't provide feedback directly,
        # but we can return the last set angle (for consistency with other plugins).
        return DataActuator(data=self.controller.servo.value * 90 + 90)  # Convert from -1 to 1 to 0 to 180 degrees

    def close(self):
        """ Terminate communication with the servo (if needed) """
        # We don't need to close anything explicitly for gpiozero
        self.emit_status(ThreadCommand('Update_Status', ['Servo motor communication closed.']))


    def commit_settings(self, param: Parameter):
        """ Apply the consequences of a change of value in the parameter settings """
        if param.name() == 'angle':
            # Apply the new angle value immediately
            self.move_to_angle(DataActuator(data=param.value()))
        else:
            pass

    def ini_stage(self, controller=None):

        """ Initialize the actuator communication """
        info = "Servo initialized successfully."
        initialized = True
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the servo to the desired angle """
        # Ensure that the value is within the allowed range of 0 to 180 degrees
        if 0 <= value.value() <= 180:
            self.controller.move_to_angle(value.value())
            self.emit_status(ThreadCommand('Update_Status', [f"Servo moved to {value.value()} degrees."]))
        else:
            self.emit_status(ThreadCommand('Update_Status', ['Invalid angle. Please enter a value between 0 and 180 degrees.']))

    def move_rel(self, value: DataActuator):
        """ Move the servo relative to the current position (increment/decrement by value)
        
        Parameters
        ----------
        value: (DataActuator) - The relative increment/decrement for the angle
        """
        # Get the current position of the servo
        current_position = self.get_actuator_value().value()

        # Calculate the target position by adding the relative value to the current position
        target_position = current_position + value.value()

        # Ensure the target position is within the valid bounds of 0 to 180 degrees
        target_position = max(0, min(target_position, 180))

        # Move the servo to the target position
        self.controller.move_abs(target_position)

        # Update the current position attribute
        self.current_position = target_position

        # Emit status update
        self.emit_status(ThreadCommand('Update_Status', [f"Servo poition incredmented by {value.value()},from {current_position} degrees to {target_position} degrees."]))
    
    def move_Home(self):
        self.controller.move_abs(0)
        self.emit_status(ThreadCommand('Update_Status',) ['Servo moved home to 0 degrees.'])

if __name__ == '__main__':
    main(__file__)
