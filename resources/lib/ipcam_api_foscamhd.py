"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is to exploit Foscam HD Cameras, ie FI9821W/P/HD816W/P.
"""

import urllib, sys
import xml.etree.ElementTree as ET
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
    def __init__(self, code ):
        super(FoscamError, self).__init__()
        self.code = int(code)

    def __str__(self):
        return  'ErrorCode: %s' % self.code

class FoscamCamera(object):
    '''A python implementation of the foscam HD816W'''

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
	_videoUrl = "rtsp://{0}:{1}@{2}/videoMain".format(self.usr, self.pwd, self.url)
        return _videoUrl

    @property
    def video_sub_url(self):
	_videoSubUrl = "rtsp://{0}:{1}@{2}/videoSub".format(self.usr, self.pwd, self.url)
        return _videoSubUrl

    @property
    def mjpeg_url(self):
	_mjpegUrl = "http://{0}/cgi-bin/CGIStream.cgi?cmd={{cmd}}&usr={1}&pwd={2}&".format(self.url, self.usr, self.pwd)
        return _mjpegUrl.format(cmd = 'GetMJStream')   #MJPEG stream is VGA resolution @ 15fps

    @property
    def snapshot_url(self):
	_snapshotUrl = "http://{0}/cgi-bin/CGIProxy.fcgi?cmd={{cmd}}&usr={1}&pwd={2}&".format(self.url, self.usr, self.pwd)
        return _snapshotUrl.format(cmd = 'snapPicture2')

    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):		
	return None
    
		
    def send_command(self, cmd, params=None):
        '''
        Send command to foscam.
        '''
        paramstr = ''
        if params:
            paramstr = urllib.urlencode(params)
            paramstr = '&' + paramstr if paramstr else ''
        cmdurl = 'http://%s/cgi-bin/CGIProxy.fcgi?usr=%s&pwd=%s&cmd=%s%s' % (
                                                                  self.url,
                                                                  self.usr,
                                                                  self.pwd,
                                                                  cmd,
                                                                  paramstr,
                                                                  )

        # Parse parameters from response string.
        if self.verbose:
            utils.log(4, 'Camera %s :: Send Foscam command: %s' %(self.number, cmdurl))
        try:
            raw_string = ''
            raw_string = urllib.urlopen(cmdurl).read()
            root = ET.fromstring(raw_string)
        except:
            if self.verbose:
                utils.log(3, 'Camera %s :: Foscam exception: %s' %(self.number, raw_string))
            return ERROR_FOSCAM_UNAVAILABLE, None
        code = ERROR_FOSCAM_UNKNOWN
        params = dict()
        
        if utils._atleast_python27:      #Check added for compatibility with Mac/python2.6 kodi builds
            for child in root.iter():
                if child.tag == 'result':
                    code = int(child.text)

                elif child.tag != 'CGI_Result':
                    params[child.tag] = child.text

        else:
            for child in root.getiterator():
                if child.tag == 'result':
                    code = int(child.text)

                elif child.tag != 'CGI_Result':
                    params[child.tag] = child.text

        if self.verbose:
            utils.log(4, 'Camera %s :: Received Foscam response: %s, %s' %(self.number, code, params))
        return code, params

    def execute_command(self, cmd, params=None, callback=None):
        '''
        Execute a command and return a parsed response.
        '''
        def execute_with_callbacks(cmd, params=None, callback=None):
            code, params = self.send_command(cmd, params)
            if callback:
                callback(code, params)
            return code, params

        if self.daemon:
            t = Thread(target=execute_with_callbacks,
                    args=(cmd, ), kwargs={'params':params, 'callback':callback})
            t.daemon = True
            t.start()
        else:
            return execute_with_callbacks(cmd, params, callback)

        
    # *************** Device manager *******************
    def get_dev_state(self, callback=None):
        '''
        Get all device state
        cmd: getDevState
        return args:
            ......
            IOAlarm      0   Disabled;  1 No Alarm;  2 Detect Alarm
            motionDetectAlarm    0   Disabled;  1 No Alarm;  2 Detect Alarm
            soundAlarm   0   Disabled;  1 No Alarm;  2 Detect Alarm
            record:      0   Not in recording; 1 Recording
            sdState:     0   No sd card; 1 Sd card OK; 2 SD card read only
            sdFreeSpace: Free space of sd card by unit of k
            sdTotalSpace: Total space of sd card by unit of k
            infraLedState    0  OFF;  1  ON
            ......
        '''
        return self.execute_command('getDevState', callback=callback)

    def reboot(self, callback=None):

        return self.execute_command('rebootSystem', callback=callback)

    def set_system_time(self, time_source, ntp_server, date_format,
                        time_format, time_zone, is_dst, dst, year,
                        mon, day, hour, minute, sec, callback=None):
        '''
        Set systeim time
        '''
        if ntp_server not in ['time.nist.gov',
                              'time.kriss.re.kr',
                              'time.windows.com',
                              'time.nuri.net',
                             ]:
            raise ValueError('Unsupported ntpServer')

        params = {'timeSource': time_source,
                  'ntpServer' : ntp_server,
                  'dateFormat': date_format,
                  'timeFormat': time_format,
                  'timeZone'  : time_zone,
                  'isDst'     : is_dst,
                  'dst'       : dst,
                  'year'      : year,
                  'mon'       : mon,
                  'day'       : day,
                  'hour'      : hour,
                  'minute'    : minute,
                  'sec'       : sec
                 }

        return self.execute_command('setSystemTime', params, callback=callback)

    def get_system_time(self, callback=None):
        '''
        Get system time.
        '''
        return self.execute_command('getSystemTime', callback=callback)

    def get_dev_name(self, callback=None):
        '''
        Get camera name.
        '''
        return self.execute_command('getDevName', callback=callback)

    def set_dev_name(self, devname, callback=None):
        '''
        Set camera name
        '''
        params = {'devName': devname.encode('gbk')}
        return self.execute_command('setDevName', params, callback=callback)

    def set_pwr_freq(self, mode, callback=None):
        '''
        Set power frequency of sensor
        mode:
            0  60HZ
            1  50Hz
            2  Outdoor
        '''
        params = {'freq': mode}
        return self.execute_command('setPwrFreq', params, callback=callback)


    def get_osd_setting(self, callback=None):
        '''
        Gets the OSD setting
            ......
            isEnableTimeStamp:  Time stamp will display on screen or not
            isEnableDevName:    Camera name will display on screen or not
            dispPos:            OSD display position, currently can only be 0
            isEnableOSDMask:    Is OSD mask effective
            ......
        '''
        return self.execute_command('getOSDSetting ', callback=callback)

    def set_osd_setting(self, params, callback=None):
        '''
        Sets the OSD setting  -- CURRENTLY NOT FUNCTIONAL AS A PYTHON FUNCTION UNTIL PARAMETERS ARE SET
            ......
            isEnableTimeStamp:  Time stamp will display on screen or not
            isEnableDevName:    Camera name will display on screen or not
            dispPos:            OSD display position, currently can only be 0
            isEnableOSDMask:    Is OSD mask effective
            ......
        '''
        params = {}
        return self.execute_command('setOSDSetting', params, callback=callback)
    

    def set_ir_on(self, callback=None):
	'''
        Turn on the IR LED
        '''
	return self.execute_command('openInfraLed', callback=callback)

    def set_ir_off(self, callback=None):
	'''
        Turn off the IR LED
        '''
	return self.execute_command('closeInfraLed', callback=callback)

    def get_ir_config(self, callback=None):
	'''
        Get IR Config
            mode:  0  Auto
                   1  Manual
        '''
	return self.execute_command('getInfraLedConfig', callback=callback)


    def set_ir_config(self, mode, callback=None):
	'''
        Set IR Config
            mode:  0  Auto
                   1  Manual
        '''
	params = {'mode': mode}
	return self.execute_command('setInfraLedConfig', params, callback=callback)

		
    # *************** AV Settings  ******************
    def set_snapshot_config(self, quality, callback=None):
	'''
        Set snapshot config
            snapPicQuality: 0 Low quality
                            1 Normal quality
                            2 High quality
            saveLocation:   0 Save to sd card
                            1 Not in use now
                            2 Upload to FTP
        '''
	response_ok, response = self.get_snapshot_config()
	save_location = response.get('saveLocation')
	
	params = {'snapPicQuality': quality,
                  'saveLocation': save_location}
                    
	self.execute_command('setSnapConfig', params, callback=callback)
		
    def get_snapshot_config(self, callback=None):
	'''
        Get snapshot config:
            snapPicQuality: 0 Low quality
                            1 Normal quality
                            2 High quality
            saveLocation:   0 Save to sd card
                            1 Not in use now
                            2 Upload to FTP
        '''
	self.execute_command('getSnapConfig', callback=callback)

    def enable_mjpeg(self):
        '''
        Set the sub stream type to Motion jpeg.
        '''
        self.set_sub_video_stream_type(1)

    def disable_mjpeg(self):
        '''
        Set the sub stream type to Motion jpeg.
        '''
        self.set_sub_video_stream_type(0)
		
		
    def get_sub_video_stream_type(self, callback=None):
        '''
        Get the stream type of sub stream.
        '''
        return self.execute_command('getSubVideoStreamType', callback=callback)

    def set_sub_video_stream_type(self, format, callback=None):
        '''
        Set the stream fromat of sub stream.
        Supported format: (1) H264 : 0
                          (2) MotionJpeg 1
        '''
        params = {'format': format}
        return self.execute_command('setSubVideoStreamType',
                                        params, callback=callback)

    def set_sub_stream_format(self, format, callback=None):
        '''
        Set the stream fromat of sub stream
            0-3
        '''
        params = {'format': format}
        return self.execute_command('setSubStreamFormat',
                                        params, callback=callback)

    def get_main_video_stream_type(self, callback=None):
        '''
        Get the stream type of main stream
        '''
        return self.execute_command('getMainVideoStreamType', callback=callback)

    def set_main_video_stream_type(self, streamtype, callback=None):
        '''
        Set the stream type of main stream
            0-3
        '''
        params = {'streamType': streamtype}
        return self.execute_command('setMainVideoStreamType',
                                        params, callback=callback)

    def get_video_stream_param(self, callback=None):
        '''
        Get video stream param
        '''
        return self.execute_command('getVideoStreamParam', callback=callback)

    def set_video_stream_param(self, streamtype, resolution, bitrate,
            framerate, gop, isvbr, callback=None):
        '''
        Set the video stream param of stream N
        streamtype(0~3): Stream N.
        resolution(0~4): 0 720P,
                         1 VGA(640*480),
                         2 VGA(640*360),
                         3 QVGA(320*240),
                         4 QVGA(320*180).
        bitrate: Bit rate of stream type N(20480~2097152).
        framerate: Frame rate of stream type N.
        GOP: P frames between 1 frame of stream type N.
             The suggest value is: X * framerate.
        isvbr: 0(Not in use currently), 1(In use).
        '''
        params = {'streamType': streamtype,
                  'resolution': resolution,
                  'bitRate'   : bitrate,
                  'frameRate' : framerate,
                  'GOP'       : gop,
                  'isVBR'     : isvbr
                 }
        return self.execute_command('setVideoStreamParam',
                                    params, callback=callback)

    def mirror_video(self, is_mirror=None, callback=None):
        '''
        Mirror video
        ``is_mirror``: 0 not mirror, 1 mirror
        '''
        if is_mirror == None:
            response_ok, response = self.get_mirror_and_flip_setting()
            
            is_mirror = response.get('isMirror')
            if is_mirror == '0':
                is_mirror = '1'
            else:
                is_mirror = '0'
            
        params = {'isMirror': is_mirror}
        return self.execute_command('mirrorVideo', params, callback=callback)

    def flip_video(self, is_flip=None, callback=None):
        '''
        Flip video
        ``is_flip``: 0 Not flip, 1 Flip
        '''
        if is_flip == None:
            response_ok, response = self.get_mirror_and_flip_setting()
            
            is_flip = response.get('isFlip')
            if is_flip == '0':
                is_flip = '1'
            else:
                is_flip = '0'
            
        params = {'isFlip': is_flip }
        return self.execute_command('flipVideo', params, callback=callback)

    def get_mirror_and_flip_setting(self, callback=None):
        
        return self.execute_command('getMirrorAndFlipSetting', None, callback=callback)





    # *************** PTZ Control *******************

    def ptz_move_up(self, callback=None):
        '''
        Move up
        '''
        return self.execute_command('ptzMoveUp', callback=callback)

    def ptz_move_down(self, callback=None):
        '''
        Move down
        '''
        return self.execute_command('ptzMoveDown', callback=callback)

    def ptz_move_left(self, callback=None):
        '''
        Move left
        '''
        return self.execute_command('ptzMoveLeft', callback=callback)

    def ptz_move_right(self, callback=None):
        '''
        Move right.
        '''
        return self.execute_command('ptzMoveRight', callback=callback)

    def ptz_move_top_left(self, callback=None):
        '''
        Move to top left.
        '''
        return self.execute_command('ptzMoveTopLeft', callback=callback)

    def ptz_move_top_right(self, callback=None):
        '''
        Move to top right.
        '''
        return self.execute_command('ptzMoveTopRight', callback=callback)

    def ptz_move_bottom_left(self, callback=None):
        '''
        Move to bottom left.
        '''
        return self.execute_command('ptzMoveBottomLeft', callback=callback)

    def ptz_move_bottom_right(self, callback=None):
        '''
        Move to bottom right.
        '''
        return self.execute_command('ptzMoveBottomRight', callback=callback)

    def ptz_stop_run(self, callback=None):
        '''
        Stop run PT
        '''
        return self.execute_command('ptzStopRun', callback=callback)

    def ptz_reset(self, callback=None):
        '''
        Reset PT to default position.
        '''
        
        return self.execute_command('ptzReset', callback=callback)

    def ptz_home_location(self, mode, callback=None):
        '''
        Reset PT to home position.
            mode:  0 Return if add-on default preset point exists or not
                   1 Go to add-on default preset if it exists and no action if it doesn't
                   2 Return if add-on default preset point exists or not, and go to point if it does or camera default if it doesn't
                   3 Reset to camera default location                   
        '''

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
            
        return self.ptz_reset()
                    
    def ptz_get_preset(self, callback=None):
        '''
        Get presets.
            cnt:      Current preset point count 
            pointN:   The name of point N 
        '''
        return self.execute_command('getPTZPresetPointList', callback=callback)
    
    def ptz_goto_preset(self, name, callback=None):
        '''
        Move to preset.
        4 points are default:  LeftMost\RightMost\TopMost\BottomMost 
        '''
        params = {'name': name}
        return self.execute_command('ptzGotoPresetPoint', params, callback=callback)

    def ptz_add_preset(self, name = None, callback=None):
        '''
        Sets current position as preset point.
        - Only 16 presets in list, with 4 default.
        '''
        if name == None:
            name = 'surveillanceroom_default'
        params = {'name': name}
        return self.execute_command('ptzAddPresetPoint', params, callback=callback)

    def ptz_delete_preset(self, name = None, callback=None):
        '''
        Delete a preset point from the preset point list.
        '''
        if name == None:
            name = 'surveillanceroom_default'
        params = {'name': name}
        return self.execute_command('ptzDeletePresetPoint', params, callback=callback)

    def get_ptz_speed(self, callback=None):
        '''
        Get the speed of PT
        '''
        return self.execute_command('getPTZSpeed', callback=callback)

    def set_ptz_speed(self, speed, callback=None):
        '''
        Set the speed of PT
            speed:  0  Very slow
                    1  Slow
                    2  Normal speed
                    3  Fast
                    4  Very fast 
        '''
        return self.execute_command('setPTZSpeed', {'speed':speed},
                                         callback=callback)

    def get_ptz_selftestmode(self, callback=None):
        '''
        Get the selftest mode of PTZ
        '''
        return self.execute_command('getPTZSelfTestMode', callback=callback)

    def set_ptz_selftestmode(self, mode=0, callback=None):
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

    def ptz_zoom_in(self, callback=None):
        '''
        Zoom In
        '''
        return self.execute_command('zoomIn', callback=callback)

    def ptz_zoom_out(self, callback=None):
        '''
        Zoom Out
        '''
        return self.execute_command('zoomOut', callback=callback)

    def ptz_zoom_stop(self, callback=None):
        '''
        Zoom Stop
        '''
        return self.execute_command('zoomStop', callback=callback)

    def get_ptz_zoom_speed(self, callback=None):
        '''
        Get Zoom Speed
            speed:  0 slow
                    1 normal
                    2 fast
        '''
        return self.execute_command('getZoomSpeed', callback=callback)

    def set_ptz_zoom_speed(self, speed, callback=None):
        '''
        Set Zoom Speed
            speed:  0 slow
                    1 normal
                    2 fast
        '''
        params = {'speed': speed}
        return self.execute_command('setZoomSpeed', params, callback=callback)


    
    # *************** Alarm Function *******************

    def is_alarm_active(self, motion_enabled, sound_enabled):
        '''
        Returns the state of the alarm on the camera.
        '''
        alarmActive = False
        success_code, response = self.get_dev_state()
        
        if success_code == 0:
            
            for alarm, enabled in (('motionDetect', motion_enabled), ('sound', sound_enabled)):
                
                if enabled:
                    param = "{0}Alarm".format(alarm)
                    
                    if response[param] == '2':
                        alarmActive = True
                        break
                    
            return success_code, alarmActive, alarm
        
        return success_code, False, None

    def get_sound_detect_config(self, callback=None):
	'''
        Get sound detect config
        '''
	return self.execute_command('getAudioAlarmConfig', callback=callback)
		
    def set_sound_detect_config(self, params, callback=None):
        '''
        Set sound detect config
        '''
        return self.execute_command('setAudioAlarmConfig', params, callback=callback)
		
    def set_sound_detection(self, enabled=1):
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        current_config['isEnable'] = enabled
        self.set_sound_detect_config(current_config)

    def enable_sound_detection(self):
        '''
        Enable sound detection
        '''
        self.set_sound_detection(1)

    def disable_sound_detection(self):
        '''
        disable sound detection
        '''
        self.set_sound_detection(0)

    def get_sound_sensitivity(self):
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        return current_config['sensitivity']
    
    def set_sound_sensitivity(self, sensitivity):
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        current_config['sensitivity'] = sensitivity
        self.set_sound_detect_config(current_config)

    def get_sound_triggerinterval(self):
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        return current_config['triggerInterval']
    
    def set_sound_triggerinterval(self, triggerInterval):
        '''
        Get the current config and set the sound detection on or off
        '''
        result, current_config = self.get_sound_detect_config()
        current_config['triggerInterval'] = triggerInterval
        self.set_sound_detect_config(current_config)

        
	
	
    def get_motion_detect_config(self, callback=None):
        '''
        Get motion detect config
        '''
        return self.execute_command('getMotionDetectConfig', callback=callback)
 
    def set_motion_detect_config(self, params, callback=None):
        '''
        Set motion detect config
        '''
        return self.execute_command('setMotionDetectConfig', params, callback=callback)

    def set_motion_detection(self, enabled=1):
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        current_config['isEnable'] = enabled
        self.set_motion_detect_config(current_config)

    def enable_motion_detection(self):
        '''
        Enable motion detection
        '''
        self.set_motion_detection(1)

    def disable_motion_detection(self):
        '''
        disable motion detection
        '''
        self.set_motion_detection(0)

    def get_motion_sensitivity(self):
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        return current_config['sensitivity']
    
    def set_motion_sensitivity(self, sensitivity):
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        current_config['sensitivity'] = sensitivity
        self.set_motion_detect_config(current_config)

    def get_motion_triggerinterval(self):
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        return current_config['triggerInterval']
    
    def set_motion_triggerinterval(self, triggerInterval):
        '''
        Get the current config and set the motion detection on or off
        '''
        result, current_config = self.get_motion_detect_config()
        current_config['triggerInterval'] = triggerInterval
        self.set_motion_detect_config(current_config)

    

class FoscamCameraOverride(FoscamCamera):
    def __init__(self, camera_settings, daemon = False, verbose = True):
        super(FoscamCamera, self).init(camera_settings, daemon = False, verbose = True)
        self.camera_number = camera_settings[0]
        #self.host = camera_settings[1]
        #self.port = camera_settings[2]
        #self.usr = camera_settings[3]
        #self.pwd = camera_settings[4]
        
    
    @property
    def video_url(self):
        _videoUrl = settings.getSetting('stream_url', self.camera_number)
        if _videoUrl == '':
            _videoUrl = "rtsp://{0}:{1}@{2}/videoMain".format(self.usr, self.pwd, self.url)
        return _videoUrl

    @property
    def mjpeg_url(self):
        _mjpegUrl = settings.getSetting('mjpeg_url', self.camera_number)
        if mjpegUrl == '':
            _mjpegUrl = "http://{0}/cgi-bin/CGIStream.cgi?cmd={GetMJStream}&usr={1}&pwd={2}&".format(self.url, self.usr, self.pwd)
        return _mjpegUrl

    @property
    def snapshot_url(self):
        _snapshotUrl = settings.getSetting('snapshot_url', self.camera_number)
        if _snapshotUrl == '':
            _snapshotUrl = "http://{0}/cgi-bin/CGIProxy.fcgi?cmd={snapPicture2}&usr={1}&pwd={2}&".format(self.url, self.usr, self.pwd)
        return _snapshotUrl
