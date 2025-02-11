import numpy as np
from PyQt5.QtCore import QTimer
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter


class TemperatureSensorWrapper:
    """Wrapper for reading the CPU temperature of the Raspberry Pi."""
    
    def __init__(self):
        """Initialize the temperature sensor (in this case, it's just the CPU temperature file)."""
        self.sensor = "/sys/class/thermal/thermal_zone0/temp"  # Path to the CPU temperature file

    def get_temperature(self) -> float:
        """Fetch the CPU temperature (in °C)."""
        try:
            with open(self.sensor, "r") as file:
                return float(file.read()) / 1000  # Convert from millidegrees to degrees Celsius
        except Exception as e:
            print(f"Error reading temperature: {e}")
            return None  # Return None if an error occurs



class DAQ_0DViewer_RPiTemperature(DAQ_Viewer_base):
    """
    PyMoDAQ 0D viewer plugin for monitoring the Raspberry Pi CPU temperature.
    """

    params = comon_parameters + [
        {"title": "Sampling Time (ms):", "name": "sampling_time", "type": "float", "value": 100.0, "min": 1.0},
        {"title": "Temperature Label:", "name": "y_label", "type": "str", "value": "CPU Temperature (°C)"},
    ]

    def ini_attributes(self):
        """Initialize attributes."""
        self.controller: TemperatureSensorWrapper = None  

    def commit_settings(self, param: Parameter):
        """Apply parameter changes and synchronize sampling settings."""
        if param.name() == "sampling_time":
            self.data_grabber_timer.setInterval(int(self.settings["sampling_time"]))  # Update sampling time
        elif param.name() == "y_label":
            self.y_axis_label = param.value()
            
    def ini_detector(self, controller=None):
        """Initialize detector."""
        if self.controller is None:
            self.emit_status(ThreadCommand("Update_Status", ["Error: Controller not initialized."]))
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
        temperature = self.controller.get_cpu_temperature()
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
