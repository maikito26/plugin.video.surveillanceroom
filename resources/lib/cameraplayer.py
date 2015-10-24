"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

Module which controls how a single IP camera plays fullscreen
"""

import xbmc, xbmcgui, xbmcaddon
import os
import settings, utils, camerasettings, foscam2

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')

_btnimage = xbmc.translatePath('special://home/addons/%s/resources/media/{0}.png' %__addonid__ ).decode('utf-8')

# Kodi key action codes.
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_BACKSPACE = 110
ACTION_STOP = 13
ACTION_SELECT_ITEM = 7
     

class Button(xbmcgui.ControlButton):
    """ Class reclasses the ControlButton class for use in this addon. """
    
    WIDTH = HEIGHT = 32

    def __new__(cls, parent, action, x, y, scaling = 1.0):
        focusTexture    = _btnimage.format(action)
        noFocusTexture  = _btnimage.format(action+ '_nofocus')
        width           = int(round(cls.WIDTH * scaling))
        height          = int(round(cls.HEIGHT * scaling))
        
        self = super(Button, cls).__new__(cls, x, y, width, height, '',
                                          focusTexture, noFocusTexture)
        parent.buttons.append(self)
        return self


class ToggleButton(xbmcgui.ControlRadioButton):
    """ Class reclasses the RadioButton class for use in this addon. """
    
    WIDTH = 110
    HEIGHT = 40

    def __new__(cls, parent, action, x, y):
        focusOnTexture      = _btnimage.format('radio-on')
        noFocusOnTexture    = _btnimage.format('radio-on')
        focusOffTexture     = _btnimage.format('radio-off')
        noFocusOffTexture   = _btnimage.format('radio-off')
        focusTexture        = _btnimage.format('back')
        noFocusTexture      = _btnimage.format('trans')
        textOffsetX         = 12

        self = super(ToggleButton, cls).__new__(cls, x, y, cls.WIDTH, cls.HEIGHT, action.title(),
                                                focusOnTexture, noFocusOnTexture,
                                                focusOffTexture, noFocusOffTexture,
                                                focusTexture, noFocusTexture,
                                                textOffsetX)

        self.action = action
        parent.buttons.append(self)
        return self



class CameraControlsWindow(xbmcgui.WindowDialog):
    """
    Class is used to create a single camera playback window of the camera view with controls
    """
    
    def __init__(self, camera_settings, monitor):
        self.monitor = monitor
        self.camera_settings = camera_settings
        self.camera_number = camera_settings[0]
        self.camera = foscam2.FoscamCamera(self.camera_settings)
        self.sensitivity = settings.getSetting_float('ptz_sensitivity%s' %self.camera_number) / 10
    
    def __enter__(self):
        return self
    
    def start(self):
        self.playVideo()
        self.doModal()
               
    def playVideo(self):
        self.player = StopResumePlayer(**{'camera_number': self.camera_number, 'monitor': self.monitor, 'callback1': self.setupUi, 'callback2': self.stop})
        url = settings.getStreamUrl(0, self.camera_number)
        listitem = xbmcgui.ListItem()

        #Hack to improve perceived responsiveness of Stream and Button Presets
        hack_enabled = settings.getSetting_bool('hack1')
        utils.log(2, 'Hack is enabled: %s' %hack_enabled)
        if hack_enabled:
            listitem.setProperty('StartOffset', '20')   
        
        self.player.maybe_stop_current()
        self.player.play(url, listitem)        
        
    def setupUi(self):
        response_code, response = self.camera.get_mirror_and_flip_setting()
        if response_code == 0:

            # Button Placement settings
            Y_OFFSET    = 100
            X_OFFSET    = 20
            OFFSET1     = 32
            OFFSET2     = 64

            self.buttons = []
            
            # Default Foscam Buttons
            self.flip_button        = ToggleButton(self, 'flip', 30, Y_OFFSET+200)        
            self.mirror_button      = ToggleButton(self, 'mirror', 30, Y_OFFSET+260)  
            self.close_button       = Button(self, 'close', 1280-60, 20)       
            self.addon_settings_button      = Button(self, 'addon_settings', 1280-120, 20)
            self.camera_settings_button     = Button(self, 'camera_settings', 1280-180, 20)
            
            self.addControl(self.addon_settings_button)
            self.addControl(self.camera_settings_button)
            self.addControl(self.close_button)
            self.addControl(self.flip_button)
            self.addControl(self.mirror_button)
            
            self.mirror_button.setSelected(int(response.get('isMirror')))
            self.flip_button.setSelected(int(response.get('isFlip')))
            
            self.flip_button.setNavigation(self.camera_settings_button, self.mirror_button, self.close_button, self.camera_settings_button)
            self.mirror_button.setNavigation(self.flip_button, self.close_button, self.close_button, self.camera_settings_button)
            self.addon_settings_button.setNavigation(self.mirror_button, self.flip_button, self.camera_settings_button, self.close_button)
            self.camera_settings_button.setNavigation(self.mirror_button, self.flip_button, self.flip_button, self.addon_settings_button)
            self.close_button.setNavigation (self.mirror_button, self.flip_button, self.addon_settings_button, self.flip_button)

            # PTZ Buttons
            ptz = settings.getSetting_int('ptz', self.camera_number)

            self.pan_tilt = False
            if ptz > 0: 
                self.pan_tilt = True

            self.zoom = False
            if ptz > 1:
                self.zoom = True
                
            if self.pan_tilt:
                
                self.up_button          = Button(self, 'up', OFFSET1+X_OFFSET, Y_OFFSET)
                self.left_button        = Button(self, 'left', X_OFFSET, OFFSET1+Y_OFFSET)        
                self.down_button        = Button(self, 'down', OFFSET1+X_OFFSET, OFFSET2+Y_OFFSET)    
                self.right_button       = Button(self, 'right', OFFSET2+X_OFFSET, OFFSET1+Y_OFFSET)
                self.top_left_button        = Button(self, 'top_left', X_OFFSET, Y_OFFSET)
                self.top_right_button       = Button(self, 'top_right', OFFSET2+X_OFFSET, Y_OFFSET)
                self.bottom_right_button    = Button(self, 'bottom_right', OFFSET2+X_OFFSET, OFFSET2+Y_OFFSET)
                self.bottom_left_button     = Button(self, 'bottom_left', X_OFFSET, OFFSET2+Y_OFFSET)
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
                
                self.flip_button.setNavigation(self.down_button, self.mirror_button, self.close_button, self.camera_settings_button)
                self.mirror_button.setNavigation(self.flip_button, self.preset_button, self.close_button, self.camera_settings_button)
                self.preset_button.setNavigation(self.mirror_button, self.up_button, self.close_button, self.camera_settings_button)
                self.addon_settings_button.setNavigation(self.preset_button, self.preset_button, self.camera_settings_button, self.close_button)
                self.camera_settings_button.setNavigation(self.preset_button, self.preset_button, self.right_button, self.addon_settings_button)
                self.close_button.setNavigation(self.preset_button, self.preset_button, self.addon_settings_button, self.left_button)
                self.up_button.setNavigation(self.preset_button, self.home_button, self.top_left_button, self.top_right_button)
                self.left_button.setNavigation(self.top_left_button, self.bottom_left_button, self.close_button, self.home_button)
                self.right_button.setNavigation(self.top_right_button, self.bottom_right_button, self.home_button, self.camera_settings_button)
                self.down_button.setNavigation(self.home_button, self.flip_button, self.bottom_left_button, self.bottom_right_button)
                self.top_left_button.setNavigation(self.preset_button, self.left_button, self.close_button, self.up_button)
                self.top_right_button.setNavigation(self.preset_button, self.right_button, self.up_button, self.camera_settings_button)
                self.bottom_right_button.setNavigation(self.right_button, self.flip_button, self.down_button, self.camera_settings_button)
                self.bottom_left_button.setNavigation(self.left_button, self.flip_button, self.close_button, self.down_button)
                self.home_button.setNavigation(self.up_button, self.down_button, self.left_button, self.right_button)

                home_location = self.camera.ptz_home_location(0)
                self.preset_button.setSelected(home_location)

            if self.zoom:
                self.zoom_in_button = Button(self, 'zoom_in', OFFSET2+X_OFFSET+32, Y_OFFSET)
                self.zoom_out_button = Button(self, 'zoom_out', OFFSET2+X_OFFSET+32, OFFSET2+Y_OFFSET)
                self.addControl(self.zoom_in_button)
                self.addControl(self.zoom_out_button)

                # Navigation still requires to be set #
            
            self.setFocus(self.close_button)

    def getControl(self, control):
        return next(button for button in self.buttons if button == control)
    
    def onControl(self, control):
        if control == self.close_button:        self.stop()
        elif control == self.flip_button:       self.camera.flip_video()
        elif control == self.mirror_button:     self.camera.mirror_video()
        elif control == self.addon_settings_button:   __addon__.openSettings()
        elif control == self.camera_settings_button:   self.open_camera_settings()
        
        elif self.pan_tilt:
            if control == self.home_button:     home_location = self.camera.ptz_home_location(2)
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

                self.monitor.waitForAbort(self.sensitivity)         #Move Button Sensitivity
                self.camera.ptz_stop_run()
                
        elif self.zoom:
            if control == self.zoom_in_button:     self.camera.ptz_zoom_in()
            elif control == self.zoom_out_button:   self.camera.ptz_zoom_out()

            self.monitor.waitForAbort(self.sensitivity)  #Move Button Sensitivity
            self.camera.ptz_zoom_stop()

    def open_camera_settings(self):
        settings_window = camerasettings.CameraSettingsWindow(self.camera_number)
        settings_window.doModal()
        del settings_window
        utils.notify('Some changes may not take affect until the service is restarts.')
        
    def toggle_preset(self):
        if self.preset_button.isSelected():
            self.camera.ptz_add_preset()
            utils.notify('Home Location is now Current Location')
        else:
            self.camera.ptz_delete_preset()
            utils.notify('Home Location is now Default Location')

    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU,
                      ACTION_BACKSPACE,
                      ACTION_NAV_BACK,
                      ACTION_STOP):
            self.stop()

    def stop(self):
        self.close()
        self.player.stop()
        self.player.maybe_resume_previous()

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


class StopResumePlayer(xbmc.Player):
    """
    Kodi Video Player reclassed to include added functionality.
    Allows stopping the currently playing video to view a preview in fullscreen
    and then resume the original playing video.
    """

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

        utils.log(4, 'Player Initialized with kwargs :: %s' %kwargs)

    def onPlayBackStarted(self):
        utils.log(4, 'Playback has started for camera %s' %self.camera_number)
        self.monitor.set_camera_playing(self.camera_number)
        self.callback1()        #SetupUi() - for camera controls, waits until it is playing to draw controls for User Experience
        #self.seekTime(4)        #Potential hack for improving stream's perceived response to ptz movement

    def onPlayBackEnded(self):
        utils.log(4, 'Playback has ended for camera %s' %self.camera_number)
        self.monitor.clear_camera_playing(self.camera_number)
        self.callback2()        #stop() - for the preview window

    def onPlayBackStopped(self):
        utils.log(4, 'Playback has stopped for camera %s' %self.camera_number)
        self.monitor.reset_camera_playing(self.camera_number)
        self.callback2()        #stop() - for the preview window

    def stop(self):
        utils.log(4, 'Player told to stop for camera %s' %self.camera_number)
        self.monitor.reset_camera_playing(self.camera_number)
        xbmc.executebuiltin('PlayerControl(Stop)')          # Because player.stop() was losing the player and didn't work *sad face*
        
    def maybe_stop_current(self):
        """ If there is a video playing, it will capture the source and current playback time """
        
        if self.isPlaying():
            self.resume_time = self.getTime()
            self.previous_file = self.getPlayingFile()
            self.stop()
            utils.log(2, "Stopped {0}".format(self.previous_file))
            
        else:
            self.previous_file = None

    def maybe_resume_previous(self):
        """ If a video was playing previously, it will restart it at the resume time """
        
        if self.previous_file is not None:
            resume_time_adjustment = settings.getSetting_int('resume_time')
            resume_time_str = "{0:.1f}".format(self.resume_time - resume_time_adjustment)
            utils.log(2, "Resuming {0} at {1}".format(self.previous_file, resume_time_str))
            listitem = xbmcgui.ListItem()
            listitem.setProperty('StartOffset', resume_time_str)
            self.play(self.previous_file, listitem)


def play(camera_number, monitor, camera_type=None):
    """
    Function to call to play the IP Camera feed.  Determines if controls are shown or not.

    camera_type == 3: No Controls
    """

    camera_settings = settings.getBasicSettings(camera_number)

    if camera_settings:
        
        if not camera_type:
            camera_type = settings.getCameraType(camera_number)

        # Foscam Camera
        if camera_type < 3:
            
            with CameraControlsWindow(camera_settings, monitor) as player:
                player.start()

        # Generic Camera or Foscam Called without Controls
        else:
            
            url = settings.getStreamUrl(0, camera_number)
            name = settings.getCameraName(camera_number)
            utils.log(4, 'Camera %s ::  Name: %s;  Url: %s' %(camera_number, name, url))
            
            listitem = xbmcgui.ListItem()
            listitem.setInfo(type = 'Video', infoLabels = {'Title': name})
            listitem.setArt({'thumb': utils.get_icon(camera_number)})
            
            player = StopResumePlayer(**{'camera_number': camera_number, 'monitor': monitor})

            utils.log(4, 'Camera %s ::  Starting generic player' %camera_number)
            player.play(url, listitem)
            
    else:
        
        utils.log(2, 'Camera %s is not configured correctly' %camera_number)
        utils.notify('Camera %s not configured correctly' %camera_number)


if __name__ == "__main__":
    pass



  



        



            
            
