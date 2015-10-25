"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

Service loop which enables preview window capability
"""

import xbmc, xbmcaddon, xbmcvfs
import threading, time, os, Queue
from resources.lib import foscam2, monitor, previewgui, settings, utils

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

        
def alarmStateHealthCheck(camera_settings, motion_enabled, sound_enabled):
    """ Function to determine state of alarms on cameras, and also connectivity health of camera """

    # Non-alarm enabled or Generic IP Cameras return this
    if not motion_enabled and not sound_enabled:
        return False
    
    alarmActive = False
    
    with foscam2.FoscamCamera(camera_settings, verbose=False) as camera:
        success_code, alarmActive, alarm = camera.is_alarm_active(motion_enabled, sound_enabled)


        ### Health Check code for Foscam Camera ###
        if success_code != 0:       

            #Timeout is 30 seconds before determining camera is not connected  
            for x in range(1,3):
                
                utils.log(2, 'SERVICE  :: Camera %s did not give response 0, gave response %d.  Retry # %d in 5 seconds' %(camera_settings[0], success_code, x))
                monitor.waitForAbort(5)
                success_code, alarmActive, alarm = camera.is_alarm_active(motion_enabled, sound_enabled)      

                if success_code == 0:  
                    break

            #Camera is not connected, so notify the user
            if success_code != 0:
                
                settings.notify(utils.translation(32222) %camera_settings[0])
                monitor.cache_set_test_result(camera_settings[0], success_code)

                #Loop to keep retrying the connection ever 60 seconds
                while success_code != 0 and not monitor.abortRequested():
                    
                    utils.log(3, 'SERVICE  :: Camera %s did not give response 0, gave response %d.  60 seconds for next retry. ' %(camera_settings[0], success_code))
                    monitor.waitForAbort(60)    
                    success_code, alarmActive, alarm = camera.is_alarm_active(motion_enabled, sound_enabled)

                settings.notify(utils.translation(32223) %camera_settings[0])
                monitor.cache_set_test_result(camera_settings[0], success_code)
                
                #Reset PTZ Camera on Service Start
                settings.resetLocation(camera_settings[0])
                
        ### End of Health Check code for Foscam HD camera ###


    if alarmActive:
        camera_number = camera_settings[0]
        utils.log(2, 'SERVICE  :: Camera {0} - Alarm is active. ({1}ed).'.format(camera_number, alarm))
                          
    return alarmActive

               
class CameraPreviewThread(threading.Thread):
    """
    This class is a stoppable thread.  It controls the entire process for a single camera.
    Each camera will check the status of itself if it is playing in the main player.  It calls an image
    worker thread to update it's image
    """
    
    def __init__(self, camera_settings):
        super(CameraPreviewThread, self).__init__()
        self._stop = False
        self.camera_settings = camera_settings
        
    def run(self):
        """ This runs the main loop for the camera """
        
        camera_number = self.camera_settings[0]

        #Reset PTZ Camera on Service Start
        settings.resetLocation(camera_number)

        # Settings
        check_interval = settings.getSetting_int('interval', camera_number)
        dur_service = settings.getSetting_int('dur_service', camera_number)
        dur_script = settings.getSetting_int('dur_script', camera_number)
        p_service = settings.getSetting_int('p_service', camera_number)
        p_script = settings.getSetting_int('p_script', camera_number)
        p_scripttoggle = settings.getSetting_int('p_scripttoggle', camera_number)
        motion_enabled, sound_enabled = settings.getEnabledAlarms(camera_number)
        trigger_interval = settings.getTriggerInterval(camera_number, self.camera_settings, motion_enabled, sound_enabled)
            
        # Creates the Window to be used until Service is stopped       
        previewWindow = previewgui.CameraPreviewWindow(self.camera_settings, monitor)

        ### MAIN LOOP ###
        
        durationTime = 0
        
        while not monitor.abortRequested() and not self.stopped():

            manual_override = monitor.script_override(camera_number)
            alarmActive = False

            if monitor.preview_not_open_allowed(camera_number):
                '''
                PREVIEW WINDOW IS CURRENTLY CLOSED
                This decision is used to determine how and when the window will be opened.
                '''

                if not manual_override:
                    #If Script was called, we don't care about the alarm state  
                    alarmActive = alarmStateHealthCheck(self.camera_settings, motion_enabled, sound_enabled)
                    
                
                if alarmActive or manual_override:
                    '''
                    Open Conditions:
                    - Alarm is active (and alarm triggers are enabled)
                    - Manually from script
                    '''
                    
                    if not manual_override:
                        durationTime = time.time() + dur_service 
                    else:
                        durationTime = time.time() + dur_script

                    
                    if not monitor.preview_window_opened(camera_number):
                        #Only open the window if it's not already open
                        utils.log(2, 'SERVICE  :: Camera %s - Preview window is opening' %camera_number)
                        q.put([camera_number, previewWindow])    
                        previewWindow.start()
                    

                            
            
            elif monitor.preview_window_opened(camera_number):
                '''
                PREVIEW WINDOW IS OPEN
                This decision is used to determine how and when the window will be closed.
                '''
                
                if (not manual_override and p_service == 0) or (manual_override and p_script == 0):
                    '''
                    Close Conditions:
                    - Duration Exceeded and No Alarm is Detected
                    - Manual
                    '''
                    
                    alarmActive = alarmStateHealthCheck(self.camera_settings, motion_enabled, sound_enabled)
                    
                    if not alarmActive:
                        #Alarm is not active, so check if duration is exceeded
                        
                        if durationTime < time.time():
                            previewWindow.stop()
                            utils.log(2, 'SERVICE  :: Camera %s - The alarm is no longer detected.  The preview window will close.' %camera_number)   

                        else:
                            utils.log(2, 'SERVICE  :: Camera %s - Preview window is expected to close in %d seconds.' %(camera_number, (1 - (time.time() - durationTime))))

                    
                    else:
                        #Alarm is still active, so reset duration
                        
                        if not manual_override:
                            durationTime = time.time() + dur_service 
                        else:
                            durationTime = time.time() + dur_script
                        
                
                elif (not manual_override and p_service == 1) or (manual_override and p_script == 1):
                    '''
                    Close Conditions:
                    - Duration Exceeded
                    - Manual
                    '''
                    
                    #Set alarm state to False because we don't care about it
                    alarmActive = False

                    if durationTime < time.time():
                        previewWindow.stop()
                        utils.log(2, 'SERVICE  :: Camera %s - The alarm is no longer detected.  The preview window will close.' %camera_number)   

                    else:
                        utils.log(2, 'SERVICE  :: Camera %s - Preview window is expected to close in %d seconds.' %(camera_number, (1 - (time.time() - durationTime))))


               
                else:
                    '''
                    Close Conditions:
                    - No Alarm is Detected
                    - Manual
                    '''

                    #Set duration to 0 because we don't care about it
                    durationTime = 0

                    if (not manual_override and p_service == 3): 
                        
                        alarmActive = alarmStateHealthCheck(self.camera_settings, motion_enabled, sound_enabled)
                          
                        if not alarmActive:  
                            previewWindow.stop()
                            utils.log(2, 'SERVICE  :: Camera %s - The alarm is no longer detected.  The preview window will close.' %camera_number)



            # Sleep Logic - Includes logic to help detect if window is being opened by script instead of trigger
            if not alarmActive:
                sleep = check_interval              
            else:
                sleep = trigger_interval

            x = 1
            sleep = sleep * 2

        
            while not monitor.abortRequested() and not self.stopped() and x < sleep:
                '''
                SLEEP
                - Processes the interval between each loop

                Exit Conditions:
                - Script is called to open the window, if it is not already open

                Other Actions:
                - Window is open, alarm is not active, and duration is exceeded; Close Window
                '''
                
                if not manual_override and monitor.script_override(camera_number):
                    # If script wasn't called, and now it is so exit so it can be opened.
                    break
                
                window_opened = monitor.preview_window_opened(camera_number)

                if window_opened:
                    #Skip if duration is set as 0, since we aren't checking duration
                    if durationTime > 0:
                        # Duration check on opened windows.
                        if durationTime < time.time() and not alarmActive:     
                            previewWindow.stop()
                            #Don't break, because we still want the interval

                elif p_scripttoggle == 1:
                    # Toggles Preview open/closed if called multiple times from script - if set in settings
                    previewWindow.close()

                monitor.waitForAbort(.5)        
                x += 1

        ### /MAIN LOOP ###
  
        if monitor.preview_window_opened(camera_number):
            previewWindow.stop()
            del previewWindow
     
        utils.log(1, 'SERVICE  :: **SHUTDOWN** Camera %s - Stopped.' %camera_number)
        

    def stop(self):
        self._stop = True

    def stopped(self):
        return self._stop
                                       

                                       
class service():
    """
    This is the main service loop which controls the entire process globally,
    and creates all of the threads.
    """    
    
    def run(self, instance):
        monitor.reset()
        self.instance = instance
        preview_enabled_cameras = []        
        self.threads = []
        
        for camera_number in "1234":

            utils.log(2, 'SERVICE  :: Camera %s;  Enabled: %s' %(camera_number, settings.enabled_camera(camera_number)))
            if settings.enabled_camera(camera_number):
                camera_settings = settings.getBasicSettings(camera_number, monitor, useCache=False)

                utils.log(2, 'SERVICE  :: Camera %s;  Preview Enabled: %s;  Settings: %s' %(camera_number, settings.enabled_preview(camera_number), camera_settings))
                if settings.enabled_preview(camera_number):
                    
                    if camera_settings :

                        wt = threading.Thread(target = previewgui.ImageWorker, args = (monitor, q))                  
                        wt.daemon = True         
                        wt.start()

                        t = CameraPreviewThread(camera_settings)
                        t.daemon = True 
                        self.threads.append(t)
                        t.start()

                        utils.log(1, 'SERVICE  :: Camera %s thread started.' %camera_number)

                    else:
                        utils.log(1, 'SERVICE  :: Preview for Camera %s did not start because it is not properly configured.' %camera_number)
                
        utils.notify(utils.translation(32224))  #Service Started
        
        xbmc.executebuiltin('Container.Refresh')
        
        while not monitor.stopped() and not monitor.abortRequested():
            monitor.waitForAbort(1)

        if monitor.stopped() and not monitor.abortRequested():
            utils.notify(utils.translation(32225))  #Service Restarting
            self.restart()

        '''                             
        else:
            utils.notify('Service stopped.')
            self.stop()
            '''
                                     

    def restart(self):
        self.stop()
        monitor.waitForAbort(3)
        new_instance = self.instance + 1
                                       
        with q.mutex:
            q.queue.clear()
                                       
        start(new_instance)

    def stop(self):
        for t in self.threads:
            t.stop()
            t.join()

                      


def start(new_instance = 0):
    """
    Function which starts the service.  Called on Kodi login as well as when restarted due to settings changes
    """
    
    settings.refreshAddonSettings()
    utils.log(1, 'SERVICE  :: **START** Instance %d - Starting a new service instance.' %new_instance)
    utils.log(1, 'SERVICE  :: Log Level: %s' %utils.__log_level__)
    instance = service()
    instance.run(new_instance) 


if __name__ == "__main__":
    q = Queue.Queue(maxsize=0)
                                               
    monitor = monitor.AddonMonitor()
    start()
    monitor.waitForAbort(1)
    utils.cleanup_images()
        



