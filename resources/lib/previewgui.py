'''
Text Here!
'''

import xbmc, xbmcaddon, xbmcgui, xbmcvfs
import os   #, time
from cameraplayer import playCameraVideo

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

''' Common GUI images '''
__holder__ = xbmc.translatePath('special://home/addons/%s/resources/media/holder.png' %__addonid__ ).decode('utf-8')
__black__ = xbmc.translatePath('special://home/addons/%s/resources/media/black.png' %__addonid__ ).decode('utf-8')
__btnimage__ = xbmc.translatePath('special://home/addons/%s/resources/media/{0}.png' %__addonid__ ).decode('utf-8')

''' Keyboard input values '''
ACTION_PREVIOUS_MENU = 10
ACTION_BACKSPACE = 110
ACTION_NAV_BACK = 92
ACTION_STOP = 13
ACTION_SELECT_ITEM = 7




def cleanup_images(f, path):  
    monitor.waitForAbort(1)
    for i in xbmcvfs.listdir(path)[1]:
        print 'CLEANUP File to delete ' + str(i) 
        if f in i:
            try:
                xbmcvfs.delete(os.path.join(path, i))
                print 'Success to delete'
            except: pass  


def ImageWorker(monitor, q, path, snapShot_type):
    '''
    Thread worker that receives a window to update the image of continuously until that window is closed
    '''

    #error = os.path.join(path, 'error.png')
    
    while not monitor.abortRequested() and not monitor.stopped():
        
        try:
            item = q.get(block = False)
            
            if not snapShot_type:
                frameByMjpeg(item, monitor, path)       #Approx 10-30fps
            else: 
                frameBySnapshot(item, monitor, path)    #Approx 2-4fps
            
            camera_number = item[0][0]
            cleanup_images('preview_%s.' %camera_number, path)

        except:
            pass

        monitor.waitForAbort(0.5)
        

def frameBySnapshot(item, monitor, path):
    '''
    Text Here
    '''
    
    camera_settings = item[0]
    camera_number = camera_settings[0]
    snapshotURL = camera_settings[6]
    control = item[1]
    from urllib import urlretrieve
    
    #starttime = time.time()
    x = 0
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera_number):
    
        filename = os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x)

        try:
            urlretrieve(snapshotURL, filename)
            
            if os.path.exists(filename):
                control.img1.setImage(filename, useCache=False)
                xbmcvfs.delete(os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x - 1))
                control.img2.setImage(filename, useCache=False)
                x += 1

        except Exception, e:
            print ('Camera %s - %s' %(camera_number, str(e)))
            #control.img1.setImage(__error__, useCache=False)

    cleanup_images('preview_%s.' %camera_number, path)
    #fps = (x + 1) / (time.time() - starttime)
    #print "Preview Camera average FPS is " + str(fps) 



def get_mjpeg_frame(stream):
    '''
    Text Here
    '''
    
    content_length = ""
    try:
        while not "Length" in content_length: 
            content_length = stream.readline()
        bytes = int(content_length.split(':')[-1])
        content_length = stream.readline()
        return stream.read(bytes)
    
    except requests.RequestException as e:
        print str(e)
        return None
    

def frameByMjpeg(item, monitor, path):
    '''
    Text Here
    '''
        
    camera_settings = item[0]
    camera_number = camera_settings[0]
    control = item[1]

    import foscam
    camera = foscam.Camera(camera_settings)
    stream = camera.get_mjpeg_stream()
        
    #starttime = time.time()
    x = 0
    
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera_number):
        
        frame = get_mjpeg_frame(stream)

        if frame:
            filename = os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x)
            with open(filename, 'wb') as jpeg_file:
                jpeg_file.write(frame)
                
        if os.path.exists(filename):
            control.img1.setImage(filename, useCache=False)
            xbmcvfs.delete(os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x - 1))
            control.img2.setImage(filename, useCache=False)
            x += 1
            
        else:
            print ('Camera %s - %s' %(camera_number, 'Error on MJPEG'))
            #control.img1.setImage(__error__, useCache=False)

    cleanup_images('preview_%s.' %camera_number, path)
    #fps = (x + 1) / (time.time() - starttime)
    #print "Preview Camera average FPS is " + str(fps)




