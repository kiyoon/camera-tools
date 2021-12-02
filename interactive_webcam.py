# Optimised for Canon M50
# List of configs: https://github.com/gphoto/libgphoto2/issues/608
# Base capture loop code from: https://github.com/jim-easterbrook/python-gphoto2/issues/15

import gphoto2 as gp
from subprocess import Popen, PIPE

def set_config_value(camera, field_name, field_value):
    """
    Set configValue for given configField
    :param field_name:
    :param field_value:
    :return:
    """
    # get configuration tree
    config = camera.get_config()
#    for child in config.get_children():
#        label = '{} ({})'.format(child.get_label(), child.get_name())
#        print(label)
    # find the capture target config item
    config_target = gp.check_result(gp.gp_widget_get_child_by_name(config, str(field_name)))
    # value = gp.check_result(gp.gp_widget_get_choice(config_target, 2))
    gp.check_result(gp.gp_widget_set_value(config_target, str(field_value)))
    # set config
    camera.set_config(config)
    #logger.debug("set field_name:{}, field_value:{}".format(field_name, field_value))

if __name__ == '__main__':
    camera = gp.Camera()
    try:
        camera.init()
    except Exception:
        print('Killing processes to unlock camera..')
        proc = Popen(['pkill', '-9', 'gvfs-gphoto2-volume-monitor'])
        proc.communicate()
        proc = Popen(['pkill', '-9', 'gvfsd-gphoto2'])
        proc.communicate()
        camera.init()

    ffmpeg = Popen(['ffmpeg', '-i', '-', '-vcodec', 'rawvideo', '-pix_fmt', 'yuv420p', '-f', 'v4l2', '/dev/video0'], stdin=PIPE)

    iso = 400 
    i = 1
    while True:
        capture = camera.capture_preview()
        #if i > 1000:
        if True:
            set_config_value(camera, 'iso', iso)
            set_config_value(camera, 'whitebalance', 'Color Temperature')
            set_config_value(camera, 'colortemperature', 5200)
            set_config_value(camera, 'whitebalanceadjusta', '+0') # Color Temperature AB
            set_config_value(camera, 'whitebalanceadjustb', '+0') # Color Temperature GM
            #set_config_value(camera, 'whitebalanceadjusta', 9) # Color Temperature AB
            #set_config_value(camera, 'whitebalanceadjustb', 9) # Color Temperature GM
            
        i += 1
        print(i)
        #iso += 100
        filedata = capture.get_data_and_size()
        data = memoryview(filedata)
        ffmpeg.stdin.write(data.tobytes())
