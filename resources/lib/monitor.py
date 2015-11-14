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
        Window(10000).setProperty('SR_monitor', '1')
        self.dismissed_time = [0, 0, 0, 0, 0, 0, 0]  
        self._dismissed_behavior = settings.getSetting_int('dismissed_behavior')            #0 - All dismissed, 1 - Just the window itself
        self._dismissed_duration = settings.getSetting_int('dismissed_duration') 
        self._preview_disabled_window_id = settings.getDisabledWindowIds()

    def stop(self):
        Window(10000).clearProperty('SR_monitor')
        
    def stopped(self):
        if Window(10000).getProperty('SR_monitor') == '1':
            return False
        return True
    
    def onSettingsChanged(self):
        utils.log(2, 'MONITOR: Settings change was detected')
        if not self.stopped():
            self.stop()


    # Improves UI speed by caching the result when the camera is first connected    
    def write_testResult(self, camera_number, success_code):
        if success_code == 0:
            Window(10000).setProperty('SR_result_%s' %camera_number, '1')
        else:
            Window(10000).clearProperty('SR_result_%s' %camera_number)
            
    def testResult(self, camera_number):
        if Window(10000).getProperty('SR_result_%s' %camera_number) == '1':
            return True
        return False




    # NEW @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    def openRequest(self, camera_number):
        Window(10000).setProperty('SR_openRequest_%s' %camera_number, '1')

    def openRequest_manual(self, camera_number):
        Window(10000).setProperty('SR_openRequest_manual_%s' %camera_number, '1')
        self.openRequest(camera_number)

    def closeRequest(self, camera_number):
        Window(10000).setProperty('SR_closeRequest_%s' %camera_number, '1')

    def set_alarmActive(self, camera_number):
        Window(10000).setProperty('SR_alarmActive_%s' %camera_number, '1')

    
    def clear_openRequest(self, camera_number):
        Window(10000).clearProperty('SR_openRequest_%s' %camera_number)

    def clear_openRequest_manual(self, camera_number):
        Window(10000).clearProperty('SR_openRequest_manual_%s' %camera_number)

    def clear_closeRequest(self, camera_number):
        Window(10000).clearProperty('SR_closeRequest_%s' %camera_number)

    def clear_alarmActive(self, camera_number):
        Window(10000).clearProperty('SR_alarmActive_%s' %camera_number)
        
        
    def openRequested(self, camera_number):
        if Window(10000).getProperty('SR_openRequest_%s' %camera_number) == '1':
            return True
        return False

    def openRequested_manual(self, camera_number):
        if Window(10000).getProperty('SR_openRequest_manual_%s' %camera_number) == '1':
            return True
        return False

    def closeRequested(self, camera_number):
        if Window(10000).getProperty('SR_closeRequest_%s' %camera_number) == '1':
            return True
        return False

    def alarmActive(self, camera_number):
        if Window(10000).getProperty('SR_alarmActive_%s' %camera_number) == '1':
            return True
        return False


    def openPreview(self, camera_number):
        self.clear_closeRequest(camera_number)
        Window(10000).setProperty('SR_openPreview_%s' %camera_number, '1')
        self.clear_openRequest(camera_number)

    def closePreview(self, camera_number):
        self.clear_openRequest(camera_number)
        self.clear_openRequest_manual(camera_number)
        Window(10000).clearProperty('SR_openPreview_%s' %camera_number)
        self.clear_closeRequest(camera_number)
        
    def previewOpened(self, camera_number):
        if Window(10000).getProperty('SR_openPreview_%s' %camera_number) == '1':
            return True
        return False
    

    # Used to disable or enable the preview service from activating without restarting the service   
    def togglePreview(self):
        if self.toggledPreview():
            Window(10000).clearProperty('SR_togglePreview')
            utils.notify(utils.translation(32226))
        else:
            Window(10000).setProperty('SR_togglePreview', '1')
            utils.notify(utils.translation(32227))
            
    def toggledPreview(self):
        if Window(10000).getProperty('SR_togglePreview') == '1':
            return True
        return False
        

    # Used to make the add-on globally aware that a camera is playing fullscreen or not
    def set_playingCamera(self, camera_number):
        Window(10000).setProperty('SR_playingCamera_%s' %camera_number, '1')
        if camera_number == '0':
            self.dismissAllPreviews()
        else:
            self.closeRequest(camera_number)

    def clear_playingCamera(self, camera_number):
        Window(10000).clearProperty('SR_playingCamera_%s' %camera_number)

    def playingCamera(self, camera_number):
        allcameras = Window(10000).getProperty('SR_playingCamera_0')
        singlecamera = Window(10000).getProperty('SR_playingCamera_%s' %camera_number)
        if allcameras == '1' or singlecamera == '1':
            return True
        return False


    # Used to delay the next time the preview window is shown if it is manually dismissed
    def dismissAllPreviews(self):
        self.closeRequest('1')
        self.closeRequest('2')
        self.closeRequest('3')
        self.closeRequest('4')
        self.closeRequest('5')
        self.closeRequest('6')
        

    def dismissPreview(self, camera_number):
        dismissed_until = time() + self._dismissed_duration
        if self._dismissed_behavior == 0:   # Dismiss All
            self.dismissed_time[0] = dismissed_until
            self.dismissAllPreviews()
        else:                               # Individual Only
            self.dismissed_time[int(camera_number)] = dismissed_until

    def clear_dismissedPreview(self, camera_number):
        self.dismissed_time[int(camera_number)] = 0

    def previewDismissed(self, camera_number):
        if self._dismissed_behavior == 0:   # Dismiss All
            if self.dismissed_time[0] == 0:
                return False
            if time() > self.dismissed_time[0]:
                self.clear_dismissedPreview(0)
                return False
        else:                               # Individual Only
            if self.dismissed_time[int(camera_number)] == 0:
                return False
            if time() > self.dismissed_time[int(camera_number)]:
                self.clear_dismissedPreview(camera_number)
                return False
        return True


    # Used to determine if the window in focus is allowed to lose focus due to a preview window opening
    def checkWindowID(self):
        current_dialog_id = getCurrentWindowDialogId()
        current_window_id = getCurrentWindowId()

        for window_id in self._preview_disabled_window_id:
            if current_window_id == window_id or current_dialog_id == window_id:
                return True
        return False


    # Function that determines if a preview is allowed to be shown considering the global state
    def previewAllowed(self, camera_number):
        allowed = not (self.playingCamera(camera_number) or self.previewDismissed(camera_number) or self.checkWindowID() or self.toggledPreview())
        return (not self.previewOpened(camera_number)) and allowed

    #Request to test by @mrjd in forum
    def overrideURL(self, camera_number, url):
        Window(10000).setProperty('SR_urlOverride_%s' %camera_number, url)
        
    def clear_overrideURL(self, camera_number):
        Window(10000).clearProperty('SR_urlOverride_%s' %camera_number)

    def get_overrideURL(self, camera_number):
        return Window(10000).getProperty('SR_urlOverride_%s' %camera_number)



if __name__ == "__main__":
    pass
