"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to draw and show the preview window
"""

import xbmc, xbmcaddon, xbmcgui, xbmcvfs
import os, requests, time
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

#Close Conditions
CONDITION_DURATION_NO_ALARM = 0
CONDITION_DURATION = 1
CONDITION_MANUAL = 2
CONDITION_NO_ALARM = 3


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
        self.cond_service = settings.getSetting_int('cond_service', self.camera.number)
        self.cond_manual = settings.getSetting_int('cond_manual', self.camera.number)
        self.dur_service = settings.getSetting_int('dur_service', self.camera.number)
        self.dur_manual = settings.getSetting_int('dur_manual', self.camera.number)
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
        
        self.stop() #Initializes state and makes ready to be used

    def start(self):
        url = self.monitor.get_overrideURL(self.camera.number)  #Request to test by @mrjd in forum
        stream_type = self.camera.getStreamType(2)
        
        if url == '':
            url = self.camera.getStreamUrl(2, stream_type)

        if stream_type == 0:
            t = threading.Thread(target = self.getImagesMjpeg, args = (url,))         
        elif stream_type == 1:
            t = threading.Thread(target = self.getImagesSnapshot, args = (url,)) 
        elif stream_type == 2:
            t = threading.Thread(target = self.getImagesMjpegInterlace, args = (url,))
            
        t.daemon = True
        
        self.monitor.openPreview(self.camera.number)
        t.start()
        self.show()
        self.wait_closeRequest()
        

    def stop(self, wait = True):
        self.monitor.closePreview(self.camera.number)
        self.close()
        if wait:
            self.wait()

    def wait_openRequest(self):
        while not self.monitor.abortRequested() and not self.monitor.stopped():
            if self.monitor.openRequested(self.camera.number):
                self.openRequest_manual = self.monitor.openRequested_manual(self.camera.number)
                break
            self.monitor.waitForAbort(.5)

        if not self.monitor.abortRequested() and not self.monitor.stopped():
            self.start()

    def wait(self):
        if not self.monitor.abortRequested() and not self.monitor.stopped():
            self.wait_openRequest()


    def wait_closeRequest(self):
        # Duration is 0 if Close Condition is Manual or Alarm only, otherwise set based on source
        duration = 0
        if not self.monitor.openRequested_manual(self.camera.number):
            if self.cond_service == CONDITION_DURATION_NO_ALARM or self.cond_service == CONDITION_DURATION:
                duration = time.time() + self.dur_service

        else:            
            if self.cond_manual == CONDITION_DURATION_NO_ALARM or self.cond_manual == CONDITION_DURATION:
                duration = time.time() + self.dur_manual

        # Loop Condition Checking
        while not self.monitor.abortRequested() and not self.monitor.stopped():

            # Requested by Service
            if not self.monitor.openRequested_manual(self.camera.number):
                if self.cond_service == CONDITION_DURATION_NO_ALARM and self.monitor.alarmActive(self.camera.number):
                    duration = time.time() + self.dur_service

            # Requested Manually
            elif self.cond_manual == CONDITION_DURATION_NO_ALARM and self.monitor.alarmActive(self.camera.number):
                duration = time.time() + self.dur_manual

            # Duration Check if Close Condition is not Manual or Alarm only
            if duration > 0 and time.time() > duration: 
                self.monitor.closeRequest(self.camera.number)

            # Check if close Request
            if self.monitor.closeRequested(self.camera.number):
                break
            
            self.monitor.waitForAbort(.5)
        
        self.stop()
        

    
    def playFullscreen(self):
        self.stop(wait = False)
        cameraplayer.play(self.camera.number, self.monitor)
        self.wait()

    def onControl(self, control):
        if control == self.close_button:
            self.monitor.dismissPreview(self.camera.number)
            self.stop()
            
    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE, ACTION_NAV_BACK):
            self.monitor.dismissPreview(self.camera.number)
            self.stop()
            
        elif action == ACTION_SELECT_ITEM:
            self.playFullscreen()
            





    def getImagesMjpeg(self, url):
        """ Update camera position with mjpeg frames """
     
        try:
            stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            self.img1.setImage(_error, useCache = False)
            return

        x = 0
        while not self.monitor.abortRequested() and not self.monitor.stopped() and self.monitor.previewOpened(self.camera.number):
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
                break

        utils.remove_leftover_images('%s_%s.' %(self.prefix, self.camera.number))




    def getImagesSnapshot(self, url, *args, **kwargs):
        """ Update camera position with snapshots """
        
        x = 0
        while not self.monitor.abortRequested() and not self.monitor.stopped() and self.monitor.previewOpened(self.camera.number):
            
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
                break

        utils.remove_leftover_images('%s_%s.' %(self.prefix, self.camera.number))




    def getImagesMjpegInterlace(self, url, *args, **kwargs):
        """ Update camera position with interlaced mjpeg frames """
        
        try:
            stream = requests.get(url, stream = True, timeout = TIMEOUT).raw
            
        except requests.RequestException as e:
            utils.log(3, e)
            self.img1.setImage(_error, useCache = False)
            return
            
        x = 0
        while not self.monitor.abortRequested() and not self.monitor.stopped() and self.monitor.previewOpened(self.camera.number):
            
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
                break

        utils.remove_leftover_images('%s_%s.' %(self.prefix, self.camera.number))

        
if __name__ == "__main__":
    pass

