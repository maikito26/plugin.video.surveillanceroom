'''
Text Here!
'''

import xbmc, xbmcgui, xbmcaddon
import foscam
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

    def __new__(cls, parent, action, x, y, camera = None, scaling = 1.0):
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

    def __new__(cls, parent, action, x, y, camera):
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


class MoveButton(Button):
    def __init__(self, parent, direction, x, y, camera):
        self.cmd = partial(camera.move, direction)

    def send_cmd(self, control=None):
        return self.cmd()


class MirrorFlipButton(ToggleButton):
    def __init__(self, parent, action, x, y, camera):
        self.cmd = partial(camera.toggle_mirror_flip, action)

    def send_cmd(self, control=None):
        return self.cmd(control.isSelected())





class CameraControlsWindow(xbmcgui.WindowDialog):
    '''
    Class is used to create a single camera playback window of the camera view with controls
    '''
    
    def __init__(self, camera_settings, monitor):
        self.monitor = monitor
        self.camera_settings = camera_settings
        self.camera_number = camera_settings[0]
        self.camera = foscam.Camera(camera_settings)
    
    def __enter__(self):
        return self
    
    def start(self):
        self.playVideo()
        self.setupUi()

        mirror, flip = self.camera.get_mirror_and_flip()

        self.mirror_button.setSelected(mirror)
        self.flip_button.setSelected(flip)

        self.doModal()


    def playVideo(self):
        self.player = StopResumePlayer(**{'camera_number': self.camera_number, 'monitor': self.monitor})
        self.player.maybe_stop_current()
        #if utils.get_bool_setting('mjpeg'):
        #    camera.enable_mjpeg()
        #    url = camera.mjpeg_url
        #else:
        #    url = camera.video_url
        self.player.play(self.camera_settings[7])
        
    def setupUi(self):
        Y_OFFSET = 100
        X_OFFSET = 20
        OFFSET1 = 32
        OFFSET2 = 64

        self.buttons = []

        self.up_button          = MoveButton(self, 'up', OFFSET1+X_OFFSET, Y_OFFSET, self.camera)
        self.left_button        = MoveButton(self, 'left', X_OFFSET, OFFSET1+Y_OFFSET, self.camera)        
        self.down_button        = MoveButton(self, 'down', OFFSET1+X_OFFSET, OFFSET2+Y_OFFSET, self.camera)    
        self.right_button       = MoveButton(self, 'right', OFFSET2+X_OFFSET, OFFSET1+Y_OFFSET, self.camera)
        self.left_up_button     = MoveButton(self, 'left_up', X_OFFSET, Y_OFFSET, self.camera)
        self.right_up_button    = MoveButton(self, 'right_up', OFFSET2+X_OFFSET, Y_OFFSET, self.camera)
        self.right_down_button  = MoveButton(self, 'right_down', OFFSET2+X_OFFSET, OFFSET2+Y_OFFSET, self.camera)
        self.left_down_button   = MoveButton(self, 'left_down', X_OFFSET, OFFSET2+Y_OFFSET, self.camera)
        self.home_button        = MoveButton(self, 'home', OFFSET1+X_OFFSET, OFFSET1+Y_OFFSET, self.camera)
        self.flip_button        = MirrorFlipButton(self, 'flip', 30, Y_OFFSET+200, self.camera)        
        self.mirror_button      = MirrorFlipButton(self, 'mirror', 30, Y_OFFSET+260, self.camera)  
        self.close_button       = Button(self, 'close', 1280-60, 20)       
        self.settings_button    = Button(self, 'settings', 1280-120, 20)

        self.addControl(self.up_button)
        self.addControl(self.left_button)
        self.addControl(self.down_button)
        self.addControl(self.right_button)
        self.addControl(self.left_up_button)
        self.addControl(self.right_up_button)
        self.addControl(self.right_down_button)
        self.addControl(self.left_down_button)
        self.addControl(self.home_button)
        self.addControl(self.flip_button)
        self.addControl(self.mirror_button)
        self.addControl(self.settings_button)
        self.addControl(self.close_button)
        
        self.setFocus(self.close_button)

        #up, down, left,right
        self.up_button.setNavigation        (self.mirror_button,    self.home_button,       self.left_up_button,    self.right_up_button)
        self.left_button.setNavigation      (self.left_up_button,   self.left_down_button,  self.close_button,      self.home_button)
        self.right_button.setNavigation     (self.right_up_button,  self.right_down_button, self.home_button,       self.settings_button)
        self.down_button.setNavigation      (self.home_button,      self.flip_button,       self.left_down_button,  self.right_down_button)
        self.left_up_button.setNavigation   (self.mirror_button,    self.left_button,       self.close_button,      self.up_button)
        self.right_up_button.setNavigation  (self.mirror_button,    self.right_button,      self.up_button,         self.settings_button)
        self.right_down_button.setNavigation(self.right_button,     self.flip_button,       self.down_button,       self.settings_button)
        self.left_down_button.setNavigation (self.left_button,      self.flip_button,       self.close_button,      self.down_button)
        self.home_button.setNavigation      (self.up_button,        self.down_button,       self.left_button,       self.right_button)
        self.flip_button.setNavigation      (self.down_button,      self.mirror_button,     self.close_button,      self.close_button)
        self.mirror_button.setNavigation    (self.flip_button,      self.up_button,         self.close_button,      self.close_button)
        self.settings_button.setNavigation  (self.mirror_button,    self.mirror_button,     self.right_button,      self.close_button)
        self.close_button.setNavigation     (self.mirror_button,    self.mirror_button,     self.settings_button,   self.right_button)
        


    def getControl(self, control):
        return next(button for button in self.buttons if button == control)
    
    def onControl(self, control):
        if control == self.close_button:
            self.stop()
        elif control == self.settings_button:
            pass
            #utils.open_settings()
        else:
            button = self.getControl(control)
            response = button.send_cmd(control)

            if not response:
                #msg = u"{0}: {1}".format(utils.get_string(32103), response.message)
                #utils.notify(msg)
                pass

                if isinstance(control, xbmcgui.ControlRadioButton):
                    control.setSelected(not control.isSelected())

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

    def onPlayBackStarted(self):
        self.monitor.set_camera_playing(self.camera_number)

    def onPlayBackEnded(self):
        self.monitor.clear_camera_playing(self.camera_number)

    def onPlayBackStopped(self):
        self.monitor.clear_camera_playing(self.camera_number)

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
            resume_time_str = "{0:.1f}".format(self.resume_time - self.monitor.playback_resume_time())
            print "Resuming {0} at {1}".format(self.previous_file, resume_time_str)
            listitem = xbmcgui.ListItem()
            listitem.setProperty('StartOffset', resume_time_str)
            self.play(self.previous_file, listitem)



def playCameraVideo(camera_settings, monitor):
    '''
    Text Here
    '''

    with CameraControlsWindow(camera_settings, monitor) as camera_player:
        camera_player.start()






if __name__ == "__main__":
    pass



  



        



            
            
