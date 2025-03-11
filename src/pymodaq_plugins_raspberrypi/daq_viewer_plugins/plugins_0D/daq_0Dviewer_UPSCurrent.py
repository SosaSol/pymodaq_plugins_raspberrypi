import numpy as np
import smbus
from pymodaq.utils.daq_utils import ThreadCommand
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

# INA219 register addresses
_REG_CONFIG       = 0x00 # Config Register (R/W)
_REG_SHUNTVOLTAGE = 0x01 # SHUNT VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE   = 0x02 # BUS VOLTAGE REGISTER (R)
_REG_POWER        = 0x03 # POWER REGISTER (R)
_REG_CURRENT      = 0x04 # CURRENT REGISTER (R)
_REG_CALIBRATION  = 0x05 # CALIBRATION REGISTER (R/W)

class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V               = 0x00      # set bus voltage range to 16V
    RANGE_32V               = 0x01      # set bus voltage range to 32V (default)

class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV              = 0x00      # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV              = 0x01      # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV             = 0x02      # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV             = 0x03      # shunt prog. gain set to /8, 320 mV range

class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S          = 0x00      #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S         = 0x01      # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S         = 0x02      # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S         = 0x03      # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S         = 0x09      # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S         = 0x0A      # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S         = 0x0B      # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S        = 0x0C      # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S        = 0x0D      # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S        = 0x0E      # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S       = 0x0F      # 12bit, 128 samples, 68.10ms

class Mode:
    """Constants for ``mode``"""
    POWERDOW                = 0x00      # power down
    SVOLT_TRIGGERED         = 0x01      # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02      # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03      # shunt and bus voltage triggered
    ADCOFF                  = 0x04      # ADC off
    SVOLT_CONTINUOUS        = 0x05      # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06      # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07      # shunt and bus voltage continuous

def find_ina219_address(i2c_bus=1):
    """Scan the I²C bus for devices and return the first detected address."""
    bus = smbus.SMBus(i2c_bus)
    for addr in range(0x03, 0x77):  # Valid I²C address range
        try:
            bus.write_quick(addr)  # Quick test to see if a device responds
            return addr
        except OSError:
            continue
    print("DEBUG: No INA219 device found on the I²C bus.")
    return None

class UPSCurrentSensor:
    """Wrapper for reading current from the UPS HAT using INA219."""
    
    def __init__(self, i2c_bus=1, addr=None):
        try:
            self.bus = smbus.SMBus(i2c_bus)
        except Exception as e:
            raise RuntimeError(f"Failed to open I2C bus {i2c_bus}: {e}")
        
        # Auto-detect the I²C address if not provided
        self.addr = addr if addr is not None else find_ina219_address(i2c_bus)
        if self.addr is None:
            raise RuntimeError("No INA219 device found on the I²C bus!")
        print(f"DEBUG: Using INA219 device at address: {hex(self.addr)}")

        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2A()

    def read(self, address):
        data = self.bus.read_i2c_block_data(self.addr, address, 2)
        return ((data[0] * 256) + data[1])

    def write(self, address, data):
        temp = [0,0]
        temp[1] = data & 0xFF
        temp[0] =(data & 0xFF00) >> 8
        self.bus.write_i2c_block_data(self.addr,address,temp)
        try:
            self.bus.write_i2c_block_data(self.addr, address, temp)
        except Exception as e:
            raise IOError(f"I2C write error at register {hex(address)}: {e}")

    def set_calibration_32V_2A(self):
        """Configures to INA219 to be able to measure up to 32V and 2A of current. Counter
            overflow occurs at 3.2A.
           ..note :: These calculations assume a 0.1 shunt ohm resistor is present
        """
        self._current_lsb = 0.1  # Current LSB = 100uA per bit
        self._cal_value = 4096
        self._power_lsb = 0.002  # Power LSB = 2mW per bit

        # Set Calibration register to 'Cal' calculated above
        self.write(_REG_CALIBRATION,self._cal_value)
        
        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = self.bus_voltage_range << 13 | \
                      self.gain << 11 | \
                      self.bus_adc_resolution << 7 | \
                      self.shunt_adc_resolution << 3 | \
                      self.mode
        self.write(_REG_CONFIG,self.config)

    def get_current_mA(self):
        """Return the measured current in mA."""
        value = self.read(_REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

    def close_communication(self):
        """Close the I2C bus."""
        self.bus.close()


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
        self.controller: UPSCurrentSensor = None

    def commit_settings(self, param: Parameter):
        """Apply parameter changes and update sampling time."""
        if param.name() == "y_label":
            self.y_axis_label = param.value()

    def ini_detector(self, controller=None):
        """Initialize detector."""
        if self.is_master:
            self.controller = UPSCurrentSensor()  # Initialize controller

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
