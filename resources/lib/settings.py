"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to obtain add-on settings and camera settings
"""

import xbmc, xbmcgui, xbmcaddon
import foscam2, utils

__addon__ = xbmcaddon.Addon()

'''
# --> This should exist on all modules that log
import inspect
stck = inspect.stack()
frm = stck[1]
mod = inspect.getmodule(frm[0])
mod1 = (str(mod).split("'"))
mod2 = mod1[len(mod1)-2]
mod3 = mod2.split(".")
mod4 = mod3[len(mod3)-2]
mod5 = mod4.split("\\")
mod6 = mod5[len(mod5)-1]

__logid__ = ('SETTINGS_{0}').format(mod6.upper())

from logging import log
# --
'''

INVALID_PASSWORD_CHARS = ('{', '}', ':', ';', '!', '?', '@', '\\', '/')
INVALID_USER_CHARS = ('@',)


### Basic Addon Setting Controls ###

def refreshAddonSettings():
    global __addon__
    __addon__ = xbmcaddon.Addon()
    
def setSetting(setting, camera_number='', value=''):
    utils.log(2, 'SETTINGS :: %s%s Value Set as - %s' %(setting, camera_number, value))
    return __addon__.setSetting(setting + camera_number, value)
    
def getSetting(setting, camera_number=''):
    return __addon__.getSetting(setting + camera_number)

def getSetting_int(setting, camera_number=''):
    return int(__addon__.getSetting(setting + camera_number))

def getSetting_bool(setting, camera_number=''):
    if 'true' in __addon__.getSetting(setting + camera_number):
        return True
    else:
        return False

def getSetting_float(setting, camera_number=''):
    return float(__addon__.getSetting(setting + camera_number))


### Specialize setting Functions ###

def enabled_camera(camera_number):
    return getSetting_bool('enabled', camera_number)

def enabled_preview(camera_number):
    if enabled_camera(camera_number):
        return getSetting_bool('enabled_preview', camera_number)
    else:
        return False
    
def atLeastOneCamera(cameras_to_check="1234"):
    for camera_number in cameras_to_check:
        if enabled_camera(camera_number):
            return True
    return False

def getAllEnabledCameras(monitor):
    enabled_cameras = []
    for camera_number in "1234":
        
        enabled = enabled_camera(camera_number)
        connected = monitor.cache_test_result(camera_number)
        
        if enabled and not connected:
            test_settings = getBasicSettings(camera_number, monitor, useCache=False)
            connected = monitor.cache_test_result(camera_number)

        if enabled and connected:
            enabled_cameras.append(camera_number)
            
    return enabled_cameras

def getCameraType(camera_number):
    return getSetting_int('type', camera_number)

def getSupportedAlarms(camera_number):
    return getSetting_int('alarm', camera_number)
    
def getEnabledAlarms(camera_number):
    motion_enabled = False
    sound_enabled = False
    
    supported = getSupportedAlarms(camera_number)

    if supported > 0:
        motion_enabled = getSetting_bool('motion', camera_number)
        
    if supported > 1: 
        sound_enabled = getSetting_bool('sound', camera_number)
        
    return motion_enabled, sound_enabled

def getSnapShotUrl(camera_number):
    return getStreamUrl(1, camera_number, 1)

def getNewArt(camera_number, value = None):
    if value is None:
        value = getSetting_int('fanart')
    
    if value == 0:
        return getSnapShotUrl(camera_number)
    return None

def getCameraName(camera_number):
    name = getSetting('name', camera_number)
    if name == '':
        name = '%s' %utils.translation(32000 + int(camera_number))
    return name

def getDisabledWindowIds():   
    window_ids = []
    if 'true' in __addon__.getSetting('w_setting'):
        window_ids.extend([10140, 10004, 10011, 10012, 10013, 10014, 10015, 10016, 10017, 10018, 10019, 10021])
    if 'true' in __addon__.getSetting('w_context'):
        window_ids.extend([10106])
    if 'true' in __addon__.getSetting('w_home'):
        window_ids.extend([10000])
    if 'true' in __addon__.getSetting('w_library'):
        window_ids.extend([10001, 10002, 10003, 10005, 10006, 10025, 10028, 10040])
    if 'true' in __addon__.getSetting('w_sysinfo'):
        window_ids.extend([10007, 10100])
    if 'true' in __addon__.getSetting('w_keyboard'):
        window_ids.extend([10103, 10109, 10110])
    if 'true' in __addon__.getSetting('w_controls'):
        window_ids.extend([10114, 10115, 10120, 101222, 10123, 10124, 12901, 12902, 12903, 12904])

    other_window_ids = __addon__.getSetting('w_windowid')
    if other_window_ids != '':
        window_ids_list = other_window_ids.split(',')
        for window_id in window_ids_list:
            window_ids.extend(int(window_id))
            
    return window_ids
        
def getStreamType(source, camera_number):
    '''
    Source:
        0   Video Stream
        1   All Camera Player
        2   Preview
    '''
    stream_type = None
    
    if source == 0:
        stream_type = getSetting_int('stream', camera_number)
            
    elif source == 1:
        stream_type = getSetting_int('allstream', camera_number)
        
    elif source == 2:
        stream_type = getSetting_int('preview_stream', camera_number)

    return stream_type

def getGenericIpcamUrl(source, stream_type, camera_number):
    '''
    Source  -   Stream_type:
        0   Video Stream  -  0 Video; 1 Mjpeg    
        1   All Camera Player  -  0 Mjpeg; 1 Snapshot; 2 Mjpeg
        2   Preview  -  0 Mjpeg; 1 Snapshot; 2 Mjpeg
    '''

    url = None

    if (source > 0 and stream_type != 1) or (source == 0 and stream_type == 1):
        url = getSetting('mjpeg_url', camera_number)
        
    elif (source == 0 and stream_type == 0):
        url = getSetting('stream_url', camera_number)
        
    else:    
        url = getSetting('snapshot_url', camera_number)

    return url

def getFoscamUrl(source, stream_type, camera_number):
    '''
    Source  -   Stream_type:
        0   Video Stream  -  0 Video; 1 Mjpeg    
        1   All Camera Player  -  0 Mjpeg; 1 Snapshot; 2 Mjpeg
        2   Preview  -  0 Mjpeg; 1 Snapshot; 2 Mjpeg
    '''

    url = None
    with foscam2.FoscamCamera(getBasicSettings(camera_number)) as camera:
    
        if (source > 0 and stream_type != 1) or (source == 0 and stream_type == 1):
            url = camera.mjpeg_url
            
        elif (source == 0 and stream_type == 0):
            url = camera.video_url
            
        else:    
            url = camera.snapshot_url

    return url

def getFoscamOverrideUrl(source, stream_type, camera_number):
    '''
    Source  -   Stream_type:
        0   Video Stream  -  0 Video; 1 Mjpeg    
        1   All Camera Player  -  0 Mjpeg; 1 Snapshot; 2 Mjpeg
        2   Preview  -  0 Mjpeg; 1 Snapshot; 2 Mjpeg
    '''

    url = None
    with foscam2.FoscamCamera(getBasicSettings(camera_number)) as camera:
    
        if (source > 0 and stream_type != 1) or (source == 0 and stream_type == 1):
            url = getSetting('mjpeg_url', camera_number)
            if url == '':
                url = camera.mjpeg_url
            
        elif (source == 0 and stream_type == 0):
            url = getSetting('stream_url', camera_number)
            if url == '':
                url = camera.video_url
            
        else:
            url = getSetting('snapshot_url', camera_number)
            if url == '':
                url = camera.snapshot_url

    return url
    
def getStreamUrl(source, camera_number, stream_type=None):
    '''
    MAIN CALLER
    Source:
        0   Video Stream
        1   All Camera Player
        2   Preview
    '''

    camera_type = getCameraType(camera_number)
    if not stream_type:
        stream_type = getStreamType(source, camera_number)
    url = None

    if camera_type == 0 or camera_type == 1:
        url = getFoscamUrl(source, stream_type, camera_number)

    elif camera_type == 1:
        url = getFoscamOverrideUrl(source, stream_type, camera_number)
        
    else:
        url = getGenericIpcamUrl(source, stream_type, camera_number)

    return url    

def getBasicSettings(camera_number, monitor=None, useCache=True):
    """ Returns the login details of the camera """
    
    camera_type = getCameraType(camera_number)
    utils.log(4, 'SETTINGS :: Use Cache: %s;  Camera %s;  Camera Type: %s;  Monitor: %s' %(useCache, camera_number, camera_type, monitor)) 
              
    if camera_type < 3:
        ''' Foscam Camera '''
        
        host = getSetting('host', camera_number)
        if not host:
            utils.log(3, 'SETTINGS :: Camera %s - No host specified.' %camera_number)
            return None
        
        port = getSetting('port', camera_number)
        if not port:
            utils.log(3, 'SETTINGS :: Camera %s - No port specified.' %camera_number)
            return None
        
        username = getSetting('user', camera_number)
        invalid = invalid_user_char(username)
        if invalid:
            utils.log(3, 'SETTINGS :: Camera %s - Invalid character in user name: %s' %(camera_number, invalid))
            return None
        
        password = getSetting('pass', camera_number)
        invalid = invalid_password_char(password)
        if invalid:
            utils.log(3, 'SETTINGS :: Camera %s - Invalid character in password: %s' %(camera_number, invalid))
            return None

        basic_settings = [camera_number, host, port, username, password]
        
        # Camera test and caching logic
        if monitor:
            if useCache:
                utils.log(2, 'SETTINGS :: Camera %s - Checking previous test result...' %camera_number)
                success_code = monitor.cache_get_test_result(camera_number)
                
            else:    
                utils.log(2, 'SETTINGS :: Camera %s - Testing connection...'% camera_number)
                with foscam2.FoscamCamera(basic_settings) as camera:
                    success_code, response = camera.get_dev_state()
                monitor.cache_set_test_result(camera_number, success_code)
            
            if success_code != 0:
                utils.log(3, 'SETTINGS :: No connection to Camera %s.  Code: %s.  Settings: %s' %(camera_number, success_code, basic_settings))
                return None
        
            utils.log(2, 'SETTINGS :: Successful connection to Camera %s' %camera_number)
            utils.log(4, 'SETTINGS :: Camera %s;  Settings: %s;  Cache Used: %s' %(camera_number, basic_settings, useCache))

            # MJPEG Enable - for Service Run.  Ensures MJPEG URLs are Successful
            if not useCache:
                if getSetting_int('stream', camera_number) == 1 or getSetting_int('allstream', camera_number) != 1 or getSetting_int('preview_stream', camera_number) != 1:
                    utils.log(2, 'SETTINGS :: Enabling MJPEG on subStream for Camera %s' %camera_number)
                    camera.enable_mjpeg()
                    
    else:
        ''' Generic IP Camera '''
        
        if monitor and not useCache:
            monitor.cache_set_test_result(camera_number, 0)
               
        basic_settings = [camera_number, '', '', '', '']
        utils.log(4, 'SETTINGS :: Camera %s;  Type: Generic;  Settings: %s' %(camera_number, basic_settings))

    return basic_settings


### Foscam Camera Settings ###

def resetLocation(camera_number):
    if getSetting_int('ptz', camera_number) > 0:
        reset_mode = getSetting_int('conn', camera_number)
        if reset_mode > 0:
            if reset_mode == 2:
                reset_mode = 3
            with foscam2.FoscamCamera(getBasicSettings(camera_number)) as camera:
                camera.ptz_home_location(reset_mode)
                utils.log(2, 'SETTINGS :: Reset Camera %s to the home location' %camera_number)

def getTriggerInterval(camera_number, camera_settings, motion_enabled, sound_enabled):
    """ Gets the alarm trigger interval from the camera """
    
    if camera_settings[2] != '':
        with foscam2.FoscamCamera(camera_settings) as camera:
            motion_trigger_interval = int(camera.get_motion_detect_config()[1].get('triggerInterval'))
            sound_trigger_interval = int(camera.get_sound_detect_config()[1].get('triggerInterval'))
    trigger_interval = 5
    
    if motion_enabled and sound_enabled:
        trigger_interval = min(motion_trigger_interval, sound_trigger_interval)    
    elif motion_enabled:
        trigger_interval = motion_trigger_interval  
    elif sound_enabled:
        trigger_interval = sound_trigger_interval
        
    return trigger_interval


### Error Checking Support ###

def invalid_char(credential, chars, stringid, show_dialog):
    for char in chars:
        if char in credential:
            if show_dialog:
                utils.dialog_ok(utils.translation(stringid), ' ', ' '.join(chars))
            return char
    return False

def invalid_password_char(password, show_dialog=False):
    return invalid_char(password, INVALID_PASSWORD_CHARS, 32205, show_dialog)

def invalid_user_char(user, show_dialog=False):
    return invalid_char(user, INVALID_USER_CHARS, 32206, show_dialog)

