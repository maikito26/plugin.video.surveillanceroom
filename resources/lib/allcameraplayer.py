"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to show all cameras on fullscreen
"""

import xbmc, xbmcaddon, xbmcvfs, xbmcgui
import threading, os,  requests#, time
from urllib import urlretrieve
import settings, monitor, utils
from resources.lib.ipcam_api_wrapper import CameraAPIWrapper as Camera
import socket
TIMEOUT = settings.getSetting_int('request_timeout')
socket.setdefaulttimeout(TIMEOUT)

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

_datapath = xbmc.translatePath(('special://profile/addon_data/{0}').format(__addonid__)).decode('utf-8')
_loader = xbmc.translatePath(('special://home/addons/{0}/resources/media/loader_old.gif').format(__addonid__)).decode('utf-8')
_error = xbmc.translatePath(('special://home/addons/{0}/resources/media/error.png').format(__addonid__)).decode('utf-8')
_holder = xbmc.translatePath(('special://home/addons/{0}/resources/media/placeholder.jpg').format(__addonid__)).decode('utf-8')
_black = xbmc.translatePath('special://home/addons/%s/resources/media/black.png' %__addonid__ ).decode('utf-8')

ACTION_PREVIOUS_MENU = 10
ACTION_STOP = 13
ACTION_NAV_BACK = 92
ACTION_BACKSPACE = 110
      
monitor = monitor.AddonMonitor()

class AllCameraDisplay(xbmcgui.WindowDialog):
    """ Window class used to show all cameras on """
    
    def __init__(self):
        self.isRunning = True

        # Black Background
        background_fade_animation = [
                                    ('WindowOpen', ("effect=fade time=200")),
                                    ('WindowClose', ("effect=fade time=1500"))
                                    ]

        img = xbmcgui.ControlImage(0, 0, 1280, 720, filename = _black, aspectRatio = 0)
        self.addControl(img)
        img.setAnimations(background_fade_animation)

        # Individual Camera positions setup
        urls = []
        files = []
        imgs = []
        imgs2 = []
        
        coords = [  (0, 0, 640, 360),   
                    (640, 0, 640, 360),
                    (0, 360, 640, 360),
                    (640, 360, 640, 360) ]

        effect = ['slide', 'slide']
        time = [1200, 1000]
        tween = ['back', 'back']
        easing = ['Out', 'InOut']
        animations = [
                        [ ('WindowOpen', ("effect={0} start=-640,-360 time={1} tween={2} easing={3}").format( effect[0], time[0], tween[0], easing[0])),
                          ('WindowClose', ("effect={0} end=-640,-360 time={1} tween={2} easing={3}").format( effect[1], time[1], tween[1], easing[1] )) ],
                        [ ('WindowOpen', ("effect={0} start=640,-360 time={1} tween={2} easing={3}").format( effect[0], time[0], tween[0], easing[0] )),
                          ('WindowClose', ("effect={0} end=640,-360 time={1} tween={2} easing={3}").format( effect[1], time[1], tween[1], easing[1] )) ],
                        [ ('WindowOpen', ("effect={0} start=-640,360 time={1} tween={2} easing={3}").format( effect[0], time[0], tween[0], easing[0] )),
                          ('WindowClose', ("effect={0} end=-640,360 time={1} tween={2} easing={3}").format( effect[1], time[1], tween[1], easing[1] )) ],
                        [ ('WindowOpen', ("effect={0} start=640,360 time={1} tween={2} easing={3}").format( effect[0], time[0], tween[0], easing[0] )),
                          ('WindowClose', ("effect={0} end=640,360 time={1} tween={2} easing={3}").format( effect[1], time[1], tween[1], easing[1] )) ]
                        ]

        # Acquire all Enabled & Connected cameras
        enabled_cameras = settings.getAllEnabledCameras(monitor)

        # Logic to ensure enabled cameras are placed in the correct position
        threads = []
        for window_position in '1234':
            position = int(window_position) - 1

            # Sets the initial image to the loader gif
            img1 = xbmcgui.ControlImage(*coords[position], filename = _loader, aspectRatio = 0) 
            self.addControl(img1)  #Bug was seen here previously, hence the 'try' and this will need to be investigated in future
            img1.setAnimations(animations[position])

            # Connected and Enabled Camera
            if len(enabled_cameras) > position:
                img2 = xbmcgui.ControlImage(*coords[position], filename = '', aspectRatio = 0)
                self.addControl(img2)
                img2.setAnimations(animations[position])

                control = [img1, img2]

                with Camera(enabled_cameras[position]) as camera:
                    stream_type = camera.getStreamType(1)
                    url = camera.getStreamUrl(1, stream_type)
                    prefix = 'AllCamera'

                    if stream_type == 0:    #MJPEG
                        t = threading.Thread(target = self.getImagesMjpeg, args = (camera, url, control, prefix))
                        
                    elif stream_type == 2:  #MJPEG Interlaced
                        t = threading.Thread(target = self.getImagesMjpegInterlace, args = (camera, url, control, prefix))
                        
                    else:                   #Snapshot
                        t = threading.Thread(target = self.getImagesSnapshot, args = (camera, url, control, prefix))

                    threads.append(t)
                    t.start()
                

            # No Camera so set the place holder image    
            else:
                img1.setImage(_holder, useCache = False)  
                    
        if len(threads) > 0:
            self.doModal()    

            #while not monitor.abortRequested() and self.isRunning:       
            #    monitor.waitForAbort(1)

            monitor.maybe_resume_previous()
            monitor.waitForAbort(1)
            utils.remove_leftover_images('AllCamera')
            
        else:
            utils.log(2, 'Unable to start All Camera Player')
            utils.notify('Player did not start.  Check camera settings.')


    def getImagesSnapshot(self, camera, url, control, prefix):
        """ Update camera position with snapshots """
        
        x = 0
        while not monitor.abortRequested() and self.isRunning:
            
            try:
                filename = os.path.join(_datapath, '%s_%s.%d.jpg') %(prefix, camera.number, x)
                urlretrieve(url, filename)
                
                if os.path.exists(filename): 
                    control[0].setImage(filename, useCache = False)                
                    xbmcvfs.delete(os.path.join(_datapath, '%s_%s.%d.jpg') %(prefix, camera.number, x - 1))
                    control[1].setImage(filename, useCache = False)
                    x += 1
                    
            except Exception, e:
                utils.log(3, 'Camera %s - Error on MJPEG: %s' %(camera.number, e))
                control[0].setImage(_error, useCache = False)
                return


    def getImagesMjpeg(self, camera, url, control, prefix):
        """ Update camera position with mjpeg frames """
        
        try:
            stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            control[0].setImage(_error, useCache = False)
            return
            
        x = 0
        while not monitor.abortRequested() and self.isRunning:
            
            filename = os.path.join(_datapath, '%s_%s.%d.jpg') %(prefix, camera.number, x)
            filename_exists = utils.get_mjpeg_frame(stream, filename)

            if filename_exists:
                control[0].setImage(filename, useCache = False)
                control[1].setImage(filename, useCache = False)
                xbmcvfs.delete(os.path.join(_datapath, '%s_%s.%d.jpg') %(prefix, camera.number, x - 1))
                x += 1
                
            else:
                utils.log(3, 'Camera %s - Error on MJPEG' %camera.number)
                control[0].setImage(_error, useCache = False)
                return


    def getImagesMjpegInterlace(self, camera, url, control, prefix):
        """ Update camera position with interlaced mjpeg frames """

        try:
            stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            control[0].setImage(_error, useCache = False)
            return
            
        x = 0
        while not monitor.abortRequested() and self.isRunning:
            
            filename = os.path.join(_datapath, '%s_%s.%d.jpg') %(prefix, camera.number, x)
            filename_exists = utils.get_mjpeg_frame(stream, filename)

            if filename_exists:
                if x % 2 == 0:  #Interlacing for flicker reduction/elimination
                    control[0].setImage(filename, useCache = False)
                else:
                    control[1].setImage(filename, useCache = False)
                xbmcvfs.delete(os.path.join(_datapath, '%s_%s.%d.jpg') %(prefix, camera.number, x - 2))
                x += 1
                
            else:
                utils.log(3, 'Camera %s - Error on MJPEG' %camera.number)
                control[0].setImage(_error, useCache = False)
                return
    

    def onAction(self, action):        
        if action in (ACTION_PREVIOUS_MENU, ACTION_STOP, ACTION_NAV_BACK, ACTION_BACKSPACE):
            self.isRunning = False
            monitor.waitForAbort(.2)
            self.close()
            

def play():
    """ Main function to show all cameras """
    
    if settings.atLeastOneCamera():
        monitor.set_playingCamera('0')
        PlayerWindow = AllCameraDisplay()
        del PlayerWindow
        monitor.clear_playingCamera('0')
        
    else:
        utils.log(2, 'No Cameras Configured')
        utils.notify('You must configure a camera first')

    


if __name__ == "__main__":
    play()
