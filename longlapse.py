
#!/usr/bin/python3

# timelapse based on sunrise/sunset
# 11/13/16

import picamera
import ephem
import time
import datetime
import os
import subprocess


class Camera(object):

    def __init__(self):
        self.base_pi_path = '/home/pi/longlapse'
        self.base_remote_path = 'kestrel@KESTREL.local:/Users/kestrel/Desktop/picamera/first_run'
        self.pixels = (2592, 1944)
        self.framerate = 1
        self.led = False
        self.vflip = True
        self.hflip = True
        self.meter_mode = 'backlit'
        self.iso = 100
        # self.awb_mode = 'off'
        # self.exposure_mode = 'off'  # exposure_mode off disables picam.analog_gain & picam.digital_gain, which are not directly settable
        self.counter = 1

    def take_pic(self, today):
        with picamera.PiCamera(resolution=self.pixels, framerate=self.framerate) as picam:
            picam.iso = self.iso
            picam.led = self.led
            picam.vflip = self.vflip
            picam.hflip = self.hflip
            picam.meter_mode = self.meter_mode
            time.sleep(5)

            now = datetime.datetime.now()
            picam.capture(os.path.join(self.base_pi_path, today, '{}_frame{:03d}.jpg'.format(now.strftime("%Y-%m-%d_%H-%M"), self.counter)))
            # picam.capture('/home/pi/picameraTest/lapse/01/{}_frame{:03d}.jpg'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"), self.counter))
            # print("captured frame {} at {}\n".format(self.counter, now))

            self.counter += 1

    def wait(self):
        next_minute = (datetime.datetime.now() + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)
        delay = (next_minute - datetime.datetime.now()).seconds
        time.sleep(delay)

    def calculate_frames(self, awake_interval):
        self.total_frames_today = int(abs(awake_interval.total_seconds()/60))

    def sleep_til_sunrise(self, sleep_interval):
        time.sleep(sleep_interval)

    def make_todays_dir(self, today):
        os.mkdir(os.path.join(self.base_pi_path, today))

    def copy_todays_dir(self, today):
        copy_from = os.path.join(self.base_pi_path, today)
        copy_to = os.path.join(self.base_remote_path, today)
        subprocess.call(['scp', '-rp', copy_from, copy_to], stdout=subprocess.DEVNULL)


class Light(object):

    def __init__(self):
        self.seattle = ephem.Observer()
        self.seattle.pressure = 0
        self.seattle.horizon = '-6'
        self.seattle.lon = '-122:21:19:5'
        self.seattle.lat = '47:44:03:9'
        self.seattle.elevation = 145

    def get_times(self):
        # self.prev_rise = ephem.localtime(seattle.previous_rising(ephem.Sun()))
        self.next_rise = ephem.localtime(self.seattle.next_rising(ephem.Sun()))
        self.next_set = ephem.localtime(self.seattle.next_setting(ephem.Sun()))
        self.sleep_interval = self.next_rise - datetime.datetime.now()
        self.awake_interval = self.next_rise - self.next_set
        self.today = light.next_rise.strftime("%Y-%m-%d")


if __name__ == '__main__':
    camera = Camera()
    light = Light()

    light.get_times()
    camera.make_todays_dir(light.today)
    camera.calculate_frames(light.awake_interval)
    camera.sleep_til_sunrise(light.sleep_interval)

    for frame in range(camera.total_frames_today):
        camera.take_pic(light.today)
        camera.wait()

    # TODO: put this in try:except with limited retries
    camera.copy_todays_dir(light.today)
