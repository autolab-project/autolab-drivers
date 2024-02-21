# -*- coding: utf-8 -*-
"""
Supported instruments (identified):
-
"""
category = "Camera"

import numpy as np


class Driver():

    def __init__(self):
        self._nb_img = 1

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

    def get_image_avg(self):
        """ Capture N images and output average """
        if self._nb_img == 1:
            return self.get_one_image()

        self.capture(self._nb_img)
        average_img = list()

        for i in range(self._nb_img):
            image = self.get_image()
            average_img.append(image)

        average_img = np.mean(average_img, 0, dtype=image.dtype)
        return average_img

    def get_nb_img(self) -> int:
        return int(self._nb_img)

    def set_nb_img(self, value: int):
        assert int(value) > 0, 'Average should be positive int'
        self._nb_img = int(value)


    def get_driver_model(self):
        model = []
        model.append({'element': 'variable', 'name': 'image',
                      'type': np.ndarray,
                      'read': self.get_image_avg,
                      'help': 'Capture and return one image or an average of N images using the average variable'})

        model.append({'element': 'variable', 'name': 'average',
                      'type': int,
                      'read_init': True, 'read': self.get_nb_img, 'write': self.set_nb_img,
                      'help': 'Number of images averaged during acquisition'})

        model.append({'element': 'action', 'name': 'abort',
                      'do': self.abort,
                      'help': 'Abort image acquisition'})

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
        error = ''
        for mode in try_mode:

            # Find index, serial
            try:
                index, serial = cam.find_first(mode)
            except Exception as e:
                error = e
                continue

            # Open the connection
            try:
                cam.open(index, mode)
            except pecamerapy.CommOpenError as e:
                error = e
                break
            else:
                CAMERA_FOUND = True
                break

        if not CAMERA_FOUND: raise ConnectionError(f'Error with camera: {error}')

        self.cam = cam

        Driver.__init__(self)

    def close(self):
        # Abort the capture
        self.cam.abort()
        # Close the camera
        self.cam.close()
############################## Connections classes ##############################
#################################################################################
