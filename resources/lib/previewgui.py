"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to draw and show the preview window
"""

import xbmc, xbmcaddon, xbmcgui, xbmcvfs
import os, requests   #, time
import utils, settings, cameraplayer

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

_black = xbmc.translatePath('special://home/addons/%s/resources/media/black.png' %__addonid__ ).decode('utf-8')
_btnimage = xbmc.translatePath('special://home/addons/%s/resources/media/{0}.png' %__addonid__ ).decode('utf-8')
_error = xbmc.translatePath('special://home/addons/%s/resources/media/error.png' %__addonid__ ).decode('utf-8')
_datapath = xbmc.translatePath('special://profile/addon_data/%s' %__addonid__ ).decode('utf-8')

ACTION_PREVIOUS_MENU = 10
ACTION_BACKSPACE = 110
ACTION_NAV_BACK = 92
ACTION_STOP = 13
ACTION_SELECT_ITEM = 7


def ImageWorker(monitor, q):
    """
    Thread worker that receives a window to update the image of continuously until that window is closed

    item:
        [0] camera_number;  [1]window.control
    """
    
    while not monitor.abortRequested() and not monitor.stopped():
        
        if not q.empty():
            
            try:
                item = q.get(block = False)
        
                stream_type = settings.getStreamType(2, item[0])
                url = settings.getStreamUrl(2, item[0], stream_type)

                utils.log(2, 'Received request for image processing of Camera %s.  Stream Type: %d;  URL: %s' %(item[0], stream_type, url)) 
                
                if stream_type == 0:
                    frameByMjpeg(item, monitor, url)           #Approx 10-30fps
                elif stream_type == 1: 
                    frameBySnapshot(item, monitor, url)        #Approx 2-4fps
                elif stream_type == 2:
                    frameByMjpegInterlaced(item, monitor, url) #Approx 5-15fps
                
                utils.remove_leftover_images('preview_%s.' %item[0])

            except:
                pass

        monitor.waitForAbort(0.5)
        
def frameBySnapshot(item, monitor, url):
    """ Updates window using snapshots """
    
    camera_number = item[0]
    control = item[1]
    from urllib import urlretrieve
    
    #starttime = time.time()
    x = 0
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera_number):
    
        filename = os.path.join(_datapath, 'preview_%s.%d.jpg') %(camera_number, x)

        try:
            urlretrieve(url, filename)
            
            if os.path.exists(filename):
                control.img1.setImage(filename, useCache=False)
                xbmcvfs.delete(os.path.join(_datapath, 'preview_%s.%d.jpg') %(camera_number, x - 1))
                control.img2.setImage(filename, useCache=False)
                x += 1

        except Exception, e:
            utils.log(3, 'Camera %s - %s' %(camera_number, str(e)))
            control.img1.setImage(_error, useCache=False)

    utils.remove_leftover_images('preview_%s.' %camera_number)
    #fps = (x + 1) / (time.time() - starttime)
    #print "Preview Camera average FPS is " + str(fps) 

def frameByMjpeg(item, monitor, url):
    """ Updates window using mjpeg frames """
    
    camera_number = item[0]
    control = item[1]

    try:
        stream = requests.get(url, stream=True).raw
        
    except requests.RequestException as e:
        utils.log(3, e)
        control.img2.setImage(_error, useCache=False)
        
    #starttime = time.time()
    x = 0
    
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera_number):

        filename = os.path.join(_datapath, 'preview_%s.%d.jpg') %(camera_number, x)
        filename_exists = utils.get_mjpeg_frame(stream, filename)
        
        if filename_exists:
            control.img1.setImage(filename, useCache=False)
            xbmcvfs.delete(os.path.join(_datapath, 'preview_%s.%d.jpg') %(camera_number, x - 1))
            control.img2.setImage(filename, useCache=False)
            x += 1
            
        else:
            utils.log(3, 'Camera %s - Error on Mjpeg' %camera_number)
            control.img1.setImage(_error, useCache=False)

    utils.remove_leftover_images('preview_%s.' %camera_number)
    #fps = (x + 1) / (time.time() - starttime)
    #print "Preview Camera average FPS is " + str(fps)

def frameByMjpegInterlaced(item, monitor, url):
    """ Updates window using interlaced mjpeg frames """
    
    camera_number = item[0]
    control = item[1]
    
    try:
        stream = requests.get(url, stream=True).raw
        
    except requests.RequestException as e:
        utils.log(3, e)
        control.img2.setImage(_error, useCache=False)
        
    #starttime = time.time()
    x = 0
    
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera_number):

        filename = os.path.join(_datapath, 'preview_%s.%d.jpg') %(camera_number, x)
        filename_exists = utils.get_mjpeg_frame(stream, filename)

                
        if filename_exists:
            if x % 2 == 0:  #Interlacing for flicker reduction/elimination
                control.img1.setImage(filename, useCache=False)
            else:
                control.img2.setImage(filename, useCache=False)
            xbmcvfs.delete(os.path.join(_datapath, 'preview_%s.%d.jpg') %(i, x - 2))
            x += 1
            
        else:
            utils.log(3, 'Camera %s - Error on Mjpeg' %camera_number)
            control.img2.setImage(_error, useCache=False)
                              
    utils.remove_leftover_images('preview_%s.' %camera_number)
    #fps = (x + 1) / (time.time() - starttime)
    #print "Preview Camera average FPS is " + str(fps)

class Button(xbmcgui.ControlButton):
    """ Class reclasses the ControlButton class for use in this addon. """
    
    WIDTH = HEIGHT = 32

    def __new__(cls, parent, action, x, y, camera = None, scaling = 1.0):
        focusTexture    = _btnimage.format(action)
        noFocusTexture  = _btnimage.format(action+ '_nofocus')
        width           = int(round(cls.WIDTH * scaling))
        height          = int(round(cls.HEIGHT * scaling))
        
        self = super(Button, cls).__new__(cls, x, y, width, height, '',
                                          focusTexture, noFocusTexture)
        parent.buttons.append(self)
        return self

class CameraPreviewWindow(xbmcgui.WindowDialog):
    """ Class is used to create the picture-in-picture window of the camera view """
    
    def __init__(self, camera_settings, monitor):
        self.monitor = monitor
        self.camera_settings = camera_settings
        self.camera_number = self.camera_settings[0]
        self.monitor.set_preview_window_closed(self.camera_number)

        self.buttons = []
        
        # Positioning of the window       
        WIDTH = 320
        HEIGHT = 180
        
        scaling = settings.getSetting_float('scaling', self.camera_number)
        
        width = int(float(WIDTH * scaling))
        height = int(float(HEIGHT * scaling))
        
        button_scaling = 0.5 * scaling
        button_width = int(round(Button.WIDTH * button_scaling))
        
        position = settings.getSetting('position', self.camera_number).lower()
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

        animations = [('WindowOpen', ("effect=slide start={0:d} time=1300 tween=cubic easing=out").format(start)),
                      ('WindowClose', ("effect=slide end={0:d} time=900 tween=back easing=inout").format(start))]

        self.black = xbmcgui.ControlImage(x, y, width, height, _black)
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
           
        self.setProperty('zorder', "99")
         
    def start(self):
        self.monitor.set_preview_window_opened(self.camera_number)
        self.show()

    def stop(self):
        self.monitor.set_preview_window_closed(self.camera_number)
        self.monitor.waitForAbort(.2)
        self.close()

    def onControl(self, control):
        if control == self.close_button:
            self.monitor.set_preview_window_dismissed(self.camera_number)
            utils.log(4, 'Camera %s:  Action: Stop Button Pressed' %self.camera_number)
            self.stop()
            
    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE, ACTION_NAV_BACK):
            self.monitor.set_preview_window_dismissed(self.camera_number)
            utils.log(4, 'Camera %s:  KeyPress: ' %action)
            self.stop()
            
        elif action == ACTION_SELECT_ITEM:
            self.run()
            
    def run(self):
        self.stop()
        cameraplayer.play(self.camera_number, self.monitor)

        
if __name__ == "__main__":
    pass

