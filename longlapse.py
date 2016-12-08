#!/usr/bin/python3

# timelapse based on sunrise/sunset
# 11/13/16
# updated 12/1/16

import picamera
import ephem
import time
import datetime
import os
import shutil
import subprocess
# import shlex
import logging
import traceback
from fractions import Fraction
from longpaths import remote_path, host

log_locate = '/home/pi/longlapse/longlapse.log'


class Camera(object):

    def __init__(self):
        self.base_pi_path = '/home/pi/longlapse'
        self.remote_path = remote_path
        self.copied = False
        self.pixels = (2592, 1944)
        self.framerate = 1
        self.led = False
        self.vflip = True
        self.hflip = True
        self.meter_mode = 'backlit'
        self.iso = 100
        self.awb_mode = 'off'
        self.awb_gains = (Fraction(447, 256), Fraction(255, 256))
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

            picam.awb_mode = self.awb_mode
            picam.awb_gains = self.awb_gains

            for frame in range(self.total_frames_today):
                now = datetime.datetime.now()
                picam.capture(os.path.join(self.base_pi_path, today, '{}_frame{:03d}.jpg'.format(now.strftime("%Y-%m-%d_%H-%M"), self.counter)))
                logging.debug("awb_gains for frame{:03d}: {}".format(self.counter, picam.awb_gains))

                self.counter += 1
                self.wait()

    def wait(self):
        next_minute = (datetime.datetime.now() + datetime.timedelta(minutes=10)).replace(second=0, microsecond=0)
        delay = (next_minute - datetime.datetime.now()).total_seconds()
        time.sleep(delay)

    def calculate_frames(self, awake_interval):
        self.total_frames_today = int(abs(awake_interval / 600))

    def sleep_til_sunrise(self, sleep_interval):
        time.sleep(sleep_interval)

    def make_todays_dir(self, today):
        self.todays_dir = os.path.join(self.base_pi_path, today)
        if not os.path.isdir(self.todays_dir):
            os.mkdir(self.todays_dir)

    def make_remote_dir(self, today):
        self.remote_dir = os.path.join(self.remote_path, today)
        status = subprocess.call(['ssh', host, 'test -d {}'.format(self.remote_dir)], stdout=subprocess.DEVNULL, stderr=log_locate)

        if status == 1:
            remote = subprocess.call(['ssh', host, 'mkdir {}'.format(self.remote_dir)])

        if status == 1 and remote == 0:
            logging.info('created remote directory at {}'.format(self.remote_dir))
            return True
        elif status == 0:
            logging.info('remote directory already exists at {}'.format(self.remote_dir))
            return True
        else:
            logging.warning('problem creating remote directory at {}'.format(self.remote_dir))
            return False

    def copy_todays_dir(self, today):
        '''
        to check if file exists on remote use:
        subprocess.call(['ssh', host, 'test -f {}'.format(shlex.quote(path))])
        '''
        remote = self.make_remote_dir(today)

        if remote:
            status_dict = {}
            pic_list = [thing for thing in os.listdir(self.todays_dir) if not thing.startswith('.')]
            pic_list.sort()

            for pic in pic_list:
                pic_path = os.path.join(self.todays_dir, pic)
                status = subprocess.call(['scp', '-p', pic_path, self.remote_dir], stdout=subprocess.DEVNULL, stderr=log_locate)
                status_dict[pic] = status

        for key in status_dict.keys():
            if status_dict[key] == 1:
                logging.warning("trouble copying {}".format(key))
                self.copied = False
        else:
            self.copied = True

    def copy_log(self):
        dropbox_path = 'dropbox_me/Dropbox/longlapse'
        copy_log_from = os.path.join(self.base_pi_path, 'longlapse.log')
        copy_log_to = os.path.join(self.base_remote_path, dropbox_path)
        subprocess.call(['scp', '-p', copy_log_from, copy_log_to], stdout=subprocess.DEVNULL, stderr=log_locate)

    def delete_todays_dir(self):
        if os.path.isdir(self.todays_dir) and self.copied:
            shutil.rmtree(self.todays_dir)
            logging.info("deleted today's directory")
        else:
            logging.warning("did not delete today's directory")


class Light(object):

    def __init__(self):
        self.seattle = ephem.Observer()
        self.seattle.pressure = 0
        self.seattle.horizon = '-6'
        self.seattle.lon = '-122:21:19:5'
        self.seattle.lat = '47:44:03:9'
        self.seattle.elevation = 145

    def get_times(self):
        # self.prev_rise = ephem.localtime(self.seattle.previous_rising(ephem.Sun()))
        self.next_rise = ephem.localtime(self.seattle.next_rising(ephem.Sun()))
        self.next_set = ephem.localtime(self.seattle.next_setting(ephem.Sun()))
        self.sleep_interval = (self.next_rise - datetime.datetime.now()).total_seconds()
        self.awake_interval = (self.next_rise - self.next_set).total_seconds()
        self.today = light.next_rise.strftime("%Y-%m-%d")


if __name__ == '__main__':
    logging.basicConfig(filename=log_locate, format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.INFO)

    camera = Camera()
    light = Light()

    try:
        light.get_times()
        logging.info('----------------------- {} -----------------------'.format(light.today))
        logging.debug('light.next_rise = {}'.format(light.next_rise))
        logging.debug('light.next_set = {}'.format(light.next_set))
        logging.debug('light.sleep_interval = {}'.format(light.sleep_interval))
        logging.debug('light.awake_interval = {}'.format(light.awake_interval))
        logging.debug('light.today = {}'.format(light.today))

        camera.make_todays_dir(light.today)
        logging.info("made today's directory at {}".format(camera.todays_dir))

        camera.calculate_frames(light.awake_interval)
        logging.info('{} frames will be shot today over {} hours'.format(camera.total_frames_today, abs(light.awake_interval) / 3600))

        logging.info('sleeping til sunrise {} hours from now'.format(light.sleep_interval / 3600))
        camera.sleep_til_sunrise(light.sleep_interval)

        logging.info("I'm awake!")

        camera.take_pic(light.today)

        # TODO: use rsync instead of these methods for file copying and directory deleting
        logging.info("copying today's directory to kestrel")
        camera.copy_todays_dir(light.today)
        logging.info("finished copying today's directory")

        camera.delete_todays_dir()

        logging.info("copying today's log to DropBox\n")
        camera.copy_log()

    except Exception as e:
        logging.error(traceback.format_exc())