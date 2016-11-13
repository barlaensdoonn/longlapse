#!/usr/bin/python3

# timelapse based on sunrise/sunset
# 11/13/16

import picamera
import time
import datetime


pixels = (2592, 1944)
frameRate = 1
frames = 1

'''
for getting exif out of image:

from PIL import Image
from PIL.ExifTags import TAGS

with Image.open("001.jpg") as img:
exif = {
    TAGS[k]: v for k, v in img._getexif().items() if k in TAGS
}
'''


def setParams():
    with picamera.PiCamera(resolution=pixels, framerate=frameRate) as camera:
        camera.led = False
        camera.vflip = True
        camera.meter_mode = 'matrix'

        time.sleep(5)

        print("initial analog gain = ", camera.analog_gain)
        print("initial digital gain = ", camera.digital_gain)
        print("inital exposure_speed = ", camera.exposure_speed)
        print("initial awbg = ", camera.awb_gains)
        print()

        exposureValues = {"shutterSpeed": camera.exposure_speed, "awbg": camera.awb_gains}
        return exposureValues


def takePic(counter, shutterSpeed=0, awbg=0):
    with picamera.PiCamera(resolution=pixels, framerate=frameRate) as camera:
        camera.led = False
        camera.vflip = True
        camera.hflip = True
        camera.awb_mode = 'off'
        camera.exposure_mode = 'off'
        camera.iso = 100
        print("current analog gain = ", camera.analog_gain)
        print("current digital gain = ", camera.digital_gain)
        camera.shutter_speed = shutterSpeed
        # camera.shutter_speed = 3000
        # print("testing shutter speed {} instead".format(camera.shutter_speed))
        print("current shutter_speed = ", camera.shutter_speed)
        camera.awb_gains = awbg
        print("current awbg = ", awbg)

        currentTime = datetime.datetime.now()
        now = currentTime.time()
        print("capturing frame {} at {}".format(counter, now))
        camera.capture('/home/pi/picameraTest/lapse/01/{0:03d}.jpg'.format(counter))


def wait():
    next_minute = (datetime.datetime.now() + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)
    delay = (next_minute - datetime.datetime.now()).seconds
    time.sleep(delay)


if __name__ == '__main__':
    counter = 1
    params = setParams()
    wait()

    for i in range(frames):
        takePic(counter, **params)
        counter += 1
        wait()
