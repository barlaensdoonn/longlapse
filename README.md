## *longlapse.py*

###### python script for longterm timelapse on raspberry pi

- uses sunrise/sunset times calculated with pyephem library to determine # of frames for the day and when to start/stop
- saves each day's photos in a directory named YYY-MM-DD
- copies photos over the network to an archive at the end of the day
- writes activity to a log file and copies to a remote DropBox directory daily
