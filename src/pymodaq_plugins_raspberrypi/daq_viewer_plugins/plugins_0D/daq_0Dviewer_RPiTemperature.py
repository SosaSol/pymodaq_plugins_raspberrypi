import numpy as np
from PyQt5.QtCore import QTimer
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

class TemperatureSensor:
    """Wrapper for reading the CPU temperature of the Raspberry Pi."""
    
    def __init__(self):
        """Initialize the temperature sensor (using the CPU temperature file)."""
        self.sensor = "/sys/class/thermal/thermal_zone0/temp"  # Path to the CPU temperature file
        print(f"DEBUG: Temperature sensor file set to {self.sensor}")

    def get_temperature(self) -> float:
        """Fetch the CPU temperature (in °C)."""
        try:
            with open(self.sensor, "r") as file:
                temp_str = file.read().strip()
                print(f"DEBUG: Raw temperature string: {temp_str}")
                temp = float(temp_str) / 1000  # Convert from millidegrees to degrees Celsius
                print(f"DEBUG: Converted temperature: {temp} °C")
                return temp
        except Exception as e:
            print(f"Error reading temperature: {e}")
            return None  # Return None if an error occurs

class DAQ_0DViewer_RPiTemperature(DAQ_Viewer_base):
    """
    PyMoDAQ 0D viewer plugin for monitoring the Raspberry Pi CPU temperature.
    """

    params = comon_parameters + [
        {"title": "Temperature Label:", "name": "y_label", "type": "str", "value": "CPU Temperature (°C)"},
    ]

    def ini_attributes(self):
        """Initialize attributes."""
        self.controller: TemperatureSensor = None
        print("DEBUG: ini_attributes() called, controller set to None.")

    def commit_settings(self, param: Parameter):
        """Apply parameter changes and synchronize sampling settings."""
        if param.name() == "y_label":
            self.y_axis_label = param.value()
            print(f"DEBUG: Temperature label updated to {self.settings['y_label']}")

    def ini_detector(self, controller=None):
        """Initialize detector."""
        if self.controller is None:
            self.controller = TemperatureSensor()  # Initialize controller
            print("DEBUG: TemperatureSensor controller initialized in ini_detector().")
        else:
            print("DEBUG: Controller already initialized.")
        self.ini_detector_init(slave_controller=controller)
        self.dte_signal_temp.emit(DataToExport(name="RPi_Temperature",
                                                data=[DataFromPlugins(name="Temperature",
                                                                    data=[np.array([0])],
                                                                    dim="Data0D",
                                                                    labels=[self.settings["y_label"]])]))
        return "Raspberry Pi CPU Temperature Sensor initialized", True

    def grab_data(self, Naverage=1, **kwargs):
        """Acquire temperature data."""
        if self.controller is None:
            print("DEBUG: In grab_data() - Controller is not initialized!")
            self.emit_status(ThreadCommand("Update_Status", ["Error: Controller not initialized."]))
            return
        temperature = self.controller.get_temperature()
        if temperature is None:
            print("DEBUG: In grab_data() - Failed to read temperature!")
            self.emit_status(ThreadCommand("Update_Status", ["Error: Failed to read temperature."]))
            return
        print(f"DEBUG: In grab_data() - Temperature read: {temperature} °C")
        y_data = np.array([temperature])
        self.dte_signal.emit(DataToExport(name="RPi_Temperature",
                                        data=[DataFromPlugins(name="Temperature",
                                                                data=y_data,
                                                                dim="Data0D",
                                                                labels=[self.settings["y_label"]])]))

    def stop(self):
        """Clean up resources."""
        self.emit_status(ThreadCommand("Update_Status", ["Temperature monitoring stopped."]))
        print("DEBUG: stop() called.")

    def close(self):
        """Close the detector."""
        self.emit_status(ThreadCommand("Update_Status", ["RPi Temperature Sensor closed."]))
        print("DEBUG: close() called.")

if __name__ == "__main__":
    main(__file__)
