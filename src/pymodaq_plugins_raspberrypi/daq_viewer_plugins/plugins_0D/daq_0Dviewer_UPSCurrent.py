import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_raspberrypi.hardware.INA219_wrapper import INA219Wrapper
class DAQ_0DViewer_UPSCurrent(DAQ_Viewer_base):
    """
    PyMoDAQ 0D viewer plugin for monitoring the current drawn from the UPS HAT.
    Uses the INA219 chip to measure the current in mA.
    """

    params = comon_parameters + [
        {"title": "Current Label:", "name": "y_label", "type": "str", "value": "Current (mA)"},
    ]

    def ini_attributes(self):
        """Initialize attributes."""
        self.controller: INA219Wrapper = None

    def commit_settings(self, param: Parameter):
        """Apply parameter changes and update sampling time."""
        if param.name() == "y_label":
            self.y_axis_label = param.value()

    def ini_detector(self, controller=None):
        """Initialize detector."""
        if self.is_master:
            self.controller = INA219Wrapper() # Initialize controller

        # Emit initial dummy data
        self.dte_signal_temp.emit(DataToExport(name="UPS_Current",
                                               data=[DataFromPlugins(name="Current",
                                                                     data=[np.array([0])],  # Placeholder
                                                                     dim="Data0D",
                                                                     labels=[self.settings["y_label"]])]))
        return "UPS Current Sensor initialized successfully", True

    def grab_data(self, Naverage=1, **kwargs):
        """Acquire current data from the UPS HAT."""
        current_mA = self.controller.get_current_mA()
        y_data = np.array([current_mA])  # Single value for 0D viewer
        self.dte_signal.emit(DataToExport(name="UPS_Current",
                                          data=[DataFromPlugins(name="Current",
                                                                data=y_data,
                                                                dim="Data0D",
                                                                labels=[self.settings["y_label"]])]))

    def stop(self):
        """Stop data acquisition."""
        self.emit_status(ThreadCommand("Update_Status", ["Acquisition stopped."]))

    def close(self):
        """Clean up resources."""
        if self.controller:
            self.controller.close_communication()
        self.emit_status(ThreadCommand("Update_Status", ["UPS Current Sensor closed."]))

if __name__ == "__main__":
    main(__file__)
