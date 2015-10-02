'''
   Notes about this file:
'''

import xbmc, xbmcaddon, xbmcvfs
import threading, time, os, Queue
from resources.lib import foscam, imaging, monitor, gui, settings

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')
__path__ = xbmc.translatePath('special://profile/addon_data/%s' %__addonid__ ).decode('utf-8')

          
class CameraPreviewThread(threading.Thread):
    '''
    This class is a stoppable thread.  It controls the entire process for a single camera.
    Each camera will check the status of itself if it is playing in the main player.  It calls an image
    worker thread to update it's image
    '''
    
    def __init__(self, camera):
        super(CameraPreviewThread, self).__init__()
        self._stop = False
        self.camera = camera
        
    def run(self):
        '''
        This runs the main loop for the camera
        '''
        
        camera_number = self.camera[0]
        snapshotURL = self.camera[6]
        motion_enabled = self.camera[17]
        sound_enabled = self.camera[18]
        duration = self.camera[14]
        check_interval = self.camera[19]
        trigger_interval = self.camera[21]
        
        print camera_number + " : Camera thread started"
        
        previewWindow = gui.CameraPreviewWindow(self.camera, monitor)
        
        with foscam.Camera(self.camera) as connected_camera:
            
            while not monitor.abortRequested() and not self.stopped():

                if monitor.preview_allowed(camera_number):

                    alarmActive = False
                    alarmState = connected_camera.get_device_state()
                    
                    if alarmState:                                          
                        for alarm, enabled in (('motionDetect', motion_enabled), ('sound', sound_enabled)):
                            if enabled:
                                param = "{0}Alarm".format(alarm)
                                if alarmState[param] == 2:
                                    alarmActive = True
                                    print ('Camera {0} - Alarm is active. ({1}ed).').format(camera_number, alarm)
                                    break                        
                    
                    if alarmActive:                                         
                        durationTime = time.time() + duration               

                        if not monitor.preview_window_opened(camera_number):
                            print ('Camera {0} - Preview window is opening.').format(camera_number)
                            q.put([self.camera, previewWindow, True])
                            previewWindow.start()
                            
                    else:
                        if monitor.preview_window_opened(camera_number):                                      
                            print  ('Camera {0} - Preview window is expected to close in {1} seconds.').format(camera_number, 1 - (time.time() - durationTime))
                            if durationTime < time.time():
                                previewWindow.stop()
                                print ('Camera {0} - The alarm is no longer detected.  The preview window will close.').format(camera_number)
                                
                    if alarmActive:  
                        sleep = int(trigger_interval - 1)
                    else:
                        sleep = int(check_interval)

                    monitor.waitForAbort(sleep)
                    
                else: 
                    if monitor.preview_window_opened(camera_number):
                        previewWindow.stop()
                    monitor.waitForAbort(1)
     
        print ('**SHUTDOWN** Camera {0} - Stopped.').format(camera_number)
        

    def stop(self):
        self._stop = True

    def stopped(self):
        return self._stop
                                       


def CheckEnabledCameras():
    '''
    This function gets the user settings and camera configurations and verifies at least
    one camera is enabled, and that at least one camera is enabled for preview
    '''
    
    preview_enabled_cameras = []   
    atLeastOneCamera, cameras = settings.getSettings('all')

    if atLeastOneCamera:
        for camera in cameras:
            preview_enabled = False
            
            if len(camera) > 14:
                preview_enabled = camera[13]
                
            if preview_enabled:
                preview_enabled_cameras.append(camera)
                
    if len(preview_enabled_cameras) > 0:
        return True, preview_enabled_cameras

    else:
        return False, None

                                       
class service():
    '''
    This is the main service loop which controls the entire process globally,
    and creates all of the threads.
    '''    
    
    def run(self, instance):
        self.instance = instance
        
        preview_enabled_cameras = []        
        self.threads = []

        monitor.disable_changes()   
        configured_ok = False
        configured_ok, preview_enabled_cameras = CheckEnabledCameras()
        
        monitor.waitForAbort(2)             
        monitor.reset()
        
        if configured_ok:
            x = 0
            for camera in preview_enabled_cameras:
                t = threading.Thread(target = imaging.ImageWorker, args = (monitor, q, __path__))
                t.daemon = True
                t.start()
                
                t = CameraPreviewThread(camera)
                self.threads.append(t)
                t.start()
 
        while not monitor.stopped() and not monitor.abortRequested():
            monitor.waitForAbort(1)

        if monitor.stopped() and not monitor.abortRequested():
            self.restart()
                                     
        else:     
            self.stop()
                                     

    def restart(self):
        self.stop()                              
        new_instance = self.instance + 1
        monitor.waitForAbort(5)
                                       
        with q.mutex:
            q.queue.clear()
                                       
        start(new_instance)

    def stop(self):
        for t in self.threads:
            t.stop()
            t.join()


                      


def start(new_instance = 0):
    '''
    Function which starts the service.  Called on Kodi login as well as when restarted due to settings changes
    '''
    
    print ('**START** Instance {0} - Starting a new service instance.').format(new_instance)
    instance = service()
    instance.run(new_instance)

 


if __name__ == "__main__":
    q = Queue.Queue(maxsize=0)
                                       
    if not xbmcvfs.exists(__path__):
        try:
            xbmcvfs.mkdir(__path__)
        except:
            pass
        
    monitor = monitor.AddonMonitor()
    start()
    
    for i in xbmcvfs.listdir(__path__)[1]:
        if i <> "settings.xml":
            xbmcvfs.delete(os.path.join(__path__, i))
        