class Button(xbmcgui.ControlButton):
    '''
    Class reclasses the ControlButton class for use in this addon.
    '''
    
    WIDTH = HEIGHT = 32

    def __new__(cls, parent, action, x, y, camera = None, scaling = 1.0):
        focusTexture    = __btnimage__.format(action)
        noFocusTexture  = __btnimage__.format(action+ '_nofocus')
        width           = int(round(cls.WIDTH * scaling))
        height          = int(round(cls.HEIGHT * scaling))
        
        self = super(Button, cls).__new__(cls, x, y, width, height, '',
                                          focusTexture, noFocusTexture)
        parent.buttons.append(self)
        return self

   
class CameraPreviewWindow(xbmcgui.WindowDialog):
    '''
    Class is used to create the picture-in-picture window of the camera view
    '''
    
    def __init__(self, camera_settings, monitor):
        self.camera_settings = camera_settings
        self.monitor = monitor
        self.camera_number = camera_settings[0]
        
        self.monitor.preview_window_reset(self.camera_number)

       # Can be used to capture self's window id
        #self.show()
        #monitor.waitForAbort(.07)   
        #self.monitor.set_preview_window_id(self.camera_number)
        #monitor.waitForAbort(.07) 
        #self.close()

        self.snapshotURL = camera_settings[6]
        scaling = camera_settings[19]
        position = camera_settings[18]
        self.setProperty('zorder', "99")
        self._stopped = True
        self.buttons = []
        
        '''
        Positioning of the window
        '''
        
        WIDTH = 320
        HEIGHT = 180
        width = int(float(WIDTH * scaling))
        height = int(float(HEIGHT * scaling))
        
        
        if 'bottom' in position:
            y = 720 - height
        else:
            y = 0

        if 'left' in position:
            x = 0
            start = - width
        else:
            x = 1280 - width
            start = width

        button_scaling = 0.5 * scaling
        button_width = int(round(Button.WIDTH * button_scaling))

        animations = [('WindowOpen', ("effect=slide start={0:d} time=1300 tween=cubic easing=out").format(start)),
                      ('WindowClose', ("effect=slide end={0:d} time=900 tween=back easing=inout").format(start))]

        self.black = xbmcgui.ControlImage(x, y, width, height, __black__)
        self.addControl(self.black)
        self.black.setAnimations(animations)
        
        self.img1 = xbmcgui.ControlImage(x, y, width, height, '')
        self.img2 = xbmcgui.ControlImage(x, y, width, height, '')
        self.addControl(self.img1)
        self.addControl(self.img2)
        self.img1.setAnimations(animations)
        self.img2.setAnimations(animations)

        self.close_button = Button(self, 'close', x + width - button_width - 10, y + 10, scaling=button_scaling)
        self.addControl(self.close_button)
        self.close_button.setAnimations(animations)                    
           

    def start(self):
        self.monitor.preview_window_open(self.camera_number)
        #self.monitor.waitForAbort(.2)
        self.show()

    def stop(self):
        self.monitor.preview_window_reset(self.camera_number)
        self.monitor.waitForAbort(.2)
        self.close()

    def onControl(self, control):
        if control == self.close_button:
            self.monitor.set_dismissed_preview(self.camera_number)
            self.stop()
            
    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE, ACTION_NAV_BACK):
            self.monitor.set_dismissed_preview(self.camera_number)
            self.stop()
        elif action == ACTION_SELECT_ITEM:
            self.run()
            
    def run(self):
        self.stop()
        playCameraVideo(self.camera_number, self.monitor)
        #xbmc.executebuiltin("RunAddon({0})".format(utils.addon_info('id')))
        











if __name__ == "__main__":
    pass

