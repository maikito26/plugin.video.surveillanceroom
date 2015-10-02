'''
   Notes about this file:
   1. Send and Get commands from Camera are not yet confirmed or guaranteed (such as updating camera motion settings)
   2. Schedule, and other Camera Settings are not yet implemented but will be in the future

   Function Definition:
       getSettings(settings_to_get = 'all', cameras_to_get = '1234'):

       settings_to_get: 'enabled'(0), 'basic'(1), 'features'(2), 'all'(3)
       cameras_to_get: '1', '2', '3', '4', '1234'

       returns boolean:
           'True' if there is one Enabled camera, otherwise 'False'

       returns list of lists:
           [
           0:  [0]camera_number
           1:  [1]host  [2]port  [3]username  [4]password  [5]camera_type  [6]snapshot  [7]rtsp  [8]mjpeg
           2:  [9]controls  [10]motionsupport  [11]soundsupport  [12]usempjegstream
           3:  [13]preview_enabled  [14]duration  [15]location  [16]scaling  [17]motion_enabled
                   [18]sound_enabled  [19]check_interval  [20]preview_source  [21]trigger_interval
           ]

'''

import xbmc, xbmcgui, xbmcaddon
from resources.lib import foscam

__addon__ = xbmcaddon.Addon('plugin.video.foscam4kodi')

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

INVALID_PASSWORD_CHARS = ('{', '}', ':', ';', '!', '?', '@', '\\', '/')
INVALID_USER_CHARS = ('@',)

def get_basicSettings (camera_number):
    cameratype = __addon__.getSetting('cameratype' + camera_number).lower()
    basicSettings = [camera_number]
    
    if 'foscam' in cameratype:
        host = __addon__.getSetting('host' + camera_number)
        port = __addon__.getSetting('port' + camera_number)
        username = __addon__.getSetting('username' + camera_number)
        password = __addon__.getSetting('password' + camera_number)
        basicSettings.extend([host, port, username, password])
        
    else:
        basicSettings.extend([' ', ' ', ' ', ' '])

    snapshot = __addon__.getSetting('snapshot' + camera_number)
    rtsp = __addon__.getSetting('rtsp' + camera_number)
    mpjeg = __addon__.getSetting('mpjpeg' + camera_number)

    basicSettings.extend([cameratype, snapshot, rtsp, mpjeg])

    return basicSettings


   
def checkSettings(basicSettings, useCache):
    camera_number = basicSettings[0]
    host = basicSettings[1]
    username = basicSettings[3]
    password = basicSettings[4]
    camera_type = basicSettings[5]
    checkedSettings = basicSettings[1::1]

    if 'foscam' in camera_type:
        if not host:
            print 'Error: Camera {0} - No host specified.'.format(camera_number)
            return False, None

        invalid = invalid_user_char(username)
        if invalid:
            print 'Error: Camera {0} - Invalid character in user name: {1}'.format(camera_number, invalid)
            return False, None

        invalid = invalid_password_char(password)
        if invalid:
            print 'Error: Camera {0} - Invalid character in password: {1}'.format(camera_number, invalid)
            return False, None

        

        with foscam.Camera(basicSettings) as camera:
            if useCache:
                print 'Camera {0} - Checking previous test result...'.format(camera_number)
                success = bool(xbmcgui.Window(10000).getProperty('Camera%sTestResult' %camera_number))
                msg = ''

            else:    
                print 'Camera {0} - Testing connection...'.format(camera_number)
                success, msg = camera.test()

            if not success:
                xbmcgui.Window(10000).clearProperty('Camera%sTestResult' %camera_number)
                print 'Error: Camera {0} - {1}'.format(camera_number, msg)
                return False, None

            xbmcgui.Window(10000).setProperty('Camera%sTestResult' %camera_number, '1')
            
            if len(checkedSettings[5]) < 5:
                checkedSettings[5] = camera.snapshot_url
            if len(checkedSettings[6]) < 5:
                checkedSettings[6] = camera.video_url
            if len(checkedSettings[7]) < 5:
                checkedSettings[7] = camera.mjpeg_url

        return True, checkedSettings
    
    else: #Totally needs updated for empty URLs that are required!
        return True, checkedSettings



