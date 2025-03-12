from pymodaq.control_modules.move_module import DAQ_Move_base
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter import Parameter
import RPi.GPIO as GPIO

class DAQ_Move_Relay(DAQ_Move_base):
    """
    Plugin for controlling a relay connected to a Raspberry Pi GPIO pin.
    """

    _controller_units = 'State'  # Relay state: ON or OFF

    def ini_attributes(self):
        self.controller = None
        self.settings.add_parameter(
            Parameter.create(
                name='relay_state', type='bool', value=False,
                tip='Relay ON (True) or OFF (False)'
            )
        )

    def ini_stage(self, controller=None):
        """
        Initialize the GPIO pin for relay control.
        """
        self.controller = GPIO
        self.controller.setmode(GPIO.BCM)
        self.pin = 26  # GPIO pin number
        self.controller.setup(self.pin, GPIO.OUT)
        self.controller.output(self.pin, GPIO.HIGH)  # Start with relay OFF
        return "Relay initialized"

    def close(self):
        """
        Clean up GPIO settings.
        """
        if self.controller:
            self.controller.cleanup()

    def move_Abs(self, value):
        """
        Set relay state based on the absolute value.
        """
        if value > 0:
            self.controller.output(self.pin, GPIO.LOW)  # Relay ON
            self.emit_status(ThreadCommand('Update_Status', [[value, 'Relay ON']]))
        else:
            self.controller.output(self.pin, GPIO.HIGH)  # Relay OFF
            self.emit_status(ThreadCommand('Update_Status', [[value, 'Relay OFF']]))

    def stop_motion(self):
        """
        Emergency stop: Turn relay OFF.
        """
        self.controller.output(self.pin, GPIO.HIGH)
        self.emit_status(ThreadCommand('Update_Status', [[0, 'Relay stopped (OFF)']]))
