"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to obtain add-on settings and camera settings
"""

import xbmc, xbmcgui, xbmcaddon
import utils

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

        if enabled:
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

