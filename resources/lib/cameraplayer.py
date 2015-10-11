'''
Text Here!
'''

import xbmc, xbmcgui, xbmcaddon
from settings import getSettings, get_playbackRewindTime, notify
from functools import partial

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')

''' Common GUI images '''
__btnimage__ = xbmc.translatePath('special://home/addons/%s/resources/media/{0}.png' %__addonid__ ).decode('utf-8')

''' Keyboard input values '''
ACTION_PREVIOUS_MENU = 10
ACTION_BACKSPACE = 110
ACTION_NAV_BACK = 92
ACTION_STOP = 13
ACTION_SELECT_ITEM = 7


class Button(xbmcgui.ControlButton):
    '''
    Class reclasses the ControlButton class for use in this addon.
    '''
    
    WIDTH = HEIGHT = 32

    def __new__(cls, parent, action, x, y, scaling = 1.0):
        focusTexture    = __btnimage__.format(action)
        noFocusTexture  = __btnimage__.format(action+ '_nofocus')
        width           = int(round(cls.WIDTH * scaling))
        height          = int(round(cls.HEIGHT * scaling))
        
        self = super(Button, cls).__new__(cls, x, y, width, height, '',
                                          focusTexture, noFocusTexture)
        parent.buttons.append(self)
        return self


class ToggleButton(xbmcgui.ControlRadioButton):
    '''
    Class reclasses the RadioButton class for use in this addon.
    '''
    
    WIDTH = 110
    HEIGHT = 40

    def __new__(cls, parent, action, x, y):
        focusOnTexture      = __btnimage__.format('radio-on')
        noFocusOnTexture    = __btnimage__.format('radio-on')
        focusOffTexture     = __btnimage__.format('radio-off')
        noFocusOffTexture   = __btnimage__.format('radio-off')
        focusTexture        = __btnimage__.format('back')
        noFocusTexture      = __btnimage__.format('trans')
        textOffsetX         = 12

        self = super(ToggleButton, cls).__new__(cls, x, y, cls.WIDTH, cls.HEIGHT, action.title(),
                                                focusOnTexture, noFocusOnTexture,
                                                focusOffTexture, noFocusOffTexture,
                                                focusTexture, noFocusTexture,
                                                textOffsetX)

        self.action = action
        parent.buttons.append(self)
        return self

    def send_cmd(self, control):
        return self.cmd.set_enabled(control.isSelected())