#Get settings.xml data    
def getSettings(settings_to_get = 'all', cameras_to_get = '1234'):
    global __addon__
    __addon__ = xbmcaddon.Addon('plugin.video.foscam4kodi')

    if settings_to_get == 'enabled':
        settings_level = 0
    elif settings_to_get == 'basic':
        settings_level = 1
    elif settings_to_get == 'features':
        settings_level = 2
    elif settings_to_get == 'all':
        settings_level = 3
    
    activeCameras = []
    configuredCorrectly = False

    for camera_number in cameras_to_get:

        
        '''
        Enabled Settings - Settings Level 0
        '''
        if 'true' in __addon__.getSetting('camera%s' %camera_number):
            camera_enabled = True
            print 'Camera {0} - Enabled'.format(camera_number)

            if settings_level == 0:
                activeCameras.append([camera_number])
                
        else:
            camera_enabled = False
            print 'Camera {0} - Not Enabled.'.format(camera_number)


        if camera_enabled:


            '''
            Basic Settings - Settings Level 1
            '''
            if settings_level > 0:
                basicSettings = get_basicSettings(camera_number)

                useCache = False
                if settings_level < 3:
                    useCache = True
                    
                configuredCorrectly, checkedSettings = checkSettings(basicSettings, useCache)


            if configuredCorrectly:
                activeCameras.append([camera_number])
                activeCameras[len(activeCameras)-1].extend(checkedSettings)



                '''
                Features Settings - Settings Level 2
                '''
                if settings_level > 1:
                    controls = False
                    motionsupport = False
                    soundsupport = False
                    usempjegstream = False
                    
                    if 'true' in __addon__.getSetting('controls' + camera_number):
                        controls = True

                    if 'true' in __addon__.getSetting('motionsupport' + camera_number):
                        motionsupport = True

                    if 'true' in __addon__.getSetting('soundsupport' + camera_number):
                        soundsupport = True

                    if 'true' in __addon__.getSetting('usemjpegstream' + camera_number):
                        usempjegstream = True

                        #Command Required to set/force mpjeg stream settings on camera

                    activeCameras[len(activeCameras)-1].extend([controls, motionsupport, soundsupport, usempjegstream])



                '''
                All Settings - Settings Level 3
                '''
                if settings_level > 2:
                    
                    preview_enabled  = False
                    if 'true' in __addon__.getSetting('preview_enabled' + camera_number):
                        preview_enabled = True

                    activeCameras[len(activeCameras)-1].extend([preview_enabled])
     
                    if preview_enabled:
                        duration = float(__addon__.getSetting('duration' + camera_number))
                        location = __addon__.getSetting('location' + camera_number).lower()
                        scaling = float(__addon__.getSetting('scaling' + camera_number))
                        
                        motion_enabled = False
                        sound_enabled = False
                        
                        if 'true' in __addon__.getSetting('motion_trigger' + camera_number) and motionsupport:
                            motion_enabled = True

                        if 'sound' in __addon__.getSetting('sound_trigger' + camera_number) and soundsupport:
                            sound_enabled = True

                        check_interval = int(__addon__.getSetting('check_interval' + camera_number))
                        preview_source = __addon__.getSetting('preview_source' + camera_number)

                        if 'true' in __addon__.getSetting('update_camera_settings' + camera_number):
                            set_CameraAlarmSettings(basicSettings, motion_enabled, sound_enabled)
                            
                        else:
                            get_CameraAlarmSettings(basicSettings, motion_enabled, sound_enabled)
                            
                        __addon__ = xbmcaddon.Addon()                       #Quick Refresh of Settings in RAM
                            
                        motion_trigger_interval = int(__addon__.getSetting('motion_trigger_interval' + camera_number))
                        sound_trigger_interval = int(__addon__.getSetting('sound_trigger_interval' + camera_number))

                        trigger_interval = 5
                        
                        if motion_enabled and sound_enabled:
                            trigger_interval = min(motion_trigger_interval, sound_trigger_interval)
                            
                        elif motion_enabled:
                            trigger_interval = motion_trigger_interval
                            
                        elif sound_enabled:
                            trigger_interval = sound_trigger_interval


                        activeCameras[len(activeCameras)-1].extend([
                                                                    duration, location, scaling, motion_enabled, sound_enabled,
                                                                    check_interval, preview_source, trigger_interval
                                                                    ])

                  
    if len(activeCameras) > 0:
        return True, activeCameras

    return False, 'No cameras configured.'          


