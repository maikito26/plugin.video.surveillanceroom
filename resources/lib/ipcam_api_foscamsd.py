"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is to exploit Foscam IP Cameras, ie models starting with F189xx.

Refernced API from:
http://foscam.devcenter.me/
"""

import urllib
from threading import Thread
import utils, settings
import socket
socket.setdefaulttimeout(settings.getSetting_int('request_timeout'))

# Foscam error code.
FOSCAM_SUCCESS           = 0
ERROR_FOSCAM_FORMAT      = -1
ERROR_FOSCAM_AUTH        = -2
ERROR_FOSCAM_CMD         = -3  # Access deny. May the cmd is not supported.
ERROR_FOSCAM_EXE         = -4  # CGI execute fail.
ERROR_FOSCAM_TIMEOUT     = -5
ERROR_FOSCAM_UNKNOWN     = -7  # -6 and -8 are reserved.
ERROR_FOSCAM_UNAVAILABLE = -8  # Disconnected or not a cam.

class FoscamError(Exception):
    def __init__(self, code):
        super(FoscamError, self).__init__()
        self.code = int(code)

    def __str__(self):
        return  'ErrorCode: %s' % self.code

class FoscamCamera(object):
    '''A python implementation of the foscam SD'''

    def __init__(self, camera_settings, daemon = False, verbose = True):
        '''
        If ``daemon`` is True, the command will be sent unblockedly.
        '''
        self.number = camera_settings[0]
        self.host = camera_settings[1]
        self.port = camera_settings[2]
        self.usr = camera_settings[3]
        self.pwd = camera_settings[4]
        self.daemon = daemon
        self.verbose = verbose

    @property
    def url(self):
        _url = '%s:%s' % (self.host, self.port)
        return _url

    @property
    def video_url(self): 
	_videoUrl = "http://{0}/videostream.asf?user={1}&pwd={2}&resolution=32&rate=0".format(self.url, self.usr, self.pwd)
        return _videoUrl

    @property
    def mjpeg_url(self): 
	_mjpegUrl = "http://{0}/videostream.cgi?user={1}&pwd={2}&resolution=32&rate=0".format(self.url, self.usr, self.pwd)
        return _mjpegUrl   #MJPEG stream is VGA resolution @ 15fps

    @property
    def snapshot_url(self):
	_snapshotUrl = "http://{0}/snapshot.cgi?user={1}&pwd={2}".format(self.url, self.usr, self.pwd)
        return _snapshotUrl

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):		
	return None
		
    def send_command(self, cmd, params = None):
        '''
        Send command to foscam.
        '''
        paramstr = ''
        if params:
            paramstr = urllib.urlencode(params)
            paramstr = '&' + paramstr if paramstr else ''
        cmdurl = 'http://%s/%s.cgi?user=%s&pwd=%s%s' %(self.url, cmd, self.usr, self.pwd, paramstr) 

        # Parse parameters from response string.
        if self.verbose:
            utils.log(4, 'Camera %s :: Send Foscam command: %s' %(self.number, cmdurl))

        code = ERROR_FOSCAM_UNKNOWN
        try:
            raw_string = ''
            raw_string = urllib.urlopen(cmdurl).read()
            #print raw_string
            code = FOSCAM_SUCCESS
            
        except:
            if self.verbose:
                utils.log(3, 'Camera %s :: Foscam exception: %s' %(self.number, raw_string))
            return ERROR_FOSCAM_UNAVAILABLE, None
        
        params = dict()
        response = raw_string.replace('var ','').replace('\n','').split(';')
        
        for child in response:
            child_split = child.split('=')
            if len(child_split) == 2:
                params[child_split[0]] = child_split[1]
            
        if self.verbose:
            utils.log(4, 'Camera %s :: Received Foscam response: %s, %s' %(self.number, code, params))
        return code, params

    def execute_command(self, cmd, params = None, callback = None):
        '''
        Execute a command and return a parsed response.
        '''
        def execute_with_callbacks(cmd, params = None, callback = None):
            code, params = self.send_command(cmd, params)
            if callback:
                callback(code, params)
            return code, params

        if self.daemon:
            t = Thread(target=execute_with_callbacks,
                    args=(cmd, ), kwargs={'params': params, 'callback': callback})
            t.daemon = True
            t.start()
        else:
            return execute_with_callbacks(cmd, params, callback)

    # *************** Device manage *******************
    def get_dev_state(self, callback = None):
        '''
        Get all device state
        cmd: getDevState
        return args:
            ......
            id:
            device id sys_ver:
            firmware version app_ver:
            webpage gui version alias:aliasname
            now:the lapse second from 1970-1-1 0:0:0 to device current time.
            Tz:device current time zone setting and the number of seconds deviation of GMT T  
            alarm_status: device current alarm status,
                0  no alarm;  1  motion detection alarm;  2  input alarm;  3  voice detection alarm
            ......
        '''
        return self.execute_command('get_status', callback = callback)
    
    def reboot(self, callback = None):
        ''' Reboots device '''
        return self.execute_command('reboot', callback=callback)



    # *************** AV Settings  ******************
    def get_camera_params(self, callback = None):
        '''
        resolution: 8 qvga;  32 vga
        brightness: 0~255
        contrast:   0~6
        mode:       0 50hz;  1 60hz;  2 outdoor
        flip:       0 initial;  1 vertical rotate;  2 horizontal rotate;  3 is vertical + horizontal rotate
        '''
        return self.execute_command('get_camera_params', None, callback = callback)

    def set_camera_params(self, param, value, callback = None): 
        '''
        /camera_control.cgi?param=&value=[&user=&pwd=&next_url=]
        
        0: resolution: 2 qqvga; 8 qvga;  32 vga
        1: brightness: 0~255
        2: contrast:   0~6
        3: mode:       0 50hz;  1 60hz;  2 outdoor5
        5: flip:       0 initial;  1 vertical rotate;  2 horizontal rotate;  3 is vertical + horizontal rotate
        '''
        params = {'value': value,
                  'param': param}
        return self.execute_command('camera_control', params, callback = callback)
    
    def get_mirror_and_flip_setting(self, callback = None):
        response_ok, response = self.get_camera_params()
        if response['flip'] == '0':
            return response_ok, {'isMirror': '0', 'isFlip': '0'}
        elif response['flip'] == '1':
            return response_ok, {'isMirror': '0', 'isFlip': '1'}
        elif response['flip'] == '2':
            return response_ok, {'isMirror': '1', 'isFlip': '0'}
        elif response['flip'] == '3':
            return response_ok, {'isMirror': '1', 'isFlip': '1'}

    def mirror_video(self, is_mirror = None, callback = None):
        '''
        is_mirror: 0 not mirror; 1 mirror
        '''
        response_ok, response = self.get_mirror_and_flip_setting()
        print response
        if is_mirror == None:
            is_mirror = response['isMirror']       
        value = ''
        if is_mirror == '0':
            if response['isFlip'] == '0':
                value = '2'
            else:
                value = '3' 
        elif is_mirror == '1':
            if response['isFlip'] == '0':
                value = '0'
            else:
                value = '1'
        return self.set_camera_params('5', value)

    def flip_video(self, is_flip = None, callback = None):
        '''
        is_flip: 0 Not flip;  1 Flip
        '''
        response_ok, response = self.get_mirror_and_flip_setting()
        if is_flip == None:
            is_flip = response['isFlip']
        value = ''
        if is_flip == '0':
            if response['isMirror'] == '0':
                value = '1'
            else:
                value = '3'
        elif is_flip == '1':
            if response['isMirror'] == '0':
                value = '0'
            else:
                value = '2'
        return self.set_camera_params('5', value)
        
        
    def get_misc(self, callback = None):
        ''' See set_misc() '''
        return self.execute_command('get_misc', None, callback = callback)

    def set_misc(self, params, callback = None):
        '''
        led_mode:                   0 mode1;    1 mode2;    2 LED Off
                            led_mode=0 - the green led blinks only once connected.
                            led_mode=1 - the green led blinks while searching for a connection and when connected.
                            led_mode=2 - the green led is always off.
        ptz_center_onstart:         0 disable;  1 enable
                            ptz_center_onstart=0  the camera won't auto-rotate any more when restarting, so you won't need to re-position it any longer upon rebooting. 
        ptz_auto_patrol_interval:   0 none;     1 auto
        ptz_auto_patrol_type:       0 no rotate;    1 horizontal;   2 vertical;     3 horizontal+vertical 
        ptz_patrol_h_rounds:        0 infinite;     n Number of rounds
        ptz_patrol_v_rounds:        0 infinite;     n Number of rounds
        ptz_patrol_rate:            0-100;      0 slowest, 100 fastest
        ptz_patrol_up_rate:         0-100;      0 slowest, 100 fastest
        ptz_patrol_down_rate:       0-100;      0 slowest, 100 fastest
        ptz_patrol_left_rate:       0-100;      0 slowest, 100 fastest
        ptz_patrol_right_rate:      0-100;      0 slowest, 100 fastest
        ptz_disable_preset:         0 no;       1 yes (after reboot)  
        ptz_preset_onstart:         0 disable;  1 enabled
        
            http://[ipcam]/set_misc.cgi?ptz_auto_patrol_interval=30
            This function is currently not implemented in the user interface and  instructs the camera  to start a patrol at a defined interval, here 30 seconds.
            The patrol type is defined by this other command:  
            http://[ipcam]/set_misc.cgi?ptz_auto_patrol_type=1
            Possible values: 0: None; 1: horizontal; 2: vertical; 3: Horizontal + Vertical 

            http://[ipcam]/set_misc.cgi?ptz_patrol_rate= 20
            The value provided will defined how fast the camera will rotate on patrol, here 20 is the default.
            Fastest speed = 0. Slowest speed = 100.
        '''
        return self.execute_command('set_misc', params, callback = callback)

    def set_ir_on(self, callback = None): # NEED VERIFICATION
        #params = {'led_mode': '0'}
	#return self.set_misc(params, callback)
        return self.decoder_control(95)
    
    def set_ir_off(self, callback = None): # NEED VERIFICATION
	#params = {'led_mode': '2'}
	#return self.set_misc(params, callback)
        return self.decoder_control(94)

    def get_ir_config(self, callback = None): # NOT GOOD
	'''
        Get IR Config
            mode:  0  Auto
                   1  Manual
        '''
	response_ok, data = self.get_misc()
	params = {}
	if data[1]['led_mode'] == '0':
            params['mode'] = '1'
        else:
            params['mode'] = '0'
	return response_ok, params


    def set_ir_config(self, mode, callback=None): # NEED VERIFICATION
	'''
        Set IR Config
            mode:  0  Auto
                   1  Manual
        '''
	params = {}
	if mode == '0':
            params['mode'] = '1'
        else:
            params['mode'] = '0'
	return set_misc(params, callback)


    def get_dev_name(self, callback=None): # NEED VERIFICATION
        '''
        Get camera name.
        '''
        return self.execute_command('getDevName', callback=callback)

    def set_dev_name(self, devname, callback=None): # NEED VERIFICATION
        '''
        Set camera name
        '''
        params = {'devName': devname.encode('gbk')}
        return self.execute_command('setDevName', params, callback=callback)

    def set_pwr_freq(self, mode, callback=None): # NEED VERIFICATION
        '''
        Set power frequency of sensor
        mode:
            0  60HZ
            1  50Hz
            2  Outdoor
        '''
        params = {'freq': mode}
        return self.execute_command('setPwrFreq', params, callback=callback)





    def get_params(self, callback = None):  # NEED VERIFICATION
        '''
        re
        '''
        return self.execute_command('get_params', None, callback = callback)
  



    # *************** PTZ Control *******************

    def decoder_control(self, command, onestep = None, degree = None, callback = None): ### NEW FUNCTION ###
        '''
        /decoder_control.cgi?command=[&onestep=&degree=&user=&pwd=&next_url=

        onestep=1: indicate the PTZ control is one step then stop, it is only for camera 
                    with ptz originally and it is only for up, down,left and right.

        Value   485port extra connection   Internal motor
            0 up
            1 stop up 
            2 down  
            3 stop down
            4 right  
            5 stop right
            6 left   
            7 stop left   
            16 Zoom close
            17 Stop zoom close
            18 Zoom far
            19 Stop zoom far
            20 Auto patrol
            21 Stop auto patrol
            25 center
            26 Up & down patrol
            27 Stop up & down  patrol
            28 Left & right patrol
            29 Left & right  patrol
            
            30 Set preset1 
            31 Go to preset1
            ..
            60 Set preset 16 Set preset 16
            61 Go to preset 16 Go to preset 16
                        
            90 Upper right
            91 Upper left
            92 Down right
            93 Down left
            94 IR LED OFF (IO high?)
            95 IR LED ON  (IO low?)
            255  Motor test mode 
        '''
        params = {'command': command}
        if onestep != None:
            params['onestep'] = onestep
            if degree != None:
                params['degree'] = degree
            else:
                params['degree'] = 3
        return self.execute_command('decoder_control', params, callback=callback)

    def ptz_set_sensitivity(self, degree):
        self.degree = degree
        return float(self.degree)
    
    def ptz_move_up(self, callback = None):
        return self.decoder_control(0, 1, self.degree)

    def ptz_move_down(self, callback = None):
        return self.decoder_control(2, 1, self.degree)

    def ptz_move_left(self, callback = None):
        return self.decoder_control(6, 1, self.degree)

    def ptz_move_right(self, callback = None):
        return self.decoder_control(4, 1, self.degree)

    def ptz_move_top_left(self, callback = None):
        return self.decoder_control(91, 1, self.degree)

    def ptz_move_top_right(self, callback = None):
        return self.decoder_control(90, 1, self.degree)

    def ptz_move_bottom_left(self, callback = None):
        return self.decoder_control(93, 1, self.degree)

    def ptz_move_bottom_right(self, callback = None):
        return self.decoder_control(92, 1, self.degree)

    def ptz_stop_run(self, callback = None):
        return None

    def get_ptz_speed(self, callback = None):
        return None

    def set_ptz_speed(self, speed, callback = None):
        return None

    def ptz_zoom_in(self, callback = None):
        return self.decoder_control(16, 1, self.degree)

    def ptz_zoom_out(self, callback = None):
        return self.decoder_control(18, 1, self.degree)

    def ptz_zoom_stop(self, callback = None):
        return None

    def get_ptz_zoom_speed(self, callback = None):
        return None

    def set_ptz_zoom_speed(self, speed, callback = None):
        return None



    
    def ptz_reset(self, callback = None):
        '''
        Reset PT to default position.
        '''
        return self.decoder_control(25)

    def ptz_home_location(self, mode, callback = None): # NEED VERIFICATION
        '''
        Reset PT to home position.
            mode:  0 Return if add-on default preset point exists or not
                   1 Go to add-on default preset if it exists and no action if it doesn't
                   2 Return if add-on default preset point exists or not, and go to point if it does or camera default if it doesn't
                   3 Reset to camera default location                   
        '''
        mode = 3
        self.set_misc({'ptz_disable_preset': '0'})
        self.get_misc()
        
        self.ptz_goto_preset()
        return mode
        if mode < 3:
            response_code, response = self.ptz_get_preset()
            try:
                qty = int(response.get('cnt'))
                for x in range(4, qty):
                    point = response.get('point%d' %x)
                    if 'surveillanceroom_default' in point:
                        if mode == 0:
                            return True
                        else:
                            return True, self.ptz_goto_preset('surveillanceroom_default')

            except:
                pass

            if mode == 2:
                self.ptz_reset()
            return False
            
        #return self.ptz_reset()
                    
    def ptz_get_preset(self, callback=None): # NEED VERIFICATION
        '''
        Get presets.
            cnt:      Current preset point count 
            pointN:   The name of point N 
        '''
        return self.execute_command('getPTZPresetPointList', callback=callback)
    
    def ptz_goto_preset(self, callback=None): # NEED VERIFICATION
        '''
        Move to preset.
        4 points are default:  LeftMost\RightMost\TopMost\BottomMost 
        '''
        return self.decoder_control(31)

    def ptz_add_preset(self, name = None, callback=None):
        return self.decoder_control(30)

    def ptz_delete_preset(self, name = None, callback=None): # NEED VERIFICATION
        '''
        Delete a preset point from the preset point list.
        '''
        if name == None:
            name = 'surveillanceroom_default'
        params = {'name': name}
        return self.execute_command('ptzDeletePresetPoint', params, callback=callback)



    def get_ptz_selftestmode(self, callback=None): # NEED VERIFICATION
        '''
        Get the selftest mode of PTZ
        '''
        return self.execute_command('getPTZSelfTestMode', callback=callback)

    def set_ptz_selftestmode(self, mode=0, callback=None): # NEED VERIFICATION
        '''
        Set the selftest mode of PTZ
        mode = 0: No selftest
        mode = 1: Normal selftest
        mode = 1: After normal selftest, then goto presetpoint-appointed
        '''
        return self.execute_command('setPTZSelfTestMode',
                                    {'mode':mode},
                                    callback=callback
                                   )


    
    # *************** Alarm Function *******************    
    def is_alarm_active(self, motion_enabled, sound_enabled):
        '''
        Returns the state of the alarm on the camera.
        '''
        success_code, response = self.get_dev_state()
        
        if success_code == 0:
            
            if int(response.get('alarm_status')) == 1 and motion_enabled:
                return success_code, True, 'Motion Alarm Detect'

            if int(response.get('alarm_status')) == 3 and sound_enabled:
                return success_code, True, 'Sound Alarm Detect'
        
        return success_code, False, None


    

    def get_sound_detect_config(self, callback=None): # NEED VERIFICATION
	'''
        Get sound detect config
        '''
	return self.execute_command('getAudioAlarmConfig', callback=callback)
		
    def set_sound_detect_config(self, params, callback=None): # NEED VERIFICATION
        '''
        Set sound detect config
        '''
        return self.execute_command('setAudioAlarmConfig', params, callback=callback)
		
    def set_sound_detection(self, enabled=1): # NEED VERIFICATION
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        current_config['isEnable'] = enabled
        self.set_sound_detect_config(current_config)

    def enable_sound_detection(self): # NEED VERIFICATION
        '''
        Enable sound detection
        '''
        self.set_sound_detection(1)

    def disable_sound_detection(self): # NEED VERIFICATION
        '''
        disable sound detection
        '''
        self.set_sound_detection(0)

    def get_sound_sensitivity(self): # NEED VERIFICATION
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        return current_config['sensitivity']
    
    def set_sound_sensitivity(self, sensitivity): # NEED VERIFICATION
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        current_config['sensitivity'] = sensitivity
        self.set_sound_detect_config(current_config)

    def get_sound_triggerinterval(self): # NEED VERIFICATION
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        return current_config['triggerInterval']
    
    def set_sound_triggerinterval(self, triggerInterval): # NEED VERIFICATION
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        current_config['triggerInterval'] = triggerInterval
        self.set_sound_detect_config(current_config)

        
	
	
    def get_motion_detect_config(self, callback=None): # NEED VERIFICATION
        '''
        Get motion detect config
        '''
        return self.execute_command('getMotionDetectConfig', callback=callback)
 
    def set_motion_detect_config(self, params, callback=None):
        '''
        Set motion detect config
        '''
        return self.execute_command('setMotionDetectConfig', params, callback=callback)

    def set_motion_detection(self, enabled=1): # NEED VERIFICATION
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        current_config['isEnable'] = enabled
        self.set_motion_detect_config(current_config)

    def enable_motion_detection(self): # NEED VERIFICATION
        '''
        Enable motion detection
        '''
        self.set_motion_detection(1)

    def disable_motion_detection(self): # NEED VERIFICATION
        '''
        disable motion detection
        '''
        self.set_motion_detection(0)

    def get_motion_sensitivity(self): # NEED VERIFICATION
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        return current_config['sensitivity']
    
    def set_motion_sensitivity(self, sensitivity): # NEED VERIFICATION
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        current_config['sensitivity'] = sensitivity
        self.set_motion_detect_config(current_config)

    def get_motion_triggerinterval(self): # NEED VERIFICATION
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        return current_config['triggerInterval']
    
    def set_motion_triggerinterval(self, triggerInterval): # NEED VERIFICATION
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        current_config['triggerInterval'] = triggerInterval
        self.set_motion_detect_config(current_config)

    

   
