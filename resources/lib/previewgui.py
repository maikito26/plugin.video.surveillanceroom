"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to draw and show the preview window
"""

import xbmc, xbmcaddon, xbmcgui, xbmcvfs
import os, requests   #, time
import utils, settings, cameraplayer
from urllib import urlretrieve
import threading
import socket
TIMEOUT = settings.getSetting_int('request_timeout')
socket.setdefaulttimeout(TIMEOUT)

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

'''
def ImageWorker(monitor, q):
    """
    Thread worker that receives a window to update the image of continuously until that window is closed
    """
    
    while not monitor.abortRequested() and not monitor.stopped():
        if not q.empty():
            
            try:
                item = q.get(block = False)
                control = [item[0].img1, item[0].img2]
                camera = item[1]
                
                stream_type = camera.getStreamType(2)
                url = camera.getStreamUrl(2, stream_type)
                prefix = 'Preview'
                utils.log(2, 'Received request for image processing of Camera %s.  Stream Type: %d;  URL: %s' %(item[0], stream_type, url)) 

                return 
                if stream_type == 0:
                    getImagesMjpeg(camera, url, control, prefix, monitor)             
                elif stream_type == 1: 
                    getImagesSnapshot(camera, url, control, prefix, monitor)      
                elif stream_type == 2:
                    getImagesMjpegInterlaced(camera, url, control, prefix, monitor) 
                
                utils.remove_leftover_images('%s_%s.' %(prefix, camera.number))

            except:
                pass

        monitor.waitForAbort(0.5)

    
def getImagesSnapshot(camera, url, control, prefix, monitor):
    """ Update camera position with snapshots """
    
    x = 0
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera.number):
        
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

    utils.remove_leftover_images('%s_%s.' %(prefix, camera.number))
  

def getImagesMjpeg(camera, url, control, prefix, monitor):
    """ Update camera position with mjpeg frames """
 
    try:
        stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
        
    except requests.RequestException as e:
        utils.log(3, e)
        control[0].setImage(_error, useCache = False)
        return

    x = 0
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera.number):
        
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
            
    utils.remove_leftover_images('%s_%s.' %(prefix, camera.number))


def getImagesMjpegInterlace(camera, url, control, prefix, monitor):
    """ Update camera position with interlaced mjpeg frames """
    
    try:
        stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
        
    except requests.RequestException as e:
        utils.log(3, e)
        control[0].setImage(_error, useCache = False)
        return
        
    x = 0
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera.number):
        
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

    utils.remove_leftover_images('%s_%s.' %(prefix, camera.number))
    '''
    


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
    
    def __init__(self, camera, monitor):
        self.monitor = monitor
        self.camera = camera
        self.monitor.set_preview_window_closed(self.camera.number)
        self.prefix = 'Preview'
        self.buttons = []
        
        # Positioning of the window       
        WIDTH = 320
        HEIGHT = 180
        
        scaling = settings.getSetting_float('scaling', self.camera.number)
        
        width = int(float(WIDTH * scaling))
        height = int(float(HEIGHT * scaling))
        
        button_scaling = 0.5 * scaling
        button_width = int(round(Button.WIDTH * button_scaling))
        
        position = settings.getSetting('position', self.camera.number).lower()
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
         
    def start(self, url = None):
        self.monitor.set_preview_window_opened(self.camera.number)
        
        if url == None:
            stream_type = self.camera.getStreamType(2)
            url = self.camera.getStreamUrl(2, stream_type)
        else:
            stream_type = 0 # Needs to be determined somehow

        if stream_type == 0:
            t = threading.Thread(target = self.getImagesMjpeg, args = (url,))         
        elif stream_type == 1:
            t = threading.Thread(target = self.getImagesSnapshot, args = (url,)) 
        elif stream_type == 2:
            t = threading.Thread(target = self.getImagesMjpegInterlaced, args = (url,))

        t.daemon = True 
        t.start()

        self.show()
        
        
    def stop(self):
        self.monitor.set_preview_window_closed(self.camera.number)
        self.monitor.waitForAbort(.2)
        self.close()
        utils.remove_leftover_images('%s_%s.' %(self.prefix, self.camera.number))

    def onControl(self, control):
        if control == self.close_button:
            self.monitor.set_preview_window_dismissed(self.camera.number)
            self.stop()
            
    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE, ACTION_NAV_BACK):
            self.monitor.set_preview_window_dismissed(self.camera.number)
            self.stop()
            
        elif action == ACTION_SELECT_ITEM:
            self.run()
            
    def run(self):
        self.stop()
        cameraplayer.play(self.camera.number, self.monitor)


    def getImagesMjpeg(self, url):
        """ Update camera position with mjpeg frames """
     
        try:
            stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            self.img1.setImage(_error, useCache = False)
            return

        x = 0
        while not self.monitor.abortRequested() and not self.monitor.stopped() and self.monitor.preview_window_opened(self.camera.number):
            filename = os.path.join(_datapath, '%s_%s.%d.jpg') %(self.prefix, self.camera.number, x)
            filename_exists = utils.get_mjpeg_frame(stream, filename)

            if filename_exists:
                self.img1.setImage(filename, useCache = False)
                self.img2.setImage(filename, useCache = False)
                xbmcvfs.delete(os.path.join(_datapath, '%s_%s.%d.jpg') %(self.prefix, self.camera.number, x - 1))
                x += 1
                
            else:
                utils.log(3, 'Camera %s - Error on MJPEG' %self.camera.number)
                self.img1.setImage(_error, useCache = False)
                return


    def getImagesSnapshot(self, url, *args, **kwargs):
        """ Update camera position with snapshots """
        
        x = 0
        while not self.monitor.abortRequested() and not self.monitor.stopped() and self.monitor.preview_window_opened(self.camera.number):
            
            try:
                filename = os.path.join(_datapath, '%s_%s.%d.jpg') %(self.prefix, self.camera.number, x)
                urlretrieve(url, filename)
                
                if os.path.exists(filename): 
                    self.img1.setImage(filename, useCache = False)                
                    xbmcvfs.delete(os.path.join(_datapath, '%s_%s.%d.jpg') %(self.prefix, self.camera.number, x - 1))
                    self.img2.setImage(filename, useCache = False)
                    x += 1
                    
            except Exception, e:
                utils.log(3, 'Camera %s - Error on Snapshot: %s' %(self.camera.number, e))
                self.img1.setImage(_error, useCache = False)
                return


    def getImagesMjpegInterlace(self, url, *args, **kwargs):
        """ Update camera position with interlaced mjpeg frames """
        
        try:
            stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            self.img1.setImage(_error, useCache = False)
            return
            
        x = 0
        while not self.monitor.abortRequested() and not self.monitor.stopped() and self.monitor.preview_window_opened(self.camera.number):
            
            filename = os.path.join(_datapath, '%s_%s.%d.jpg') %(self.prefix, self.camera.number, x)
            filename_exists = utils.get_mjpeg_frame(stream, filename)

            if filename_exists:
                if x % 2 == 0:  #Interlacing for flicker reduction/elimination
                    self.img1.setImage(filename, useCache = False)
                else:
                    self.img2.setImage(filename, useCache = False)
                xbmcvfs.delete(os.path.join(_datapath, '%s_%s.%d.jpg') %(self.prefix, self.camera.number, x - 2))
                x += 1
                
            else:
                utils.log(3, 'Camera %s - Error on MJPEG' %self.camera.number)
                self.img1.setImage(_error, useCache = False)
                return

        
if __name__ == "__main__":
    pass

