"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to monitor the entire add-on and allow communication between events outside of the main process loop
"""

import xbmc
from xbmcgui import Window, getCurrentWindowId, getCurrentWindowDialogId
from time import time
import settings, utils

class AddonMonitor(xbmc.Monitor):
    """ Addon monitor class is used to monitor the entire addon and make changes on a global level """
    
    def __init__(self):
        xbmc.Monitor.__init__(self)

    def reset(self):
        ''' Reinitializes monitor settings '''
        self._stop = False
        self.dismissed_time = [0, 0, 0, 0, 0]  # Dirty fix for 4th spot since Im not reducing the camera number int
        self._dismissed_behavior = settings.getSetting_int('dismissed_behavior')            #0 - All dismissed, 1 - Just the window itself
        self._dismissed_duration = settings.getSetting_int('dismissed_duration') 
        self._preview_disabled_window_id = settings.getDisabledWindowIds()

    def stop(self):
        self._stop = True

    def stopped(self):
        return self._stop
    
    def onSettingsChanged(self):
        utils.log(2, 'MONITOR: Settings change was detected')
        if not self.stopped():
            self.stop()


    # Improves UI speed by caching the result when the camera is first connected    
    def cache_set_test_result(self, camera_number, success_code):
        if success_code == 0:
            Window(10000).setProperty('result%s' %camera_number, '1')
        else:
            Window(10000).clearProperty('result%s' %camera_number)
            
    def cache_test_result(self, camera_number):
        if Window(10000).getProperty('result%s' %camera_number) == '1':
            return True
        return False


    # Used to disable or enable the preview service from activating without restarting the service   
    def toggle_preview(self):
        if self.isToggleSet():
            Window(10000).clearProperty('SROOM_CACHE: preview toggle')
            utils.notify(utils.translation(32226))
        else:
            Window(10000).setProperty('SROOM_CACHE: preview toggle', '1')
            utils.notify(utils.translation(32227))
            
    def isToggleSet(self):
        if Window(10000).getProperty('SROOM_CACHE: preview toggle') == '1':
            return True
        return False


    # Used to indicate that the preview window should show because it was requested manually
    def set_script(self, camera_number):
        Window(10000).setProperty('SROOM_CACHE: Script Override %s' %camera_number, '1')

    def reset_script(self, camera_number):
        Window(10000).clearProperty('SROOM_CACHE: Script Override %s' %camera_number)
        
    def script_override(self, camera_number):
        if Window(10000).getProperty('SROOM_CACHE: Script Override %s' %camera_number) == '1':
            return True
        return False
    

    # Used to make the add-on globally aware if a preview window is open or not
    def set_preview_window_opened(self, camera_number):
        Window(10000).setProperty('SROOM_CACHE: Preview Camera Open %s' %camera_number, '1')
        
    def set_preview_window_closed(self, camera_number):
        Window(10000).clearProperty('SROOM_CACHE: Preview Camera Open %s' %camera_number)
        self.reset_script(camera_number)
        self.clear_request_to_close_window(camera_number)

    def preview_window_opened(self, camera_number):
        if Window(10000).getProperty('SROOM_CACHE: Preview Camera Open %s' %camera_number) == '1':
            return True
        return False


    # New way to request to close preview windows
    def request_to_close_window(self, camera_number):
        Window(10000).setProperty('SROOM_CACHE: Request to Close %s' %camera_number, '1')

    def clear_request_to_close_window(self, camera_number):
        Window(10000).clearProperty('SROOM_CACHE: Request to Close %s' %camera_number)

    def requested_to_close_window(self, camera_number):
        if Window(10000).getProperty('SROOM_CACHE: Request to Close %s' %camera_number) == '1':
            return True
        return False


    def set_all_preview_window_closed(self):
        self.request_to_close_window('1')
        self.request_to_close_window('2')
        self.request_to_close_window('3')
        self.request_to_close_window('4')
        

    # Used to make the add-on globally aware that a camera is playing fullscreen or not
    def set_camera_playing(self, camera_number):
        if camera_number == 'All':
            Window(10000).setProperty('SROOM_CACHE: AllCameras playing', '1')
        else:
            Window(10000).setProperty('SROOM_CACHE: Camera %s playing' %camera_number, '1')

    def reset_camera_playing(self, camera_number):
        if camera_number == 'All':
            Window(10000).clearProperty('SROOM_CACHE: AllCameras playing')
        else:
            Window(10000).clearProperty('SROOM_CACHE: Camera %s playing' %camera_number)

    def camera_is_playing(self, camera_number):
        allcameras = bool(Window(10000).getProperty('SROOM_CACHE: AllCameras playing'))
        singlecamera = bool(Window(10000).getProperty('SROOM_CACHE: Camera %s playing' %camera_number))
        if allcameras or singlecamera:
            return True
        return False


    # Used to delay the next time the preview window is shown if it is manually dismissed
    def set_preview_window_dismissed(self, camera_number):
        dismissed_until = time() + self._dismissed_duration
        if self._dismissed_behavior == 0:
            self.dismissed_time[0] = dismissed_until
            self.set_all_preview_window_closed()
        else:
            self.dismissed_time[int(camera_number)] = dismissed_until

    def reset_dismissed_preview(self, camera_number):
        self.dismissed_time[int(camera_number)] = 0

    def dismissed_preview(self, camera_number):
        if self._dismissed_behavior == 0:
            if self.dismissed_time[0] == 0:
                return False
            if time() > self.dismissed_time[0]:
                self.reset_dismissed_preview(0)
                return False
        else:
            if self.dismissed_time[int(camera_number)] == 0:
                return False
            if time() > self.dismissed_time[int(camera_number)]:
                self.reset_dismissed_preview(camera_number)
                return False
        return True


    # Used to determine if the window in focus is allowed to lose focus due to a preview window opening
    def window_id_check(self):
        current_dialog_id = getCurrentWindowDialogId()
        current_window_id = getCurrentWindowId()

        for window_id in self._preview_disabled_window_id:
            if current_window_id == window_id or current_dialog_id == window_id:
                return True
        return False


    # Function that determines if a preview is allowed to be shown considering the global state
    def preview_not_open_allowed(self, camera_number):
        opened = self.preview_window_opened(camera_number)
        isPlaying = self.camera_is_playing(camera_number)
        dismissed = self.dismissed_preview(camera_number)
        window = self.window_id_check()
        allowed = not (isPlaying or dismissed or window or self.isToggleSet())
        script_override = self.script_override(camera_number)
        
        #utils.log(4, 'MONITOR: Camera %s;  Preview Opened: %s;  Preview Allowed: %s;  Script Override: %s; Camera Is Playing: %s;  Camera Dismissed: %s;  Allowed on Window: %s'
        #      %(camera_number, opened, allowed, script_override, isPlaying, dismissed, window ))
        
        return (not opened) and (allowed or script_override)


if __name__ == "__main__":
    pass
