pymodaq_plugins_raspberrypi
########################

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_raspberrypi.svg
   :target: https://pypi.org/project/pymodaq_plugins_template/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: (https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_raspberrypi/workflows/Upload%20Python%20Package/badge.svg
   :target: https://github.com/PyMoDAQ/pymodaq_plugins_raspberrypi
   :alt: Publication Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_raspberrypi/actions/workflows/Test.yml/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins_raspberrypi/actions/workflows/Test.yml


The `pymodaq_plugins_raspberrypi` repository provides PyMoDAQ plugins for controlling hardware using Raspberry Pi GPIOs. It includes the ability to control servos using the `gpiozero` and `pigpio` libraries, allowing easy integration with PyMoDAQ's motion control system.

Authors
=======

* Solim Rovera (solim.rovera@student.isae-supaero.fr)

    Contributors
    ===========
    * ChatGPT

Instruments
===========

This plugin contains the following instruments:

Actuators
+++++++++

* **Servo**: Control of an SG90 servo motor using PWM signals with the `gpiozero` and `pigpio` libraries. The servo can be positioned within a range of 0° to 180°.

Viewers and Detectors
++++++++++

This plugin currently does not support any 0D, 1D, or 2D detectors, but these could be added in future versions.

PID Models
==========
This plugin currently does not include any PID models.

Extensions
===========
This plugin can be extended by adding more actuator control types or additional detector support.

---

Installation Instructions
=========================

- **PyMoDAQ Version**: >= 4.0
- **Tested On**: Raspberry Pi 4 B+
- **Required Libraries**:
  - `gpiozero`: Python library for controlling the GPIO pins.
  - `pigpio`: Library for controlling GPIO pins via PWM, necessary for controlling the servo motor.

Steps to Install

1. **Clone the Repository**: Clone the repository to your Raspberry Pi.
   .. codeblock::

    git clone https://github.com/sosasol/pymodaq_plugins_raspberrypi.git

2. **Install the plugin**: run the following code.
   .. codeblock::

    cd pymodaq_plugins_raspberrypi
    pip install .
