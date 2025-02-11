from qtpy.QtCore import QThread, Slot, QRectF
from qtpy import QtWidgets
import numpy as np
import pymodaq.utils.math_utils as mutils
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main, comon_parameters
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.utils.array_manipulation import crop_array_to_axis
import cv2


class DAQ_2DViewer_Camera(DAQ_Viewer_base):
    """Virtual instrument generating 2D data"""

    params = comon_parameters + [
        {'title': 'Nimages colors:', 'name': 'Nimagescolor', 'type': 'int', 'value': 3, 'default': 3, 'min': 0,
         'max': 3},
        {'title': 'Nimages pannels:', 'name': 'Nimagespannel', 'type': 'int', 'value': 1, 'default': 0, 'min': 0},
        {'title': 'Use ROISelect', 'name': 'use_roi_select', 'type': 'bool', 'value': False},
        {'title': 'Threshold', 'name': 'threshold', 'type': 'int', 'value': 1, 'min': 0},
        {'title': 'rolling', 'name': 'rolling', 'type': 'int', 'value': 1, 'min': 0},
        {'title': 'Nx', 'name': 'Nx', 'type': 'int', 'value': 640, 'default': 640, 'min': 1},
        {'title': 'Ny', 'name': 'Ny', 'type': 'int', 'value': 480, 'default': 480, 'min': 1},
        {'title': 'Amp', 'name': 'Amp', 'type': 'int', 'value': 20, 'default': 20, 'min': 1},
        {'title': 'x0', 'name': 'x0', 'type': 'slide', 'value': 50, 'default': 50, 'min': 0},
        {'title': 'y0', 'name': 'y0', 'type': 'float', 'value': 100, 'default': 100, 'min': 0},
        {'title': 'dx', 'name': 'dx', 'type': 'float', 'value': 20, 'default': 20, 'min': 1},
        {'title': 'dy', 'name': 'dy', 'type': 'float', 'value': 40, 'default': 40, 'min': 1},
        {'title': 'n', 'name': 'n', 'type': 'int', 'value': 1, 'default': 1, 'min': 1},
        {'title': 'amp_noise', 'name': 'amp_noise', 'type': 'float', 'value': 4, 'default': 0.1, 'min': 0},

        {'title': 'Cam. Prop.:', 'name': 'cam_settings', 'type': 'group', 'children': []},
    ]

    

    def ini_attributes(self):
        self.controller: str = None
        self.video_capture = cv2.VideoCapture(1)  # Usar a câmera padrão (câmera do PC)
        if not self.video_capture.isOpened():
            raise RuntimeError("Não foi possível acessar a câmera.")
        self.x_axis = None
        self.y_axis = None
        self.live = False

    @Slot(QRectF)
    def ROISelect(self, roi_pos_size: QRectF):
        self._ROI['position'] = int(roi_pos_size.left()), int(roi_pos_size.top())
        self._ROI['size'] = int(roi_pos_size.width()), int(roi_pos_size.height())

    def commit_settings(self
                        , param):
        """
            Activate parameters changes on the hardware.

            =============== ================================ ===========================
            **Parameters**   **Type**                          **Description**
            *param*          instance of pyqtgraph Parameter   the parameter to activate
            =============== ================================ ===========================

            See Also
            --------
            set_Mock_data
        """
        self.set_Mock_data()



    def set_Mock_data(self):
        """
        Substituir o mock data por frames capturados da câmera.
        """
        # Ler frame da câmera
        ret, frame = self.video_capture.read()
        if not ret:
            raise RuntimeError("Erro ao capturar o frame da câmera.")

        
        # Converter para escala de cinza e redimensionar
        #frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        Nx = self.settings.child('Nx').value()
        Ny = self.settings.child('Ny').value()
        #data_mock = cv2.resize(frame_gray, (Nx, Ny), interpolation=cv2.INTER_AREA)
        self.image = frame_rgb
        self.x_axis = Axis(label='the x axis', data=np.linspace(0, Nx, Nx, endpoint=False), index=1)
        self.y_axis = Axis(label='the y axis', data=np.linspace(0, Ny, Ny, endpoint=False), index=0)

        return self.image


    def ini_detector(self, controller=None):
        self.ini_detector_init(controller, "Mock controller")

        self.x_axis = self.get_xaxis()
        self.y_axis = self.get_yaxis()

        # initialize viewers with the future type of data but with 0value data
        self.dte_signal_temp.emit(self.average_data(1, True))

        initialized = True
        info = 'Init'
        return info, initialized

    def close(self):
        """
        Libera a câmera ao fechar o programa.
        """
        if hasattr(self, "video_capture") and self.video_capture.isOpened():
            self.video_capture.release()


    def get_xaxis(self):
        self.set_Mock_data()
        return self.x_axis

    def get_yaxis(self):
        self.set_Mock_data()
        return self.y_axis

    def grab_data(self, Naverage=1, **kwargs):
        """
            | For each integer step of naverage range set mock data.
            | Construct the data matrix and send the data_grabed_signal once done.

            =============== ======== ===============================================
            **Parameters**  **Type**  **Description**
            *Naverage*      int       The number of images to average.
                                      specify the threshold of the mean calculation
            =============== ======== ===============================================

            See Also
            --------
            set_Mock_data
        """
        

        "live is an attempt to export data as fast as possible"
        if 'live' in kwargs:
            if kwargs['live']:
                self.live = True
                self.live = False  # don't want to use that for the moment

        if self.live:
            while self.live:
                data = self.average_data(Naverage)
                QThread.msleep(100)
                self.dte_signal.emit(data)
                QtWidgets.QApplication.processEvents()
        else:
            data = self.average_data(Naverage)
            self.dte_signal.emit(data)

    def average_data(self, Naverage, init=False):
        data = []  # list of image (at most 3 for red, green and blue channels)
        data_tmp = np.zeros_like(self.image)
        
        for ind in range(Naverage):
            data_tmp += self.set_Mock_data()
        data_tmp = data_tmp / Naverage

        data_tmp = data_tmp * (data_tmp >= self.settings['threshold']) * (init is False)
        data_tmp = np.flipud(np.fliplr(data_tmp))

        
        for ind in range(self.settings['Nimagespannel']):
            datatmptmp = []
            for indbis in range(self.settings['Nimagescolor']):
                #datatmptmp.append(data_tmp)
                datatmptmp.append(data_tmp[:,:,indbis])
            data.append(DataFromPlugins(name='Mock2D_{:d}'.format(ind), data=datatmptmp, dim='Data2D',
                                        axes=[self.y_axis, self.x_axis]))
            
        return DataToExport('Mock2D', data=data)

    def stop(self):
        """
            not implemented.
        """
        self.live = False
        return ""


if __name__ == '__main__':
    main(__file__)
