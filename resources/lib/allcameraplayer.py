"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to show all cameras on fullscreen
"""

import xbmc, xbmcaddon, xbmcvfs, xbmcgui
import threading, os,  requests#, time
from urllib import urlretrieve
import settings, monitor, utils

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

        # Configure each Camera Position
        cameras = settings.getAllEnabledCameras(monitor)

        # Logic to ensure enabled cameras are placed in the correct position
        for camera_position in '1234':
            
            i = int(camera_position) - 1

            # Sets the initial image to the loader gif
            img1 = xbmcgui.ControlImage(*coords[i], filename = _loader, aspectRatio = 0) 
            try:
                self.addControl(img1)  #Bug was seen here previously, hence the 'try' and this will need to be investigated in future
            except:
                pass
            img1.setAnimations(animations[i])

            # Checks if there is another enabled camera
            if len(cameras) > i:
                print str(i) + ' ' + str(camera_position)
                print (len(cameras))

                img2 = xbmcgui.ControlImage(*coords[i], filename = '', aspectRatio = 0)
                try:
                    self.addControl(img2)
                except:
                    pass
                img2.setAnimations(animations[i])

                camera_number = cameras[i]
                stream_type = settings.getStreamType(1, camera_number)
                url = settings.getStreamUrl(1, camera_number, stream_type)

                control = [img1, img2]
                
                if stream_type == 0:    #MJPEG
                    t = threading.Thread(target=self.getImagesMjpeg, args=(camera_number, url, control))
                    
                elif stream_type == 2:  #MJPEG Interlaced
                    t = threading.Thread(target=self.getImagesMjpegInterlace, args=(camera_number, url, control))
                    
                else:                   #Snapshot
                    t = threading.Thread(target=self.getImagesSnapshot, args=(camera_number, url, control))
                    
                t.start()

            #elif enabled and not connected:
            #    img1.setImage(self.error, useCache=False)

            # No Camera so set the place holder image    
            else:
                img1.setImage(_holder, useCache=False)  
                    
        if len(cameras) > 0:
            # Update the global add-on setting and show the player onscreen
            monitor.set_camera_playing('All')
            self.show()    

            while not monitor.abortRequested() and self.isRunning:       
                monitor.waitForAbort(1)

            monitor.waitForAbort(1)
            utils.remove_leftover_images('AllCamera_')
            
        else:
            utils.log(2, 'Unable to start All Camera Player')
            utils.notify('Player did not start.  Check camera settings.')


    def getImagesSnapshot(self, i, url, control):
        """ Update camera position with snapshots """
        
        x = 0
        #starttime = time.time()
        
        while not monitor.abortRequested() and self.isRunning:
            
            try:
                filename = os.path.join(_datapath, 'AllCamera_%s.%d.jpg') %(i, x)
                urlretrieve(url, filename)
                
                if os.path.exists(filename): 
                    control[0].setImage(filename, useCache=False)                
                    xbmcvfs.delete(os.path.join(_datapath, 'AllCamera_%s.%d.jpg') %(i, x - 1))
                    control[1].setImage(filename, useCache=False)
                    x+=1
                    
            except Exception, e:
                utils.log(3, str(e))
                control[0].setImage(_error, useCache=False)

        #fps = (x + 1) / (time.time() - starttime)
        #print "All Cameras average FPS is " + str(fps)
      

    def getImagesMjpeg(self, i, url, control):
        """ Update camera position with mjpeg frames """
        
        try:
            stream = requests.get(url, stream=True).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            control[0].setImage(self.error, useCache=False)
            
        #starttime = time.time()
        x = 0
        
        while not monitor.abortRequested() and self.isRunning:
            
            filename = os.path.join(_datapath, 'AllCamera_%s.%d.jpg') %(i, x)
            filename_exists = utils.get_mjpeg_frame(stream, filename)

            if filename_exists:
                control[0].setImage(filename, useCache=False)
                control[1].setImage(filename, useCache=False)
                xbmcvfs.delete(os.path.join(_datapath, 'AllCamera_%s.%d.jpg') %(i, x - 1))
                x += 1
                
            else:
                utils.log(3, 'Camera %s - Error on MJPEG' %i)
                control[0].setImage(_error, useCache=False)

        #fps = (x + 1) / (time.time() - starttime)
        #print "Preview Camera average FPS is " + str(fps)


    def getImagesMjpegInterlace(self,i, url, control):
        """ Update camera position with interlaced mjpeg frames """
        
        try:
            stream = requests.get(url, stream=True).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            control[0].setImage(self.error, useCache=False)
            
        #starttime = time.time()
        x = 0
        
        while not monitor.abortRequested() and self.isRunning:
            
            filename = os.path.join(_datapath, 'AllCamera_%s.%d.jpg') %(i, x)
            filename_exists = utils.get_mjpeg_frame(stream, filename)

            if filename_exists:
                if x % 2 == 0:  #Interlacing for flicker reduction/elimination
                    control[0].setImage(filename, useCache=False)
                else:
                    control[1].setImage(filename, useCache=False)
                xbmcvfs.delete(os.path.join(_datapath, 'AllCamera_%s.%d.jpg') %(i, x - 2))
                x += 1
                
            else:
                utils.log(3, 'Camera %s - Error on MJPEG' %i)
                control[0].setImage(self.error, useCache=False)

        #fps = (x + 1) / (time.time() - starttime)
        #print "Preview Camera average FPS is " + str(fps)


    def onAction(self, action):        
        if action in (ACTION_PREVIOUS_MENU, ACTION_STOP, ACTION_NAV_BACK, ACTION_BACKSPACE):
            self.isRunning = False
            monitor.waitForAbort(.2)
            self.close()
            

def play():
    """ Main function to show all cameras """
    
    if settings.atLeastOneCamera():
        PlayerWindow = AllCameraDisplay()
        del PlayerWindow
        
    else:
        utils.log(2, 'No Cameras Configured')
        utils.notify('You must configure a camera first')

    monitor.reset_camera_playing('All')


if __name__ == "__main__":
    play()
