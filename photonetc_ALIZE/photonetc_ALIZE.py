# -*- coding: utf-8 -*-
"""
Supported instruments (identified):
-
"""
import numpy as np


class Driver():

    def __init__(self):
        pass

    def abort(self):
        self.cam.abort()

    def get_one_image(self) -> np.ndarray:  # np.ndarray[np.uint16]
        """ Capture one image to buffer and output it """
        self.capture(1)
        return self.get_image()

    def capture(self, value: int):
        """ Capture N images to buffer """
        value = int(value)
        frames: int = value
        pythonBufferSize: int = value
        self.cam.capture(frames, pythonBufferSize)

    def capture_video(self, value: int):
        """ Capture continuously images to buffer of size N """
        value = int(value)
        pythonBufferSize: int = value
        self.cam.capture_video(pythonBufferSize)

    def get_image(self, timeout_sec: int = 1) -> np.ndarray:  # np.ndarray[np.uint16]
        """ Output one image from buffer """
        img, metadata = self.cam.get_image(timeout_sec)
        # metadata is pecamerapy.Metadata with method: counter, exposure_time, gpi_state, pitch, timestamp
        return img

    def get_driver_model(self):
        model = []
        model.append({'element':'variable', 'name':'image',
                      'read':self.get_one_image, 'type':np.ndarray,
                      'help':'Capture and return a frame'})
        return model


#################################################################################
############################## Connections classes ##############################
class Driver_USB(Driver):
    def __init__(self, **kwargs):

        import pecamerapy

        # Define a Camera
        cam = pecamerapy.Camera()

        # Choose the desired connection mode
        try_mode = [pecamerapy.OpenMode.USB3,
                    pecamerapy.OpenMode.USB2]

        CAMERA_FOUND = False
        for mode in try_mode:

            # Find index, serial
            try:
                index, serial = cam.find_first(mode)
            except:
                continue

            # Open the connection
            try:
                cam.open(index, mode)
            except pecamerapy.CommOpenError:
                continue
            else:
                CAMERA_FOUND = True
                break

        if not CAMERA_FOUND: raise ConnectionError('No camera found')

        self.cam = cam

        Driver.__init__(self)

    def close(self):
        # Abort the capture
        self.cam.abort()
        # Close the camera
        self.cam.close()
############################## Connections classes ##############################
#################################################################################
