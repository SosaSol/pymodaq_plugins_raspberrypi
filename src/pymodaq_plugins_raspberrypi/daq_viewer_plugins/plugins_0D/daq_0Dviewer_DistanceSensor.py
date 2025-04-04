import subprocess
import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory

VALID_GPIO_PINS = [
    2, 3, 4, 17, 18, 27, 22, 23, 24, 25, 5, 6, 12, 13, 19, 20, 21, 26, 16
]  # Excludes power, ground, and reserved pins

class DistanceSensorWrapper:
    """Wrapper for HC-SR04 ultrasonic sensor using gpiozero."""
    
    def __init__(self, trigger_pin: int, echo_pin: int, max_distance: float):
        try:
            # Create a PinFactory for gpiozero
            pin_factory = PiGPIOFactory()
            self.trigger_pin = trigger_pin
            self.echo_pin = echo_pin
            self.max_distance = max_distance
            self.sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin, pin_factory=pin_factory, max_distance=max_distance)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize sensor on GPIO pins {trigger_pin}, {echo_pin}: {e}")

    def get_distance(self) -> float:
        """Fetch distance measurement (in cm)."""
        return self.sensor.distance * 100  # Convert to cm

    def close_communication(self):
        """Close sensor communication."""
        self.sensor.close()


class DAQ_0DViewer_DistanceSensor(DAQ_Viewer_base):
    """
    PyMoDAQ 0D viewer plugin for HC-SR04 ultrasonic sensor.
    """

    params = comon_parameters + [
        {"title": "Trigger Pin:", "name": "trigger_pin", "type": "int", "value": 27, "min": 0, "max": 40, "step": 1},
        {"title": "Echo Pin:", "name": "echo_pin", "type": "int", "value": 22, "min": 0, "max": 40, "step": 1},
        {"title": "Distance Label:", "name": "y_label", "type": "str", "value": "Distance (cm)"},
        {"title": "Maximum Distance (m):", "name": "max_distance", "type": "float", "value": 2.0, "min": 0.0}
    ]

    def ini_attributes(self):
        """Initialize attributes."""
        self.controller: DistanceSensorWrapper = None
    
    def start_pigpiod_if_needed(self):
        """Ensure that pigpiod is running before initializing the sensor."""
        try:
            subprocess.check_call(['pgrep', 'pigpiod'])
        except subprocess.CalledProcessError:
            subprocess.Popen(['sudo', 'pigpiod'])
            self.emit_status(ThreadCommand("Update_Status", ["Starting pigpiod daemon..."]))
            
            # Check if it actually starts
            import time
            time.sleep(1)  # Wait for the process to start
            try:
                subprocess.check_call(['pgrep', 'pigpiod'])
                self.emit_status(ThreadCommand("Update_Status", ["Pigpiod started successfully."]))
            except subprocess.CalledProcessError:
                self.emit_status(ThreadCommand("Update_Status", ["Error: Failed to start pigpiod."]))

    def commit_settings(self, param: Parameter):
        """Apply parameter changes dynamically."""

        if param.name() == "y_label":
            self.y_axis_label = param.value()

        elif param.name() in ["trigger_pin", "echo_pin"]:
            # Get new pin values
            new_trigger = self.settings["trigger_pin"]
            new_echo = self.settings["echo_pin"]

            # Validate new pins
            if new_trigger not in VALID_GPIO_PINS or new_echo not in VALID_GPIO_PINS:
                self.emit_status(ThreadCommand("Update_Status", [f"Invalid GPIO pins. Choose from: {VALID_GPIO_PINS}"]))
                return

            # Stop current sensor
            if self.controller:
                self.controller.close_communication()

            # Reinitialize sensor with new pins
            try:
                self.controller = DistanceSensorWrapper(new_trigger, new_echo)
                self.emit_status(ThreadCommand("Update_Status", [f"Sensor updated: Trigger={new_trigger}, Echo={new_echo}"]))
            except Exception as e:
                self.emit_status(ThreadCommand("Update_Status", [f"Failed to update sensor: {e}"]))

    def ini_detector(self, controller=None):
        """Initialize detector."""
        self.start_pigpiod_if_needed()  # Ensure pigpiod is running
    
        self.ini_detector_init(slave_controller=controller)

        if self.is_master:
            trigger_pin = self.settings["trigger_pin"]
            echo_pin = self.settings["echo_pin"]
            max_distance = self.settings["max_distance"]

            if trigger_pin not in VALID_GPIO_PINS or echo_pin not in VALID_GPIO_PINS:
                raise ValueError(f"Invalid GPIO pins. Choose from: {VALID_GPIO_PINS}")

            self.controller = DistanceSensorWrapper(trigger_pin, echo_pin, max_distance)

        # Initialize PyMoDAQ viewer with a placeholder value
        self.dte_signal_temp.emit(DataToExport(name="DistanceSensor",
                                               data=[DataFromPlugins(name="Distance",
                                                                     data=[np.array([0])],  # Single 0D data point
                                                                     dim="Data0D",
                                                                     labels=[self.settings["y_label"]])]))

        return "Distance Sensor initialized successfully", True

    def grab_data(self, Naverage=1, **kwargs):
        """Acquire data from sensor."""
        current_distance = self.controller.get_distance()
        y_data = np.array([current_distance])  # Single value for 0D viewer

        self.dte_signal.emit(DataToExport(name="DistanceSensor",
                                          data=[DataFromPlugins(name="Distance",
                                                                data=y_data,
                                                                dim="Data0D",
                                                                labels=[self.settings["y_label"]])]))

    def close(self):
        """Clean up resources."""
        if self.controller:
            self.controller.close_communication()
        self.emit_status(ThreadCommand("Update_Status", ["Distance Sensor closed."]))

    def stop(self):
        """Stop data acquisition."""
        self.emit_status(ThreadCommand("Update_Status", ["Acquisition stopped."]))


if __name__ == "__main__":
    main(__file__)
