"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

Service loop which enables preview window capability
"""

import xbmc, xbmcaddon, xbmcvfs
import threading, time, os, Queue, sys
from resources.lib import monitor, previewgui, settings, utils
from resources.lib.ipcam_api_wrapper import CameraAPIWrapper as Camera

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

        
              
class CameraPreviewThread(threading.Thread):
    """
    This class is a stoppable thread.  It controls the entire process for a single camera.
    Each camera will check the status of itself if it is playing in the main player.  It calls an image
    worker thread to update it's image
    """
    
    def __init__(self, camera):
        super(CameraPreviewThread, self).__init__()
        self._stop = False
        self.camera = camera
        
    def run(self):
        """ This runs the main loop for the camera """

        #Reset PTZ Camera on Service Start
        self.camera.resetLocation()

        # Settings
        check_interval = settings.getSetting_int('interval', self.camera.number)
        dur_service = settings.getSetting_int('dur_service', self.camera.number)
        dur_script = settings.getSetting_int('dur_script', self.camera.number)
        p_service = settings.getSetting_int('p_service', self.camera.number)
        p_script = settings.getSetting_int('p_script', self.camera.number)
        p_scripttoggle = settings.getSetting_int('p_scripttoggle', self.camera.number)
        self.motion_enabled, self.sound_enabled = settings.getEnabledAlarms(self.camera.number)
        trigger_interval = self.camera.getTriggerInterval(self.motion_enabled, self.sound_enabled)
            
        # Creates the Window to be used until Service is stopped       
        self.previewWindow = previewgui.CameraPreviewWindow(self.camera, monitor)

        ### MAIN LOOP ###
        
        durationTime = 0
        
        while not monitor.abortRequested() and not self.stopped():

            manual_override = monitor.script_override(self.camera.number)
            alarmActive = False

            if monitor.preview_not_open_allowed(self.camera.number):
                '''
                PREVIEW WINDOW IS CURRENTLY CLOSED
                This decision is used to determine how and when the window will be opened.
                '''

                if not manual_override:
                    #If Script was called, we don't care about the alarm state  
                    alarmActive = self.alarmStateHealthCheck()
                    
                
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

                    
                    if not monitor.preview_window_opened(self.camera.number):
                        #Only open the window if it's not already open
                        utils.log(2, 'SERVICE  :: Camera %s - Preview window is opening' %self.camera.number)
                        #q.put([self.previewWindow, self.camera])    
                        self.previewWindow.start()
                    

                            
            
            elif monitor.preview_window_opened(self.camera.number):
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
                    
                    alarmActive = self.alarmStateHealthCheck()
                    
                    if not alarmActive:
                        #Alarm is not active, so check if duration is exceeded
                        
                        if durationTime < time.time():
                            self.previewWindow.stop()
                            utils.log(2, 'SERVICE  :: Camera %s - The alarm is no longer detected.  The preview window will close.' %self.camera.number)   

                        else:
                            utils.log(2, 'SERVICE  :: Camera %s - Preview window is expected to close in %d seconds.' %(self.camera.number, (1 - (time.time() - durationTime))))

                    
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
                        self.previewWindow.stop()
                        utils.log(2, 'SERVICE  :: Camera %s - The alarm is no longer detected.  The preview window will close.' %self.camera.number)   

                    else:
                        utils.log(2, 'SERVICE  :: Camera %s - Preview window is expected to close in %d seconds.' %(self.camera.number, (1 - (time.time() - durationTime))))


               
                else:
                    '''
                    Close Conditions:
                    - No Alarm is Detected
                    - Manual
                    '''

                    #Set duration to 0 because we don't care about it
                    durationTime = 0

                    if (not manual_override and p_service == 3): 
                        
                        alarmActive = self.alarmStateHealthCheck()
                          
                        if not alarmActive:  
                            self.previewWindow.stop()
                            utils.log(2, 'SERVICE  :: Camera %s - The alarm is no longer detected.  The preview window will close.' %self.camera.number)



            # Sleep Logic - Includes logic to help detect if window is being opened by script instead of trigger
            if not alarmActive:
                sleep = check_interval              
            else:
                sleep = trigger_interval - 1

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
                - External Request to Close Window Occurs
                '''
                
                if monitor.requested_to_close_window(self.camera.number):
                    self.previewWindow.close()
                    
                if not manual_override and monitor.script_override(self.camera.number):
                    # If script wasn't called, and now it is so exit so it can be opened.
                    break
                
                window_opened = monitor.preview_window_opened(self.camera.number)

                if window_opened:
                    #Skip if duration is set as 0, since we aren't checking duration
                    if durationTime > 0:
                        # Duration check on opened windows.
                        if durationTime < time.time() and not alarmActive:     
                            self.previewWindow.stop()
                            #Don't break, because we still want the interval

                elif p_scripttoggle == 1:
                    # Toggles Preview open/closed if called multiple times from script - if set in settings
                    self.previewWindow.close()

                monitor.waitForAbort(.5)        
                x += 1

        ### /MAIN LOOP ###
  
        if monitor.preview_window_opened(self.camera.number):
            self.previewWindow.stop()
            del self.previewWindow
     
        utils.log(1, 'SERVICE  :: **SHUTDOWN** Camera %s - Stopped.' %self.camera.number)
        

    def alarmStateHealthCheck(self):
        """ Function to determine state of alarms on cameras, and also connectivity health of camera """

        # Non-alarm enabled or Generic IP Cameras return this
        if not self.motion_enabled and not self.sound_enabled:
            return False
        
        alarmActive = False  
        success_code, alarmActive, alarm = self.camera.is_alarm_active(self.motion_enabled, self.sound_enabled)

        ### Health Check code for Foscam Camera ###
        if success_code != 0:       

            #Timeout is ~20 seconds before determining camera is not connected  
            for x in range(1,2):
                
                utils.log(2, 'SERVICE  :: Camera %s did not give response 0, gave response %d.  Retry # %d in 5 seconds' %(self.camera.number, success_code, x))
                monitor.waitForAbort(5)
                success_code, alarmActive, alarm = self.camera.is_alarm_active(self.motion_enabled, self.sound_enabled)      

                if success_code == 0:  
                    break

            #Camera is not connected, so notify the user
            if success_code != 0:

                self.previewWindow.close()
                utils.notify(utils.translation(32222) %self.camera.number)   
                monitor.cache_set_test_result(self.camera.number, success_code)

                #Loop to keep retrying the connection ever 60 seconds
                while success_code != 0 and not monitor.abortRequested():
                    
                    utils.log(3, 'SERVICE  :: Camera %s did not give response 0, gave response %d.  60 seconds for next retry. ' %(self.camera.number, success_code))
                    monitor.waitForAbort(60)    
                    success_code, alarmActive, alarm = self.camera.is_alarm_active(self.motion_enabled, self.sound_enabled)

                utils.notify(utils.translation(32223) %self.camera.number)
                monitor.cache_set_test_result(self.camera.number, success_code)
                
                #Reset PTZ Camera on Service Start
                self.camera.resetLocation()
                    
            ### End of Health Check code for Foscam HD camera ###


        if alarmActive:
            utils.log(2, 'SERVICE  :: Camera {0} - Alarm is active. ({1}ed).'.format(self.camera.number, alarm))
                              
        return alarmActive
    
                                           
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

            utils.log(2, 'SERVICE  :: Camera %s;  Enabled: %s;  Preview Enabled: %s' %(camera_number, settings.enabled_camera(camera_number), settings.enabled_preview(camera_number)))
            if settings.enabled_camera(camera_number):
                camera = Camera(camera_number)

                if settings.enabled_preview(camera_number):
                    
                    if camera.Connected(monitor, useCache=False):

                        #wt = threading.Thread(target = previewgui.ImageWorker, args = (monitor, q))                  
                        #wt.daemon = True         
                        #wt.start()

                        t = CameraPreviewThread(camera)
                        t.daemon = True 
                        self.threads.append(t)
                        t.start()

                        utils.log(1, 'SERVICE  :: Camera %s thread started.' %camera_number)

                    else:
                        utils.log(1, 'SERVICE  :: Preview for Camera %s did not start because it is not properly configured.' %camera_number)
                        utils.notify('Error Connecting to Camera %s.' %camera_number)
                
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
                                       
        #with q.mutex:
        #    q.queue.clear()
                                       
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
    utils.log(1, 'SERVICE  :: Python Version: %s;  At Least 2.7: %s' %(sys.version, utils._atleast_python27))
    instance = service()
    instance.run(new_instance) 


if __name__ == "__main__":
    #q = Queue.Queue(maxsize=0)
                                               
    monitor = monitor.AddonMonitor()
    start()
    monitor.waitForAbort(1)
    utils.cleanup_images()
        



