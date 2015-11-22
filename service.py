"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

Service loop which enables preview window capability
"""

import xbmc, xbmcaddon, xbmcvfs
import threading, time, os, Queue, sys
from resources.lib import monitor, camerapreview, settings, utils
from resources.lib.ipcam_api_wrapper import CameraAPIWrapper as Camera

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

              
class CameraPreviewThread(threading.Thread):
    """
    This class is a stoppable thread.  It controls the entire process for a single camera.
    Each camera will check the status of itself if it is playing in the main player.  It calls an image
    worker thread to update it's image
    """
    
    def __init__(self, camera, monitor):
        super(CameraPreviewThread, self).__init__()
        self._stop = False
        self.camera = camera
        self.monitor = monitor
        
    def run(self):
        """ This runs the main loop for the camera """

        #Reset PTZ Camera on Service Start
        self.camera.resetLocation()

        # Settings
        check_interval = settings.getSetting_int('interval', self.camera.number)
        cond_service = settings.getSetting_int('cond_service', self.camera.number)
        self.motion_enabled, self.sound_enabled = settings.getEnabledAlarms(self.camera.number)
        trigger_interval = self.camera.getTriggerInterval(self.motion_enabled, self.sound_enabled)

        if trigger_interval < 1:    # Fix for Foscam Cameras that apparently get the data messed up
            trigger_interval = check_interval


        ### MAIN LOOP ###
        while not self.monitor.abortRequested() and not self.monitor.stopped():
            
            alarmActive = self.alarmStateHealthCheck()

            #PREVIEW WINDOW IS CURRENTLY CLOSED
            if self.monitor.previewAllowed(self.camera.number):

                #Open Condition: Alarm is Detected
                if alarmActive:
                    self.monitor.openRequest(self.camera.number)
                    utils.log(2, 'Camera %s :: Alarm is detected. Preview window is opening' %self.camera.number)
                    

            #PREVIEW WINDOW IS OPEN
            elif self.monitor.previewOpened(self.camera.number):

                #Close Condition: No Alarm is Detected
                if cond_service == camerapreview.CONDITION_NO_ALARM and not self.monitor.openRequest_manual(self.camera.number): 
                    if not alarmActive:  
                        self.monitor.closeRequest(self.camera.number)
                        utils.log(2, 'Camera %s :: The alarm is no longer detected.  The preview window will close.' %self.camera.number)


            # Sleep Logic
            if not alarmActive:
                sleep = check_interval              
            else:
                sleep = trigger_interval - 1

            #print '%s, %s, %d, %d, %d, %s' %(self.camera.number, self.monitor.previewOpened(self.camera.number), sleep, check_interval, trigger_interval, alarmActive)
            self.monitor.waitForAbort(sleep)
        ### /MAIN LOOP ###

  
        if self.monitor.previewOpened(self.camera.number):
            self.monitor.closeRequest(self.camera.number)
     
        utils.log(1, 'Camera %s :: **SERVICE SHUTDOWN** :: Thread Stopped.' %self.camera.number)


        

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
                
                utils.log(2, 'Camera %s :: SERVICE HEALTH CHECK :: Did not receive response 0, received response %d.  Retry # %d in 5 seconds' %(self.camera.number, success_code, x))
                self.monitor.waitForAbort(5)
                success_code, alarmActive, alarm = self.camera.is_alarm_active(self.motion_enabled, self.sound_enabled)      

                if success_code == 0:  
                    break

            #Camera is not connected, so notify the user
            if success_code != 0:

                self.monitor.closeRequest(self.camera.number)
                utils.notify(utils.translation(32222) %self.camera.number)   
                self.monitor.write_testResult(self.camera.number, success_code)

                #Loop to keep retrying the connection ever 60 seconds
                x = 0
                while success_code != 0:
                    if self.monitor.abortRequested() or self.monitor.stopped():
                        return False
                    
                    if x > 60:
                        x = 0
                        utils.log(3, 'Camera %s :: SERVICE HEALTH CHECK  :: Did not receive response 0, received response %d.  Retrying every 60 seconds.' %(self.camera.number, success_code))
                        success_code, alarmActive, alarm = self.camera.is_alarm_active(self.motion_enabled, self.sound_enabled)
                    
                    self.monitor.waitForAbort(1)
                    x += 1

                utils.notify(utils.translation(32223) %self.camera.number)
                self.monitor.write_testResult(self.camera.number, success_code)
                
                #Reset PTZ Camera on Service Start
                self.camera.resetLocation()
                    
            ### End of Health Check code for Foscam HD camera ###


        if alarmActive:
            self.monitor.set_alarmActive(self.camera.number)
            utils.log(2, 'Camera %s :: Alarm detected: (%sed).' %(self.camera.number, alarm))
            return True
    
        self.monitor.clear_alarmActive(self.camera.number)   
        return False


                                       
class service():
    """
    This is the main service loop which controls the entire process globally,
    and creates all of the threads.
    """    
    
    def run(self, monitor):
        self.monitor = monitor
        self.monitor.reset()
        preview_enabled_cameras = []        
        self.threads = []
        
        for camera_number in "123456":

            utils.log(2, 'Camera %s :: Enabled: %s;  Preview Enabled: %s' %(camera_number, settings.enabled_camera(camera_number), settings.enabled_preview(camera_number)))
            if settings.enabled_camera(camera_number):
                camera = Camera(camera_number)

                if settings.enabled_preview(camera_number):
                    
                    if camera.Connected(self.monitor, useCache=False):

                        previewWindow = threading.Thread(target = camerapreview.CameraPreviewWindow, args = (camera, self.monitor, ))
                        previewWindow.daemon = True
                        previewWindow.start()
                        
                        t = CameraPreviewThread(camera, self.monitor, )
                        t.daemon = True 
                        self.threads.append(t)
                        t.start()

                        utils.log(1, 'Camera %s :: Preview Thread started.' %camera_number)

                    else:
                        utils.log(1, 'Camera %s :: Preview thread did not start because camera is not properly configured.' %camera_number)
                        utils.notify('Error Connecting to Camera %s.' %camera_number)
                
        utils.notify(utils.translation(32224))  #Service Started
        
        xbmc.executebuiltin('Container.Refresh')
        
        while not self.monitor.stopped() and not self.monitor.abortRequested():
            self.monitor.waitForAbort(1)

        if self.monitor.stopped() and not self.monitor.abortRequested():
            utils.notify(utils.translation(32225))  #Service Restarting
            self.restart()

        '''                             
        else:
            utils.notify('Service stopped.')
            self.stop()
            '''
                                     

    def restart(self):
        self.stop()
        self.monitor.waitForAbort(2)                                     
        start()

    def stop(self):
        for t in self.threads:
            t.join()

                      

def start():
    """
    Function which starts the service.  Called on Kodi login as well as when restarted due to settings changes
    """
    
    settings.refreshAddonSettings()
    utils.log(1, 'SERVICE  :: **START**')
    utils.log(1, 'SERVICE  :: Log Level: %s' %utils.log_level())
    utils.log(1, 'SERVICE  :: Python Version: %s;  At Least 2.7: %s' %(sys.version, utils._atleast_python27))
    instance = service()
    instance.run(monitor) 


if __name__ == "__main__":                    
    monitor = monitor.AddonMonitor()
    start()
    monitor.waitForAbort(1)
    utils.cleanup_images()
        



