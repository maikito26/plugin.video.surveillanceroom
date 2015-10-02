import xbmc
from xbmcgui import Window, getCurrentWindowId, getCurrentWindowDialogId
import time

MENU_SETTINGS_ID = 10140
MENU_CONTEXT_ID = 10106
DISMISSED_INTERVAL = 15     #Seconds


class AddonMonitor(xbmc.Monitor):
    '''
    Addon monitor class is used to monitor the entire addon and make changes on a global level
    '''
    
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self._stop = True
        self._preview_window_state = [0, 0, 0, 0]
        self._preview_dismissed_time = [0, 0, 0, 0]
        

    '''
    Functions used when to monitor changes to settings and reset the main service
    '''
    def onSettingsChanged(self):
        if not self.stopped():
            self.stop()
        
    def reset(self):
        self._stop = False

    def stop(self):
        self._stop = True

    def disable_changes(self):
        self._stop = True

    def stopped(self):
        return self._stop


    '''
    Functions used to communicate across service threads, to determine status of each
    '''
    def preview_window_open(self, camera_number):
        self._preview_window_state[int(camera_number) - 1] = 1
        
    def preview_window_close(self, camera_number):
        self._preview_window_state[int(camera_number) - 1] = 0

    def preview_window_opened(self, camera_number):
        return self._preview_window_state[int(camera_number) - 1]


    '''
    Functions used to delay the next time the preview window is shown if it is dismissed
    '''
    def set_dismissed_preview(self, camera_number):
        self._preview_dismissed_time[int(camera_number)] = time.time() + DISMISSED_INTERVAL

    def clear_dismissed_preview(self, camera_number):
        self._preview_dismissed_time[int(camera_number)] = 0

    def preview_dismissed(self, camera_number):
        if self._preview_dismissed_time[int(camera_number)] == 0:
            return False
        if time.time() > self._preview_dismissed_time[int(camera_number)]:
            self.clear_dismissed_preview(camera_number)
            return False
        return True
    

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
    Text Here
    '''
    def settings_dialog_opened(self):
        current_dialog_id = getCurrentWindowDialogId()

        if current_dialog_id == MENU_SETTINGS_ID or current_dialog_id == MENU_CONTEXT_ID:
            return True
        else:
            return False

    '''
    Text Here
    '''
    def preview_allowed(self, camera_number):
        return not (self.camera_is_playing(camera_number) or self.preview_dismissed(camera_number) or self.settings_dialog_opened())

    
    '''
    Text Here
    '''
    def set_player_controls_window(self):
        window_id = getCurrentWindowId()
        Window(10000).setProperty('Player Controls Window Id', str(window_id))
        
    def get_player_controls_window(self):
        return Window(10000).getProperty('Player Controls Window Id')

    
                







if __name__ == "__main__":
    pass
