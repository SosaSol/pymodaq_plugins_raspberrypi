import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

import time
from gpiozero import DistanceSensor

VALID_GPIO_PINS = [
    2, 3, 4, 17, 18, 27, 22, 23, 24, 25, 5, 6, 12, 13, 19, 20, 21, 26, 16
]  # Excludes power, ground, and reserved pins

class DistanceSensorWrapper:
    """
    Python Wrapper for the HC-SR04 ultrasonic sensor using gpiozero.
    """
    def __init__(self, trigger_pin: int, echo_pin: int):
        try:
            self.trigger_pin = trigger_pin
            self.echo_pin = echo_pin
            self.start_time = None
            self.sensor = DistanceSensor(echo=echo_pin, trigger=trigger_pin)
        except Exception as e:
            raise RuntimeError(f"Failed to initialise distance sensor on GPIO trigger pin {trigger_pin} and echo pin {echo_pin}: {e}")
    
    def get_distance(self) -> float:
        """ Fetch the distance measurement from the HC-SR04 sensor. """
        return self.sensor.distance * 100  # Convert to cm

    def close_communication(self):
        """ Close the sensor. """
        self.sensor.close()


class DAQ_1DViewer_DistanceSensor(DAQ_Viewer_base):
    """
    Instrument plugin class for a 1D viewer for the HC-SR04 ultrasonic sensor.
    Measures distance over time and displays it in a viewer.

    Compatible with HC-SR04 ultrasonic distance sensors.
    """
    params = comon_parameters + [
        {"title": "Trigger Pin:", "name": "trigger_pin", "type": "int", "value": 17, "min": 0, "max": 40, "step": 1},
        {"title": "Echo Pin:", "name": "echo_pin", "type": "int", "value": 18, "min": 0, "max": 40, "step": 1},
        {"title": "Update Interval (s):", "name": "update_interval", "type": "float", "value": 0.1, "min": 0.01},
        {"title": "X Axis Label:", "name": "x_label", "type": "str", "value": "Time (s)"},
        {"title": "Y Axis Label:", "name": "y_label", "type": "str", "value": "Distance (cm)"},
    ]

    def ini_attributes(self):
        self.controller: DistanceSensorWrapper = None
        self.x_axis = None
        self.start_time = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings."""
        if param.name() == "update_interval":
            self.data_grabber_timer.setInterval(int(self.settings["update_interval"] * 1000))
        elif param.name() == "x_label":
            self.x_axis.label = param.value()
        elif param.name() == "y_label":
            self.y_axis_label = param.value()

    def ini_detector(self, controller=None):
        """Detector communication initialization."""
        self.ini_detector_init(slave_controller=controller)

        if self.is_master:
            trigger_pin = self.settings["trigger_pin"]
            echo_pin = self.settings["echo_pin"]

            if trigger_pin not in VALID_GPIO_PINS or echo_pin not in VALID_GPIO_PINS:
                raise ValueError(f"Invalid GPIO pins. Please select pins from: {VALID_GPIO_PINS}")

            self.controller = DistanceSensorWrapper(trigger_pin, echo_pin)

        self.start_time = time.time()
        self.x_axis = Axis(data=np.array([]), label=self.settings["x_label"], units="s", index=0)

        # Emit an empty data structure to initialize viewers
        self.dte_signal_temp.emit(DataToExport(name="DistanceSensor",
                                               data=[DataFromPlugins(name="Distance",
                                                                     data=[np.array([])],
                                                                     dim="Data1D",
                                                                     labels=[self.settings["y_label"]],
                                                                     axes=[self.x_axis])]))

        return "Distance Sensor Viewer initialized successfully", True

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector."""
        current_time = time.time() - self.start_time
        current_distance = self.controller.get_distance()

        self.x_axis.data = np.append(self.x_axis.data, current_time)
        y_data = np.array([current_distance])

        self.dte_signal.emit(DataToExport(name="DistanceSensor",
                                          data=[DataFromPlugins(name="Distance",
                                                                data=y_data,
                                                                dim="Data1D",
                                                                labels=[self.settings["y_label"]],
                                                                axes=[self.x_axis])]))

    def close(self):
        """Terminate the communication protocol."""
        if self.controller:
            self.controller.close_communication()
        self.emit_status(ThreadCommand("Update_Status", ["Distance Sensor Viewer closed."]))

    def stop(self):
        """Stop the current grab hardware-wise if necessary."""
        self.emit_status(ThreadCommand("Update_Status", ["Acquisition stopped."]))


if __name__ == "__main__":
    main(__file__)