class CameraControlsWindow(xbmcgui.WindowDialog):
    '''
    Class is used to create a single camera playback window of the camera view with controls
        [
        0:  [0]camera_number
        1:  [1]host  [2]port  [3]username  [4]password  [5]name  [6]snapshot  [7]rtsp  
            [8]mpjeg  [9]cameratype  [10]cameraplayer_source  [11]allcameraplayer_source     
        2:  [12]pan_tilt  [13]zoom  [14]motionsupport  [15]soundsupport
        ]
    '''
    
    def __init__(self, camera_settings, monitor):
        self.monitor = monitor
        self.camera_settings = camera_settings
        self.camera_number = camera_settings[0]

        import foscam2
        self.camera = foscam2.FoscamCamera(camera_settings)
    
    def __enter__(self):
        return self
    
    def start(self):
        self.playVideo()
        #self.setupUi()
        self.doModal()


    def playVideo(self):
        source = self.camera_settings[10]
        self.player = StopResumePlayer(**{'camera_number': self.camera_number, 'monitor': self.monitor, 'callback1': self.setupUi, 'callback2': self.stop})
        self.player.maybe_stop_current()

        if source == 0:   #Mjpeg 
            url = self.camera_settings[8]
        else:                   #Main or Substream
            url = self.camera_settings[7]

        listitem = xbmcgui.ListItem()
        listitem.setProperty('StartOffset', '20')   #Hack to improve perceived responsiveness of Stream and Button Presses
        self.player.play(url, listitem)
        
    def setupUi(self):
        Y_OFFSET    = 100
        X_OFFSET    = 20
        OFFSET1     = 32
        OFFSET2     = 64

        self.pan_tilt    = self.camera_settings[12]
        self.zoom        = self.camera_settings[13]
        
        self.buttons = []

        self.flip_button        = ToggleButton(self, 'flip', 30, Y_OFFSET+200)        
        self.mirror_button      = ToggleButton(self, 'mirror', 30, Y_OFFSET+260)  
        self.close_button       = Button(self, 'close', 1280-60, 20)       
        self.settings_button    = Button(self, 'settings', 1280-120, 20)
        self.addControl(self.flip_button)
        self.addControl(self.mirror_button)
        self.addControl(self.settings_button)
        self.addControl(self.close_button)
        self.flip_button.setNavigation      (self.settings_button,      self.mirror_button,     self.close_button,      self.settings_button)
        self.mirror_button.setNavigation    (self.flip_button,      self.close_button,         self.close_button,      self.settings_button)
        self.settings_button.setNavigation  (self.mirror_button,    self.flip_button,     self.flip_button,      self.close_button)

        response_ok, response = self.camera.get_mirror_and_flip_setting()
        if response_ok == 0:
            self.mirror_button.setSelected(int(response.get('isMirror')))
            self.flip_button.setSelected(int(response.get('isFlip')))
        
        self.close_button.setNavigation     (self.mirror_button,    self.flip_button,     self.settings_button,   self.flip_button)

        if self.pan_tilt:
            
            self.up_button          = Button(self, 'up', OFFSET1+X_OFFSET, Y_OFFSET)
            self.left_button        = Button(self, 'left', X_OFFSET, OFFSET1+Y_OFFSET)        
            self.down_button        = Button(self, 'down', OFFSET1+X_OFFSET, OFFSET2+Y_OFFSET)    
            self.right_button       = Button(self, 'right', OFFSET2+X_OFFSET, OFFSET1+Y_OFFSET)
            self.top_left_button     = Button(self, 'top_left', X_OFFSET, Y_OFFSET)
            self.top_right_button    = Button(self, 'top_right', OFFSET2+X_OFFSET, Y_OFFSET)
            self.bottom_right_button  = Button(self, 'bottom_right', OFFSET2+X_OFFSET, OFFSET2+Y_OFFSET)
            self.bottom_left_button   = Button(self, 'bottom_left', X_OFFSET, OFFSET2+Y_OFFSET)
            self.home_button        = Button(self, 'home', OFFSET1+X_OFFSET, OFFSET1+Y_OFFSET)
            self.preset_button      = ToggleButton(self, 'preset', 30, Y_OFFSET+320)
            
            self.addControl(self.up_button)
            self.addControl(self.left_button)
            self.addControl(self.down_button)
            self.addControl(self.right_button)
            self.addControl(self.top_left_button)
            self.addControl(self.top_right_button)
            self.addControl(self.bottom_right_button)
            self.addControl(self.bottom_left_button)
            self.addControl(self.home_button)
            self.addControl(self.preset_button)
            
            self.flip_button.setNavigation      (self.down_button,      self.mirror_button,     self.close_button,      self.close_button)
            self.mirror_button.setNavigation    (self.flip_button,      self.up_button,         self.close_button,      self.close_button)
            self.settings_button.setNavigation  (self.mirror_button,    self.mirror_button,     self.right_button,      self.close_button)
            self.close_button.setNavigation     (self.mirror_button,    self.mirror_button,     self.settings_button,   self.right_button)
            self.up_button.setNavigation        (self.mirror_button,    self.home_button,       self.top_left_button,    self.top_right_button)
            self.left_button.setNavigation      (self.top_left_button,   self.bottom_left_button,  self.close_button,      self.home_button)
            self.right_button.setNavigation     (self.top_right_button,  self.bottom_right_button, self.home_button,       self.settings_button)
            self.down_button.setNavigation      (self.home_button,      self.flip_button,       self.bottom_left_button,  self.bottom_right_button)
            self.top_left_button.setNavigation   (self.mirror_button,    self.left_button,       self.close_button,      self.up_button)
            self.top_right_button.setNavigation  (self.mirror_button,    self.right_button,      self.up_button,         self.settings_button)
            self.bottom_right_button.setNavigation(self.right_button,     self.flip_button,       self.down_button,       self.settings_button)
            self.bottom_left_button.setNavigation (self.left_button,      self.flip_button,       self.close_button,      self.down_button)
            self.home_button.setNavigation      (self.up_button,        self.down_button,       self.left_button,       self.right_button)


            home_location = self.camera.ptz_home_location(3)
            self.preset_button.setSelected(home_location)

        if self.zoom:
            self.zoom_in_button = Button(self, 'zoom_in', OFFSET2+X_OFFSET+32, Y_OFFSET)
            self.zoom_out_button = Button(self, 'zoom_out', OFFSET2+X_OFFSET+32, OFFSET2+Y_OFFSET)
            self.addControl(self.zoom_in_button)
            self.addControl(self.zoom_out_button)
        
        self.setFocus(self.close_button)


    def getControl(self, control):
        return next(button for button in self.buttons if button == control)
    
    def onControl(self, control):
        if control == self.close_button:        self.stop()
        elif control == self.flip_button:       self.camera.flip_video()
        elif control == self.mirror_button:     self.camera.mirror_video()
        elif control == self.settings_button:   __addon__.openSettings()
        
        elif self.pan_tilt:
            if control == self.home_button:     home_location = self.camera.ptz_home_location(1)
            elif control == self.preset_button: self.toggle_preset()
            else:
                if control == self.up_button:     self.camera.ptz_move_up()
                elif control == self.down_button:   self.camera.ptz_move_down()
                elif control == self.left_button:   self.camera.ptz_move_left()
                elif control == self.right_button:  self.camera.ptz_move_right()
                elif control == self.top_left_button:       self.camera.ptz_move_top_left()
                elif control == self.top_right_button:      self.camera.ptz_move_top_right()
                elif control == self.bottom_left_button:    self.camera.ptz_move_bottom_left()
                elif control == self.bottom_right_button:   self.camera.ptz_move_bottom_right()

                self.monitor.waitForAbort(.25)  #Move Button Sensitivity
                self.camera.ptz_stop_run()
                
        elif self.zoom:
            if control == self.zoom_in_button:     self.camera.ptz_zoom_in()
            elif control == self.zoom_out_button:   self.camera.ptz_zoom_out()

            self.monitor.waitForAbort(.25)  #Move Button Sensitivity
            self.camera.ptz_zoom_stop()
        
    def toggle_preset(self):
        if self.preset_button.isSelected():
            self.camera.ptz_add_preset()
            notify('Home Location is now Current Location')
        else:
            self.camera.ptz_delete_preset()
            notify('Home Location is now Default Location')

    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_BACKSPACE,
                      ACTION_NAV_BACK, ACTION_STOP):
            self.stop()

    def stop(self):
        self.close()
        self.player.stop()
        self.player.maybe_resume_previous()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()




