import xbmc
import xbmcaddon
import xbmcgui
from resources.lib import foscam
from functools import partial

__addon__ = xbmcaddon.Addon('plugin.video.mycam')
__addonid__ = __addon__.getAddonInfo('id')

''' Common GUI images '''
__loader__ = xbmc.translatePath('special://home/addons/%s/resources/media/loader.gif' %__addonid__ ).decode('utf-8')
__holder__ = xbmc.translatePath('special://home/addons/%s/resources/media/holder.png' %__addonid__ ).decode('utf-8')
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

    


class CameraPreviewWindow(xbmcgui.WindowDialog):
    '''
    Class is used to create the picture-in-picture window of the camera view
    '''
    
    def __init__(self, camera_settings, monitor):
        self.monitor = monitor
        self.camera_number = camera_settings[0]
        self.snapshotURL = camera_settings[6]
        scaling = camera_settings[16]
        position = camera_settings[15]
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
        self.show()

    def stop(self):
        self.close()
        self.monitor.preview_window_close(self.camera_number)

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
        #xbmc.executebuiltin("RunAddon({0})".format(utils.addon_info('id')))
        self.stop()











if __name__ == "__main__":
    pass

