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
           
           1:  [1]host  [2]port  [3]username  [4]password  [5]name  [6]snapshot  [7]rtsp  
               [8]mpjeg  [9]cameratype  [10]cameraplayer_source  [11]allcameraplayer_source
               
           2:  [12]pan_tilt  [13]zoom  [14]motionsupport  [15]soundsupport
           
           3:  [16]preview_enabled  [17]duration  [18]location  [19]scaling  [20]motion_enabled
                   [21]sound_enabled  [22]check_interval  [23]preview_source  [24]trigger_interval
           ]

'''

import xbmc, xbmcgui, xbmcaddon
from resources.lib import foscam

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



def get_playbackRewindTime():
    playback_rewind_time = int(__addon__.getSetting('playback_rewind_time'))
    return playback_rewind_time

def get_globalSettings():
    dismissed_behavior  = int(__addon__.getSetting('dismissed_behavior'))
    dismissed_time      = int(__addon__.getSetting('dismissed_time'))
    preview_manual_open = int(__addon__.getSetting('preview_manual_open_behavior'))
    
    window_ids = []
    if 'true' in __addon__.getSetting('setting_menus'):
        window_ids.extend([10140, 10004, 10011, 10012, 10013, 10014, 10015, 10016, 10017, 10018, 10019, 10021])
    if 'true' in __addon__.getSetting('context_menu'):
        window_ids.extend([10106])
    if 'true' in __addon__.getSetting('home_screen'):
        window_ids.extend([10000])
    if 'true' in __addon__.getSetting('library_navigation'):
        window_ids.extend([10001, 10002, 10003, 10005, 10006, 10025, 10028, 10040])
    if 'true' in __addon__.getSetting('system_information'):
        window_ids.extend([10007, 10100])
    if 'true' in __addon__.getSetting('virtual_keyboard'):
        window_ids.extend([10103, 10109, 10110])
    if 'true' in __addon__.getSetting('player_controls'):
        window_ids.extend([10114, 10115, 10120, 101222, 10123, 10124, 12901, 12902, 12903, 12904])

    other_window_ids = __addon__.getSetting('other_window_ids')
    if other_window_ids != '':
        window_ids_list = other_window_ids.split(',')
        for window_id in window_ids_list:
            window_ids.extend(int(window_id))

    global_settings = [dismissed_behavior, dismissed_time, preview_manual_open, window_ids]
    #print 'Global Settings'
    #print str(global_settings)
    return global_settings



def get_basicSettings(camera_number):
    cameratype = __addon__.getSetting('cameratype' + camera_number).lower()
    basic_settings = [camera_number]
    

    name = __addon__.getSetting('name' + camera_number)
    if name == '':
        del name
        name = '%s %s' %(translation(32008), camera_number)
    
    if 'foscam' in cameratype:
        host = __addon__.getSetting('host' + camera_number)
        port = __addon__.getSetting('port' + camera_number)
        username = __addon__.getSetting('username' + camera_number)
        password = __addon__.getSetting('password' + camera_number)
        
        basic_settings.extend([host, port, username, password, name])
        
    else:
        basic_settings.extend([' ', ' ', ' ', ' ', name])

    snapshot = __addon__.getSetting('snapshot' + camera_number)
    rtsp = __addon__.getSetting('rtsp' + camera_number)
    mpjeg = __addon__.getSetting('mjpeg' + camera_number)
    
    cameraplayer_source = int(__addon__.getSetting('cameraplayer_source' + camera_number))
    allcameraplayer_source = int(__addon__.getSetting('allcameraplayer_source' + camera_number))

    basic_settings.extend([snapshot, rtsp, mpjeg, cameratype, cameraplayer_source, allcameraplayer_source])
    return basic_settings

   
def checkSettings(basic_settings, useCache):
    '''
    basic_settings:
    [0]camera_number
    [1]host  [2]port  [3]username  [4]password  [5]name  [6]snapshot  [7]rtsp  
    [8]mpjeg  [9]cameratype  [10]cameraplayer_source  [11]allcameraplayer_source
    '''
               
    camera_number = basic_settings[0]
    host = basic_settings[1]
    username = basic_settings[3]
    password = basic_settings[4]
    camera_type = basic_settings[9]
    checked_settings = basic_settings[1::1]


    if 'foscam' in camera_type:
        
        #User Input Error Checking
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

        #Camera Settings
        with foscam.Camera(basic_settings) as camera:
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

            #Caches camera test result
            xbmcgui.Window(10000).setProperty('Camera%sTestResult' %camera_number, '1')

            #Makes sure camera is enabled for mjpeg if required.
            if not useCache:
                if __addon__.getSetting('preview_source' + camera_number) == 0 or basic_settings[10] == 0 or basic_settings[11] == 0:
                    camera.enable_mjpeg

            #Sets the URL if not explicitly set for Foscam Cameras 
            if len(checked_settings[5]) < 6:
                checked_settings[5] = camera.snapshot_url
            if len(checked_settings[6]) < 6:
                if basic_settings[10] == 2:
                    checked_settings[6] = camera.video_sub_url
                else:
                    checked_settings[6] = camera.video_url
            if len(checked_settings[7]) < 6:
                checked_settings[7] = camera.mjpeg_url

        return True, checked_settings

    
    else:
        #Totally needs updated for empty URLs that are required for non-Foscam Cameras!
        return True, checked_settings




def getSettings(settings_to_get = 'all', cameras_to_get = '1234'):
    '''
    Text Here
    '''
    
    global __addon__
    __addon__ = xbmcaddon.Addon()

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
                basic_settings = get_basicSettings(camera_number)

                useCache = False
                if settings_level < 3:
                    useCache = True
                    
                configuredCorrectly, checked_basic_settings = checkSettings(basic_settings, useCache)
                

            if configuredCorrectly:
                activeCameras.append([camera_number])
                activeCameras[len(activeCameras)-1].extend(checked_basic_settings)


                '''
                Features Settings - Settings Level 2
                '''
                if settings_level > 1:
                    pan_tilt = False
                    zoom = False
                    motionsupport = False
                    soundsupport = False

                    controls = __addon__.getSetting('controls' + camera_number).lower()
                    
                    if 'pan' in controls:
                        pan_tilt = True

                    if 'zoom' in controls:
                        zoom = True
                        
                    alarmtype = __addon__.getSetting('alarmtype' + camera_number).lower()
                    if 'motion' in alarmtype:
                        motionsupport = True
                    if 'sound' in alarmtype:
                        soundsupport = True

                    activeCameras[len(activeCameras)-1].extend([pan_tilt, zoom, motionsupport, soundsupport])


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
                        preview_source = int(__addon__.getSetting('preview_source' + camera_number))

                        if 'true' in __addon__.getSetting('update_camera_settings' + camera_number):
                            set_CameraAlarmSettings(basic_settings, motion_enabled, sound_enabled)
                            
                        else:
                            get_CameraAlarmSettings(basic_settings, motion_enabled, sound_enabled)
                            
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
                    #print 'All Settings'
                    #print str(activeCameras[len(activeCameras)-1])

                  
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

def notify(msg):
    __icon__  = __addon__.getAddonInfo('icon').decode("utf-8")
    addon_name = translation(32000)
    xbmcgui.Dialog().notification(addon_name, msg, icon = __icon__) 

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

