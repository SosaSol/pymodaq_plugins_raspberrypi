import numpy as np
from PyQt5.QtCore import QTimer
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter


class TemperatureSensorWrapper:
    """Wrapper for reading the CPU temperature of the Raspberry Pi."""

    @staticmethod
    def get_cpu_temperature():
        """Read the CPU temperature from the Raspberry Pi system file."""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
                return int(file.read()) / 1000  # Convert from millidegrees to degrees Celsius
        except Exception as e:
            return np.nan  # Return NaN if an error occurs


class DAQ_0DViewer_RPiTemperature(DAQ_Viewer_base):
    """
    PyMoDAQ 0D viewer plugin for monitoring the Raspberry Pi CPU temperature.
    """

    params = comon_parameters + [
        {"title": "Sampling Time (ms):", "name": "sampling_time", "type": "float", "value": 5.0, "min": 0.000001},
        {"title": "Temperature Label:", "name": "y_label", "type": "str", "value": "CPU Temperature (°C)"},
    ]

    def ini_attributes(self):
        """Initialize attributes."""
        self.controller = None  # No external hardware needed
        self.running = False
        self.data_grabber_timer = QTimer(self)  # Create the QTimer
        self.data_grabber_timer.timeout.connect(self.grab_data)  # Connect the timer to the data grabber function
        self.sync_sampling_params()  # Sync sampling time

    def commit_settings(self, param: Parameter):
        """Apply parameter changes and synchronize sampling settings."""
        if param.name() == "sampling_time":
            self.sync_sampling_params()  # Sync sampling time

    def sync_sampling_params(self):
        """Synchronize sampling time and update the timer interval."""
        sampling_time = self.settings["sampling_time"]
        if sampling_time > 0:
            self.data_grabber_timer.setInterval(int(sampling_time))  # Set the timer interval to sampling time in ms

    def ini_detector(self, controller=None):
        """Initialize detector."""
        self.ini_detector_init(slave_controller=controller)
        self.running = True  # Set running flag
        self.data_grabber_timer.start()  # Start the timer

        # Initialize PyMoDAQ viewer with a placeholder value
        self.dte_signal_temp.emit(DataToExport(name="RPi_Temperature",
                                               data=[DataFromPlugins(name="Temperature",
                                                                     data=[np.array([0])],  # Single 0D data point
                                                                     dim="Data0D",
                                                                     labels=[self.settings["y_label"]])]))
        return "Raspberry Pi CPU Temperature Sensor initialized", True

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector."""
        if not self.running:
            return

        temperature = TemperatureSensorWrapper.get_cpu_temperature()
        y_data = np.array([temperature])

        self.dte_signal.emit(DataToExport(name="RPi_Temperature",
                                          data=[DataFromPlugins(name="Temperature",
                                                                data=y_data,
                                                                dim="Data0D",
                                                                labels=[self.settings["y_label"]])]))

    def stop(self):
        """Stop the current grab."""
        self.running = False
        self.data_grabber_timer.stop()  # Stop the timer
        self.emit_status(ThreadCommand("Update_Status", ["Temperature monitoring stopped."]))

    def close(self):
        """Close the detector."""
        self.running = False
        self.data_grabber_timer.stop()  # Stop the timer
        self.emit_status(ThreadCommand("Update_Status", ["RPi Temperature Sensor closed."]))


if __name__ == "__main__":
    main(__file__)