def set_CameraAlarmSettings(camera_settings, motion_enabled, sound_enabled):
    camera_number = camera_settings[0]

    with foscam.Camera(camera_settings) as camera:
        if motion_enabled:
            command = camera.set_motion_detect_config()
            command['isEnable'] = 1
            command['sensitivity'] = __addon__.getSetting('motion_sensitivity' + camera_number)
            command['triggerInterval'] = __addon__.getSetting('motion_trigger_interval' + camera_number)                                             
            camera.send_command(command)
            
        if sound_enabled:
            command = camera.set_sound_detect_config()
            command['isEnable'] = 1
            command['sensitivity'] = __addon__.getSetting('sound_sensitivity' + camera_number)
            command['triggerInterval'] = __addon__.getSetting('sound_trigger_interval' + camera_number)
            #for iday in range(7):
            #    command['schedule{0:d}'.format(iday)] = 2**48 - 1
            camera.send_command(command)

    __addon__.setSetting('update_camera_settings' + camera_number, 'false')


def get_CameraAlarmSettings(camera_settings, motion_enabled, sound_enabled):
    camera_number = camera_settings[0]

    with foscam.Camera(camera_settings) as camera:
        if motion_enabled:
            response = camera.get_motion_detect_config()
            print str(response)
            __addon__.setSetting('motion_sensitivity' + camera_number, str(response['sensitivity']))
            __addon__.setSetting('motion_trigger_interval' + camera_number, str(response['triggerInterval']))
            command = camera.set_motion_detect_config()
            command['isEnable'] = 1
            send_http_command(command)
                
        if sound_enabled:
            response = camera.get_sound_detect_config()
            __addon__.setSetting('sound_sensitivity' + camera_number, str(response['sensitivity']))
            __addon__.setSetting('sound_trigger_interval' + camera_number, str(response['triggerInterval']))
            command = camera.set_sound_detect_config()
            command['isEnable'] = 1
            send_http_command(command)


def send_http_command(command):
    response = command.send()
    if not response:
        msg = ('{0}: {1}').format(translation(32104), response.message)
        notify(msg)

def translation(id): 
    return __addon__.getLocalizedString(id) #.encode('utf-8') 

def notify(msg, time=10000):
    __icon__  = __addon__.getAddonInfo('icon').decode("utf-8")
    addon_name = translation(32000)
    xbmcgui.Dialog().notification(addon_name, msg, __icon__, '') #, time)

def invalid_char(credential, chars, stringid, show_dialog):
    for char in chars:
        if char in credential:
            if show_dialog:
                addon_name = translation(32000)
                xbmcgui.Dialog().ok(addon_name, translation(stringid), ' ', ' '.join(chars))
            return char
    return False

def invalid_password_char(password, show_dialog=False):
    return invalid_char(password, INVALID_PASSWORD_CHARS, 32105, show_dialog)

def invalid_user_char(user, show_dialog=False):
    return invalid_char(user, INVALID_USER_CHARS, 32106, show_dialog)

