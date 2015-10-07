'''
Text Here
'''

import xbmc
from xbmcgui import Window, getCurrentWindowId, getCurrentWindowDialogId
from time import time
from settings import get_globalSettings

#MENU_SETTINGS_ID = 10140
#MENU_CONTEXT_ID = 10106
#DISMISSED_INTERVAL = 15     #Seconds


class AddonMonitor(xbmc.Monitor):
    '''
    Addon monitor class is used to monitor the entire addon and make changes on a global level
    '''
    
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self._stop = True
        #self._preview_window_state = [0, 0, 0, 0]
        self._preview_dismissed_time = [0, 0, 0, 0]
        

    '''
    Functions used when to monitor changes to settings and reset the main service
    '''
    def onSettingsChanged(self):
        if not self.stopped():
            self.stop()
        
    def reset(self):
        self._stop = False
        
        global_settings = get_globalSettings()

        self.preview_dismissal_behavior = global_settings[0]            #0 - All dismissed, 1 - Just the window itself
        self.preview_dismissal_time = global_settings[1]
        self.preview_from_script_autoclose = bool(global_settings[2])   #0 - Stay Open until Manually Closed, 1 - Use the interval time
        self.preview_disable_display_for_window_id = global_settings[3]

    def stop(self):
        self._stop = True

    def disable_changes(self):
        self._stop = True

    def stopped(self):
        return self._stop

    def playback_resume_time(self):
        return self._playback_resume_time
    

    '''
    Functions used to communicate across service threads, to determine status of each
    '''
    def script_called(self, camera_number):
        Window(10000).setProperty('Preview Camera from Script %s' %camera_number, '1')
        #self.preview_window_open(camera_number)

    def opened_from_script(self, camera_number):
        from_script = bool(Window(10000).getProperty('Preview Camera from Script %s' %camera_number))
        return from_script
        
    def preview_window_open(self, camera_number):
        Window(10000).setProperty('Preview Camera %s' %camera_number, '1')
        #self._preview_window_state[int(camera_number) - 1] = 1
        
    def preview_window_reset(self, camera_number):
        Window(10000).clearProperty('Preview Camera %s' %camera_number)
        Window(10000).clearProperty('Preview Camera from Script %s' %camera_number)
        #self._preview_window_state[int(camera_number) - 1] = 0

    def preview_window_opened(self, camera_number):
        state = bool(Window(10000).getProperty('Preview Camera %s' %camera_number))
        return state
        #return self._preview_window_state[int(camera_number) - 1]



    '''
    Functions to check status of plugin player
    '''
    def set_camera_playing(self, camera_number):
        if camera_number == 'All':
            Window(10000).setProperty('AllCameras are playing', '1')
        else:
            Window(10000).setProperty('Camera %s is playing' %camera_number, '1')

    def clear_camera_playing(self, camera_number):
        if camera_number == 'All':
            Window(10000).clearProperty('AllCameras are playing')
        else:
            Window(10000).clearProperty('Camera %s is playing' %camera_number)

    def camera_is_playing(self, camera_number):
        allcameras = bool(Window(10000).getProperty('AllCameras are playing'))
        singlecamera = bool(Window(10000).getProperty('Camera %s is playing' %camera_number))
        if allcameras or singlecamera:
            return True
        else:
            return False


    '''
    Functions used to delay the next time the preview window is shown if it is dismissed
    '''
    def set_dismissed_preview(self, camera_number):
        dismissed_until = time() + self.preview_dismissal_time
        if self.preview_dismissal_behavior == 0:
            self._preview_dismissed_time[0] = dismissed_until
        else:
            self._preview_dismissed_time[int(camera_number)] = dismissed_until

    def clear_dismissed_preview(self, camera_number):
        self._preview_dismissed_time[int(camera_number)] = 0

    def preview_dismissed(self, camera_number):
        if self.preview_dismissal_behavior == 0:
            if self._preview_dismissed_time[0] == 0:
                return False
            if time() > self._preview_dismissed_time[0]:
                self.clear_dismissed_preview(0)
                return False
            
        else:
            if self._preview_dismissed_time[int(camera_number)] == 0:
                return False
            if time() > self._preview_dismissed_time[int(camera_number)]:
                self.clear_dismissed_preview(camera_number)
                return False
        return True

    
    '''
    Text Here
    '''
    def window_id_check(self):
        current_dialog_id = getCurrentWindowDialogId()
        current_window_id = getCurrentWindowId()
        #print 'Current window IDs: ' + str(current_window_id) + ' and ' + str(current_dialog_id)

        for window_id in self.preview_disable_display_for_window_id:
            if current_window_id == window_id or current_dialog_id == window_id:
                return True
        return False



    '''
    Text Here
    '''
    def preview_not_open_allowed(self, camera_number):
        preview_not_opened = not self.preview_window_opened(camera_number)
        preview_allowed = not (self.camera_is_playing(camera_number) or self.preview_dismissed(camera_number) or self.window_id_check())
        open_request_from_script = self.opened_from_script(camera_number)
        
        return preview_not_opened and (preview_allowed or open_request_from_script)


    
                







if __name__ == "__main__":
    pass