class StopResumePlayer(xbmc.Player):
    '''
    put text here
    '''

    def __init__(self, *args, **kwargs):
        super(StopResumePlayer, self).__init__()
        self.camera_number = kwargs ['camera_number']
        self.monitor = kwargs['monitor']
        
        try:
            self.callback1 = kwargs['callback1']
        except:
            self.callback1 = None
            
        try:
            self.callback2 = kwargs['callback2']
        except:
            self.callback2 = None


    def onPlayBackStarted(self):
        self.monitor.set_camera_playing(self.camera_number)
        self.callback1()        #SetupUi() - for camera controls
        #self.seekTime(4)        #Potential hack for improving stream's perceived response to ptz movement

    def onPlayBackEnded(self):
        self.monitor.clear_camera_playing(self.camera_number)
        self.callback2()        #stop() - for the preview window

    def onPlayBackStopped(self):
        self.monitor.clear_camera_playing(self.camera_number)
        self.callback2()        #stop() - for the preview window

    def stop(self):
        self.monitor.clear_camera_playing(self.camera_number)
        xbmc.executebuiltin('PlayerControl(Stop)')          # Because player.stop() was losing the player and didn't work *sad face*
        
    def maybe_stop_current(self):
        if self.isPlaying():
            self.resume_time = self.getTime()
            self.previous_file = self.getPlayingFile()
            self.stop()
            print "Stopped {0}".format(self.previous_file)
            
        else:
            self.previous_file = None

    def maybe_resume_previous(self):
        if self.previous_file is not None:
            resume_time_str = "{0:.1f}".format(self.resume_time - get_playbackRewindTime())
            print "Resuming {0} at {1}".format(self.previous_file, resume_time_str)
            listitem = xbmcgui.ListItem()
            listitem.setProperty('StartOffset', resume_time_str)
            self.play(self.previous_file, listitem)



def playCameraVideo(camera_number, monitor):
    '''
    Text Here
    '''

    settings_ok, cameras = getSettings(settings_to_get = 'features', cameras_to_get = camera_number)
    camera_settings = cameras[0]

    if settings_ok:
        with CameraControlsWindow(camera_settings, monitor) as camera_player:
            camera_player.start()
    else:
        print 'Settings not okay'


if __name__ == "__main__":
    pass



  



        



            
            
