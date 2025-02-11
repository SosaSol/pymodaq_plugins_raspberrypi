import numpy as np
from PyQt5.QtCore import QTimer
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter


class DAQ_0DViewer_RPiTemperature(DAQ_Viewer_base):
    """
    PyMoDAQ 0D viewer plugin for monitoring the Raspberry Pi CPU temperature.
    """

    params = comon_parameters + [
        {"title": "Sampling Time (ms):", "name": "sampling_time", "type": "float", "value": 100.0, "min": 1.0},
        {"title": "Temperature Label:", "name": "y_label", "type": "str", "value": "CPU Temperature (°C)"},
    ]

    def __init__(self):
        """Ensure the viewer is properly initialized."""
        super().__init__()

    def commit_settings(self, param: Parameter):
        """Apply parameter changes and synchronize sampling settings."""
        if param.name() == "sampling_time":
            self.data_grabber_timer.setInterval(int(self.settings["sampling_time"]))  # Update sampling time
        elif param.name() == "y_label":
            self.y_axis_label = param.value()

    def get_cpu_temperature(self):
        """Read the CPU temperature from the Raspberry Pi system file."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
                return float(file.read()) / 1000  # Convert from millidegrees to degrees Celsius
        except Exception as e:
            print(f"Error reading temperature: {e}")
            return None  # Return None if an error occurs

    def ini_detector(self, controller=None):
        """Initialize detector."""
        # Initialize detector and check if the temperature can be read
        temperature = self.get_cpu_temperature()
        if temperature is None:
            self.emit_status(ThreadCommand("Update_Status", ["Error: Unable to read temperature."]))
            return

        self.ini_detector_init(slave_controller=controller)

        # Send initial dummy data to PyMoDAQ
        self.dte_signal_temp.emit(DataToExport(name="RPi_Temperature",
                                               data=[DataFromPlugins(name="Temperature",
                                                                     data=[np.array([0])],  # Placeholder data
                                                                     dim="Data0D",
                                                                     labels=[self.settings["y_label"]])]))
        return "Raspberry Pi CPU Temperature Sensor initialized", True

    def grab_data(self, Naverage=1, **kwargs):
        """Acquire temperature data."""
        temperature = self.get_cpu_temperature()
        if temperature is None:
            self.emit_status(ThreadCommand("Update_Status", ["Error reading temperature."]))
            return

        y_data = np.array([temperature])

        self.dte_signal.emit(DataToExport(name="RPi_Temperature",
                                          data=[DataFromPlugins(name="Temperature",
                                                                data=y_data,
                                                                dim="Data0D",
                                                                labels=[self.settings["y_label"]])]))

    def stop(self):
        """Clean up resources."""
        self.emit_status(ThreadCommand("Update_Status", ["Temperature monitoring stopped."]))

    def close(self):
        """Close the detector."""
        self.emit_status(ThreadCommand("Update_Status", ["RPi Temperature Sensor closed."]))


if __name__ == "__main__":
    main(__file__)
