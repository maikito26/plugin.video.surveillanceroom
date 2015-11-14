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
        cond_service = settings.getSetting_int('cond_service', self.camera.number)
        self.motion_enabled, self.sound_enabled = settings.getEnabledAlarms(self.camera.number)
        trigger_interval = self.camera.getTriggerInterval(self.motion_enabled, self.sound_enabled)


        ### MAIN LOOP ###
        while not monitor.abortRequested() and not monitor.stopped():
            alarmActive = True
            if not monitor.openRequested_manual(self.camera.number):
                alarmActive = self.alarmStateHealthCheck()

            #PREVIEW WINDOW IS CURRENTLY CLOSED
            if monitor.previewAllowed(self.camera.number):

                #Open Condition: Alarm is Detected
                if alarmActive:
                    monitor.openRequest(self.camera.number)
                    utils.log(2, 'SERVICE  :: Camera %s - Preview window is opening' %self.camera.number)
                    

            #PREVIEW WINDOW IS OPEN
            elif monitor.previewOpened(self.camera.number):

                #Close Condition: No Alarm is Detected
                if cond_service == previewgui.CONDITION_NO_ALARM: 
                    if not alarmActive:  
                        monitor.closeRequest(self.camera.number)
                        utils.log(2, 'SERVICE  :: Camera %s - The alarm is no longer detected.  The preview window will close.' %self.camera.number)


            # Sleep Logic
            if not alarmActive:
                sleep = check_interval              
            else:
                sleep = trigger_interval - 1

            monitor.waitForAbort(sleep)
        ### /MAIN LOOP ###

  
        if monitor.previewOpened(self.camera.number):
            monitor.closeRequest(self.camera.number)
     
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
                monitor.write_testResult(self.camera.number, success_code)

                #Loop to keep retrying the connection ever 60 seconds
                x = 0
                while success_code != 0 and not monitor.abortRequested() and not monitor.stopped():
                    if x > 60:
                        x = 0
                        utils.log(3, 'SERVICE  :: Camera %s did not give response 0, gave response %d.  Retrying every 60 seconds.' %(self.camera.number, success_code))
                        success_code, alarmActive, alarm = self.camera.is_alarm_active(self.motion_enabled, self.sound_enabled)
                    
                    monitor.waitForAbort(1)
                    x += 1

                utils.notify(utils.translation(32223) %self.camera.number)
                monitor.write_testResult(self.camera.number, success_code)
                
                #Reset PTZ Camera on Service Start
                self.camera.resetLocation()
                    
            ### End of Health Check code for Foscam HD camera ###


        if alarmActive:
            monitor.set_alarmActive(self.camera.number)
            utils.log(2, 'SERVICE  :: Camera {0} - Alarm is active. ({1}ed).'.format(self.camera.number, alarm))
            return True
    
        monitor.clear_alarmActive(self.camera.number)   
        return False
    
                                           
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
        
        for camera_number in "123456":

            utils.log(2, 'SERVICE  :: Camera %s;  Enabled: %s;  Preview Enabled: %s' %(camera_number, settings.enabled_camera(camera_number), settings.enabled_preview(camera_number)))
            if settings.enabled_camera(camera_number):
                camera = Camera(camera_number)

                if settings.enabled_preview(camera_number):
                    
                    if camera.Connected(monitor, useCache=False):

                        previewWindow = threading.Thread(target = previewgui.CameraPreviewWindow, args = (camera, monitor, ))
                        previewWindow.daemon = True
                        previewWindow.start()
                        
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
        



