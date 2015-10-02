import xbmc, xbmcaddon, xbmcvfs, xbmcgui
import threading, os, Queue, time
import settings
from resources.lib import imaging, monitor, foscam
from urllib import urlretrieve


__addon__ = xbmcaddon.Addon('plugin.video.foscam4kodi')
__addonid__ = __addon__.getAddonInfo('id')
__path__ = xbmc.translatePath(('special://profile/addon_data/{0}').format(__addonid__)).decode('utf-8')

ACTION_PREVIOUS_MENU = 10
ACTION_STOP = 13
ACTION_NAV_BACK = 92
ACTION_BACKSPACE = 110
      
q = Queue.Queue(maxsize=0)
monitor = monitor.AddonMonitor()


class AllCameraDisplay(xbmcgui.WindowDialog):
    '''
    Text Here
    '''
    
    def __init__(self):    

        loader = xbmc.translatePath(('special://home/addons/{0}/resources/media/loader_old.gif').format(__addonid__)).decode('utf-8')
        self.error = xbmc.translatePath(('special://home/addons/{0}/resources/media/error.png').format(__addonid__)).decode('utf-8')
        holder = xbmc.translatePath(('special://home/addons/{0}/resources/media/placeholder.jpg').format(__addonid__)).decode('utf-8')
            
        atLeastOneCamera, cameras = settings.getSettings(settings_to_get = 'basic', cameras_to_get='1234')
        
        if atLeastOneCamera:
            urls = []
            files = []
            imgs = []
            imgs2 = []
            
            coords = [  (0, 0, 640, 360),   
                        (640, 0, 640, 360),
                        (0, 360, 640, 360),
                        (640, 360, 640, 360) ]

            effect = ['slide', 'slide']
            time = [1100, 1000]
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
            
                 
            self.isRunning = True
            
            for active_camera in '1234':
                i = int(active_camera) - 1

                
                img1 = xbmcgui.ControlImage(*coords[i], filename=loader, aspectRatio = 0)
                try: self.addControl(img1)
                except: pass
                img1.setAnimations(animations[i])
                
                img2 = xbmcgui.ControlImage(*coords[i], filename='', aspectRatio = 0)
                try: self.addControl(img2)
                except: pass
                img2.setAnimations(animations[i])

                img3 = xbmcgui.ControlImage(*coords[i], filename='', aspectRatio = 0)
                try: self.addControl(img3)
                except: pass
                img3.setAnimations(animations[i])

                if len(cameras) > i:
                    camera = cameras[i]
                    url = camera[6]
                    #c = [url, img1, img2]       #SnapShot
                    c = [camera, img1, img2, img3]       #MJPEG
                    #t = threading.Thread(target=self.getImages, args=(i+1, c, __path__))    #Snapshot
                    t = threading.Thread(target=self.getImagesMjpeg, args=(i+1, c, __path__))    #MJPEG
                    t.start()

                else:
                    img1.setImage(holder, useCache=False)  
                    

            monitor.set_camera_playing('All')
            self.show()    

            while not monitor.abortRequested() and self.isRunning:       
                monitor.waitForAbort(1)

            monitor.waitForAbort(1)
            
            for i in xbmcvfs.listdir(__path__)[1]:
                if 'AllCamera_' in i:
                    try: xbmcvfs.delete(os.path.join(__path__, i))
                    except: pass  

    def getImages(self, i, c, path):
        '''
        Text here
        '''
        
        x = 0
        starttime = time.time()
        
        while not monitor.abortRequested() and self.isRunning:
            
            try:
                filename = os.path.join(path, 'AllCamera_%d.%d.jpg') %(i, x)
                urlretrieve(c[0], filename)
                
                if os.path.exists(filename): 
                    c[1].setImage(filename, useCache=False)                
                    xbmcvfs.delete(os.path.join(path, 'AllCamera_%d.%d.jpg') %(i, x - 1))
                    c[2].setImage(filename, useCache=False)
                    x+=1
                    
            except Exception, e:
                xbmc.log(str(e))
                c[1].setImage(self.error, useCache=False)

        fps = (x + 1) / (time.time() - starttime)
        print "All Cameras average FPS is " + str(fps)



    def get_mjpeg_frame(self, stream):
        '''
        Text here
        '''
        
        content_length = ''
        try:
            while not 'Length' in content_length: 
                content_length = stream.readline()
            bytes = int(content_length.split(':')[-1])
            content_length = stream.readline()
            return stream.read(bytes)
        
        except requests.RequestException as e:
            print str(e)
            return None
    

    def getImagesMjpeg(self, i, c, path):
        '''
        Text here
        '''
        
        camera = foscam.Camera(c[0])
        stream = camera.get_mjpeg_stream()
            
        starttime = time.time()
        x = 0     
        while not monitor.abortRequested() and self.isRunning:
            
            frame = self.get_mjpeg_frame(stream)
            if frame:
                filename = os.path.join(path, 'AllCamera_%d.%d.jpg') %(i, x)
                with open(filename, 'wb') as jpeg_file:
                    jpeg_file.write(frame)
                    
            if os.path.exists(filename):
                c[1].setImage(filename, useCache=False)
                xbmcvfs.delete(os.path.join(path, 'AllCamera_%d.%d.jpg') %(i, x - 1))
                monitor.waitForAbort(.01)
                c[2].setImage(filename, useCache=False)
                
                #c[3].setImage(filename, useCache=False)
                x += 1
                
            else:
                print ('Camera %s - %s' %(i, 'Error on MJPEG'))
                c[1].setImage(self.error, useCache=False)

        fps = (x + 1) / (time.time() - starttime)
        print "Preview Camera average FPS is " + str(fps)

    

    def onAction(self, action):        
        if action in (ACTION_PREVIOUS_MENU, ACTION_STOP, ACTION_NAV_BACK, ACTION_BACKSPACE):
            self.isRunning = False
            monitor.waitForAbort(.2)
            self.close()
            monitor.clear_camera_playing('All')


def Main():
    if not xbmcvfs.exists(__path__):
        try:
            xbmcvfs.mkdir(__path__)
        except:
            pass
    PlayerWindow = AllCameraDisplay()


if __name__ == "__main__":
    Main()
