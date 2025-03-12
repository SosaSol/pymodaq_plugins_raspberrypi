from pymodaq.control_modules.move_module import DAQ_Move_base
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.parameter.utils import iter_children
from pymodaq.utils.parameter import Parameter
import RPi.GPIO as GPIO

class DAQ_Move_Relay(DAQ_Move_base):
    _controller_units = "State"

    def ini_attributes(self):
        self.controller: GPIO = None  # GPIO controller
        self.settings.add_parameter(
            Parameter.create(
                name='relay_state', type='bool', value=False,
                tip='Relay ON (True) or OFF (False)'
            )
        )

    def ini_stage(self, controller=None):
        self.controller = GPIO  # Use RPi GPIO
        self.controller.setmode(GPIO.BCM)  # Set GPIO mode
        self.pin = 26  # Define relay pin
        self.controller.setup(self.pin, GPIO.OUT)
        self.controller.output(self.pin, GPIO.HIGH)  # Start relay OFF
        return ""  # Initialization successful

    def close(self):
        self.controller.cleanup()  # Reset GPIO on close

    def move_Abs(self, value):
        """Move to an absolute position (ON/OFF)"""
        if value > 0:
            print("Relay ON")
            self.controller.output(self.pin, GPIO.LOW)  # Turn relay ON
        else:
            print("Relay OFF")
            self.controller.output(self.pin, GPIO.HIGH)  # Turn relay OFF
        self.emit_status(ThreadCommand('Update_Status', [[value, '']]))

    def stop_motion(self):
        """Emergency stop - Turn relay OFF"""
        self.controller.output(self.pin, GPIO.HIGH)
        print("Relay stopped (OFF)")
