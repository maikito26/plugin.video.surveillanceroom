"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

This module is used to draw a window that contains settings relevant to a Foscam HD camera
"""

import xbmc, xbmcgui, xbmcaddon
import settings, utils
import os

__addon__ = xbmcaddon.Addon()
__addonid__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')

_images = os.path.join(__path__, 'resources', 'textures')

# Text alighnment constants. Mixed variants are obtained by bit OR (|)
ALIGN_LEFT = 0
ALIGN_RIGHT = 1
ALIGN_CENTER_X = 2
ALIGN_CENTER_Y = 4
ALIGN_CENTER = 6
ALIGN_TRUNCATED = 8
ALIGN_JUSTIFY = 10

# Kodi key action codes.
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_MOUSE_WHEEL_UP = 104
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_DRAG = 106
ACTION_MOUSE_MOVE = 107
ACTION_MOUSE_LEFT_CLICK = 100
ACTION_BACKSPACE = 110
ACTION_STOP = 13
ACTION_SELECT_ITEM = 7

def _set_textures(textures, kwargs):
    """ Set texture arguments for controls. """
    for texture in textures.keys():
        if kwargs.get(texture) is None:
            kwargs[texture] = textures[texture]

class Button(xbmcgui.ControlButton):
    """
    ControlButton class.

    Implements a clickable button.
    Parameters:
    label: string or unicode - text string.
    focusTexture: string - filename for focus texture.
    noFocusTexture: string - filename for no focus texture.
    textOffsetX: integer - x offset of label.
    textOffsetY: integer - y offset of label.
    alignment: integer - alignment of label - *Note, see xbfont.h
    font: string - font used for label text. (e.g. 'font13')
    textColor: hexstring - color of enabled button's label. (e.g. '0xFFFFFFFF')
    disabledColor: hexstring - color of disabled button's label. (e.g. '0xFFFF3300')
    angle: integer - angle of control. (+ rotates CCW, - rotates CW)
    shadowColor: hexstring - color of button's label's shadow. (e.g. '0xFF000000')
    focusedColor: hexstring - color of focused button's label. (e.g. '0xFF00FFFF')

    Note:
        After you create the control, you need to add it to the window with placeControl().

    Example:
        self.button = Button('Status', font='font14')
    """
    
    def __new__(cls, *args, **kwargs):
        textures = {'focusTexture': os.path.join(_images, 'Button', 'KeyboardKey.png'),
                    'noFocusTexture': os.path.join(_images, 'Button', 'KeyboardKeyNF.png')}
        _set_textures(textures, kwargs)
        if kwargs.get('alignment') is None:
            kwargs['alignment'] = ALIGN_CENTER
        return super(Button, cls).__new__(cls, *args, **kwargs)

class RadioButton(xbmcgui.ControlRadioButton):
    """
    ControlRadioButton class.

    Implements a 2-state switch.
    Parameters:
    label: string or unicode - text string.
    focusTexture: string - filename for focus texture.
    noFocusTexture: string - filename for no focus texture.
    textOffsetX: integer - x offset of label.
    textOffsetY: integer - y offset of label.
    _alignment: integer - alignment of label - *Note, see xbfont.h
    font: string - font used for label text. (e.g. 'font13')
    textColor: hexstring - color of enabled radio button's label. (e.g. '0xFFFFFFFF')
    disabledColor: hexstring - color of disabled radio button's label. (e.g. '0xFFFF3300')
    angle: integer - angle of control. (+ rotates CCW, - rotates CW)
    shadowColor: hexstring - color of radio button's label's shadow. (e.g. '0xFF000000')
    focusedColor: hexstring - color of focused radio button's label. (e.g. '0xFF00FFFF')
    focusOnTexture: string - filename for radio focused/checked texture.
    noFocusOnTexture: string - filename for radio not focused/checked texture.
    focusOffTexture: string - filename for radio focused/unchecked texture.
    noFocusOffTexture: string - filename for radio not focused/unchecked texture.
    Note: To customize RadioButton all 4 abovementioned textures need to be provided.
    """
    
    def __new__(cls, *args, **kwargs):
        textures = {'focusTexture': os.path.join(_images, 'RadioButton', 'MenuItemFO.png'),
                    'noFocusTexture': os.path.join(_images, 'RadioButton', 'MenuItemNF.png'),
                    'focusOnTexture': os.path.join(_images, 'RadioButton', 'radiobutton-focus.png'),
                    'noFocusOnTexture': os.path.join(_images, 'RadioButton', 'radiobutton-focus.png'),
                    'focusOffTexture': os.path.join(_images, 'RadioButton', 'radiobutton-nofocus.png'),
                    'noFocusOffTexture': os.path.join(_images, 'RadioButton', 'radiobutton-nofocus.png')}

        _set_textures(textures, kwargs)
        return super(RadioButton, cls).__new__(cls, *args, **kwargs)


class CameraSettingsWindow(xbmcgui.WindowDialog):
    """
    The main window class
    
    Future Features:
    get_dev_name() | set_dev_name('name')
        devName

    get_osd_setting() | set_osd_setting(params)
        isEnableTimeStamp:  Time stamp will display on screen or not
        isEnableDevName:    Camera name will display on screen or not
        isEnableOSDMask:    Is OSD mask effective
    """
    
    def __init__(self, camera_number, title='Camera Settings'):
        import foscam2
        title = 'Camera Settings'
        
        self.x = 340
        self.y = 150
        width = 540
        height = 400

        self.ROW_START = 45
        self.ROW_HEIGHT = 30
        self.X_SHIFT = 10
        self.LABEL_WIDTH = 240

        self.camera_number = camera_number
        self.camera = foscam2.FoscamCamera(settings.getBasicSettings(self.camera_number))
        
        self.label_enabled = {0: 'Disabled',
                              1: 'Enabled'}

        self.label_interval = {5: '5 seconds',
                               6: '6 seconds',
                               7: '7 seconds',
                               8: '8 seconds',
                               9: '9 seconds',
                               10: '10 seconds',
                               11: '11 seconds',
                               12: '12 seconds',
                               13: '13 seconds',
                               14: '14 seconds',
                               15: '15 seconds'}

        self.label_sensitivity = {0: 'Low',
                                  1: 'Medium',
                                  2: 'High',
                                  3: 'Lower',
                                  4: 'Lowest'}

        # Draw the window controls
        self._place_window(width, height, title)
        self.place_irconfig(0)
        self.place_pt_speedconfig(1)
        self.place_z_speedconfig(2)
        self.get_motion_default()
        self.place_motion_enable(3)
        self.place_motion_sensitivityconfig(4)
        self.place_motion_triggerconfig(5)
        self.get_sound_default()
        self.place_sound_enable(6)
        self.place_sound_sensitivityconfig(7)
        self.place_sound_triggerconfig(8)
        self.place_mjpeg_enable(9)
        self.place_close_button(10)

        # Set up/down navigation
        self.window_close_button.controlDown(self.radio_irAuto)
        self.radio_irAuto.controlUp(self.window_close_button)
        self.radio_irOn.controlUp(self.window_close_button)
        self.radio_irOff.controlUp(self.window_close_button)
        self.radio_irAuto.controlDown(self.button_pt_speedup)
        self.radio_irOn.controlDown(self.button_pt_speeddown)
        self.radio_irOff.controlDown(self.button_pt_speeddown)
        self.button_pt_speedup.controlUp(self.radio_irAuto)
        self.button_pt_speeddown.controlUp(self.radio_irOff)
        self.button_pt_speedup.controlDown(self.button_z_speedup)
        self.button_pt_speeddown.controlDown(self.button_z_speeddown)
        self.button_z_speedup.controlUp(self.button_pt_speedup)
        self.button_z_speeddown.controlUp(self.button_pt_speeddown)
        self.button_z_speedup.controlDown(self.radio_motion)
        self.button_z_speeddown.controlDown(self.radio_motion)
        self.radio_motion.controlUp(self.button_z_speedup)
        self.radio_motion.controlDown(self.button_m_sensitivityup)
        self.button_m_sensitivityup.controlUp(self.radio_motion)
        self.button_m_sensitivitydown.controlUp(self.radio_motion)
        self.button_m_sensitivityup.controlDown(self.button_m_triggerup)
        self.button_m_sensitivitydown.controlDown(self.button_m_triggerup)
        self.button_m_triggerup.controlUp(self.button_m_sensitivityup)
        self.button_m_triggerdown.controlUp(self.button_m_sensitivitydown)
        self.button_m_triggerup.controlDown(self.radio_sound)
        self.button_m_triggerdown.controlDown(self.radio_sound)
        self.radio_sound.controlUp(self.button_m_triggerup)
        self.radio_sound.controlDown(self.button_s_sensitivityup)
        self.button_s_sensitivityup.controlUp(self.radio_sound)
        self.button_s_sensitivitydown.controlUp(self.radio_sound)
        self.button_s_sensitivityup.controlDown(self.button_s_triggerup)
        self.button_s_sensitivitydown.controlDown(self.button_s_triggerdown)
        self.button_s_triggerup.controlUp(self.button_s_sensitivityup)
        self.button_s_triggerdown.controlUp(self.button_s_sensitivitydown)
        self.button_s_triggerup.controlDown(self.radio_mjpeg)
        self.button_s_triggerdown.controlDown(self.radio_h264)
        self.radio_mjpeg.controlUp(self.button_s_triggerup)
        self.radio_h264.controlUp(self.button_s_triggerdown)
        self.radio_mjpeg.controlDown(self.button_close)
        self.radio_h264.controlDown(self.button_close)
        self.button_close.controlUp(self.radio_mjpeg)
        
        #Disable unsupported features
        ptz = settings.getSetting_int('ptz', self.camera_number)
        if ptz == 0: # Disable Pan & Tilt
            self.label_pt.setEnabled(False)
            self.button_pt_speedup.setEnabled(False)
            self.button_pt_speeddown.setEnabled(False)
            self.label_pt_speedsetting.setEnabled(False)
            
        if ptz < 2: # Disable Zoom:
            self.label_z.setEnabled(False)
            self.button_z_speedup.setEnabled(False)
            self.button_z_speeddown.setEnabled(False)
            self.label_z_speedsetting.setEnabled(False)

        motion_enabled, sound_enabled = settings.getEnabledAlarms(self.camera_number) 
        if not motion_enabled:
            self.label_m.setEnabled(False)
            self.label_ms.setEnabled(False)
            self.label_mt.setEnabled(False)
            self.radio_motion.setEnabled(False)
            self.button_m_triggerup.setEnabled(False)
            self.button_m_triggerdown.setEnabled(False)
            self.label_m_triggersetting.setEnabled(False)
            self.button_m_sensitivityup.setEnabled(False)
            self.button_m_sensitivitydown.setEnabled(False)
            self.label_m_sensitivitysetting.setEnabled(False)

        if not sound_enabled:
            self.label_s.setEnabled(False)
            self.label_ss.setEnabled(False)
            self.label_st.setEnabled(False)
            self.radio_sound.setEnabled(False)
            self.button_s_triggerup.setEnabled(False)
            self.button_s_triggerdown.setEnabled(False)
            self.label_s_triggersetting.setEnabled(False)
            self.button_s_sensitivityup.setEnabled(False)
            self.button_s_sensitivitydown.setEnabled(False)
            self.label_s_sensitivitysetting.setEnabled(False)

        self.setFocus(self.radio_irAuto)


    # CONTROLS #####################################
            
    def _place_window(self, width, height, title):
        """ Main window drawing """

        X_MARGIN = 5    # Horisontal adjustment for a header background if the main background has transparent edges. 
        Y_MARGIN = 5    # Vertical adjustment for a header background if the main background has transparent edges  
        Y_SHIFT = 4     # Header position adjustment if the main backround has visible borders.
        HEADER_HEIGHT = 35  # The height of a window header (for the title background and the title label).


        background_img = os.path.join(_images, 'AddonWindow', 'ContentPanel.png')
        background = xbmcgui.ControlImage(self.x, self.y, width, height, background_img)
        
        title_background_img = os.path.join(_images, 'AddonWindow', 'dialogheader.png')
        title_background = xbmcgui.ControlImage(self.x + X_MARGIN, self.y + Y_MARGIN, width - 2 * X_MARGIN, HEADER_HEIGHT, title_background_img)
        
        title_bar = xbmcgui.ControlLabel(self.x + X_MARGIN, self.y + Y_MARGIN + Y_SHIFT, width - 2 * X_MARGIN, HEADER_HEIGHT,
                                         title, alignment=ALIGN_CENTER, textColor='0xFFFFA500', font='font13_title')
        
        self.window_close_button = xbmcgui.ControlButton(self.x + width - 70, self.y + Y_MARGIN + Y_SHIFT, 60, 30, '',
                        focusTexture=os.path.join(_images, 'AddonWindow', 'DialogCloseButton-focus.png'),
                        noFocusTexture=os.path.join(_images, 'AddonWindow', 'DialogCloseButton.png'))
        
        self.addControl(background)
        self.addControl(title_background)
        self.addControl(title_bar)
        self.addControl(self.window_close_button)


    def place_close_button(self, row):
        """ Close Buttondrawing """

        BUTTON_WIDTH = 100
        self.button_close = Button(self.x + 220, self.y + self.ROW_START + self.ROW_HEIGHT * row + 15,
                                   BUTTON_WIDTH, self.ROW_HEIGHT, 'Close')
        self.addControl(self.button_close)

               
    def place_irconfig(self, row):
        """ IR LED Controls """
        
        label_value = 'IR LED Control'
        self.label_ir = xbmcgui.ControlLabel(self.x + self.X_SHIFT,
                                             self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                             self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 80
        SPACE = 20
        
        self.radio_irAuto = RadioButton(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                        self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                        BUTTON_WIDTH, self.ROW_HEIGHT, 'Auto')
        
        self.radio_irOn = RadioButton(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                      self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                      BUTTON_WIDTH, self.ROW_HEIGHT, 'On')
        
        self.radio_irOff = RadioButton(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH * 2 + SPACE,
                                       self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                       BUTTON_WIDTH, self.ROW_HEIGHT, 'Off')
        
        self.addControl(self.label_ir)
        self.addControl(self.radio_irAuto)
        self.addControl(self.radio_irOn)
        self.addControl(self.radio_irOff)

        self.radio_irAuto.controlLeft(self.radio_irOff)
        self.radio_irAuto.controlRight(self.radio_irOn)
        self.radio_irOn.controlLeft(self.radio_irAuto)
        self.radio_irOn.controlRight(self.radio_irOff)
        self.radio_irOff.controlLeft(self.radio_irOn)
        self.radio_irOff.controlRight(self.radio_irAuto)
        
        if int(self.camera.get_ir_config()[1].get('mode')) == 0:
            self.radio_irAuto.setSelected(True)
        else:
            if int(self.camera.get_dev_state()[1].get('infraLedState')) == 1:
                self.radio_irOn.setSelected(True)
            else:
                self.radio_irOff.setSelected(True)


    def place_pt_speedconfig(self, row):
        """ Pan and Tilt Camera Speed Controls """
        
        self.ptlabel = {0: 'Very Slow',
                1: 'Slow',
                2: 'Normal',
                3: 'Fast',
                4: 'Very Fast'}

        self.pt_speed = int(self.camera.get_ptz_speed()[1].get('speed'))

        label_value = 'Pan & Tilt Speed'
        self.label_pt = xbmcgui.ControlLabel(self.x + self.X_SHIFT,
                                             self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                             self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 40
        LABEL_WIDTH = 160
        SPACE = 20
        
        self.button_pt_speedup = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                        self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                        BUTTON_WIDTH, self.ROW_HEIGHT, '+')

        self.label_pt_speedsetting = xbmcgui.ControlLabel(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                                          self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                                          LABEL_WIDTH, self.ROW_HEIGHT, self.ptlabel.get(self.pt_speed), alignment = 6)
        
        self.button_pt_speeddown = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + LABEL_WIDTH + SPACE,
                                          self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                          BUTTON_WIDTH, self.ROW_HEIGHT, '-')

        self.addControl(self.label_pt)
        self.addControl(self.button_pt_speedup)
        self.addControl(self.label_pt_speedsetting)
        self.addControl(self.button_pt_speeddown)

        self.button_pt_speedup.controlLeft(self.button_pt_speeddown)
        self.button_pt_speedup.controlRight(self.button_pt_speeddown)
        self.button_pt_speeddown.controlLeft(self.button_pt_speedup)
        self.button_pt_speeddown.controlRight(self.button_pt_speedup)


    def place_z_speedconfig(self, row):
        """ Zoom Camera Speed controls """
        
        self.zlabel = {0: 'Slow',
                       1: 'Normal',
                       2: 'Fast',}

        self.z_speed = int(self.camera.get_ptz_zoom_speed()[1].get('speed'))

        label_value = 'Zoom Speed'
        self.label_z = xbmcgui.ControlLabel(self.x + self.X_SHIFT,
                                            self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                            self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 40
        LABEL_WIDTH = 160
        SPACE = 20
        
        self.button_z_speedup = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                       self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                       BUTTON_WIDTH, self.ROW_HEIGHT, '+')

        self.label_z_speedsetting = xbmcgui.ControlLabel(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                                         self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                                         LABEL_WIDTH, self.ROW_HEIGHT, self.zlabel.get(self.z_speed), alignment = 6)
        
        self.button_z_speeddown = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + LABEL_WIDTH + SPACE,
                                         self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                         BUTTON_WIDTH, self.ROW_HEIGHT, '-')

        self.addControl(self.label_z)
        self.addControl(self.button_z_speedup)
        self.addControl(self.label_z_speedsetting)
        self.addControl(self.button_z_speeddown)

        self.button_z_speedup.controlLeft(self.button_z_speeddown)
        self.button_z_speedup.controlRight(self.button_z_speeddown)
        self.button_z_speeddown.controlLeft(self.button_z_speedup)
        self.button_z_speeddown.controlRight(self.button_z_speedup)


    def place_mjpeg_enable(self, row):
        """ Enable MJPEG Video Control """
        
        label_value = 'Substream Type'
        self.label_mjpeg = xbmcgui.ControlLabel(self.x + self.X_SHIFT,
                                                self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                                self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 120
        SPACE = 20
        
        self.radio_mjpeg = RadioButton(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                        self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                        BUTTON_WIDTH, self.ROW_HEIGHT, 'MJPEG')

        self.radio_h264 = RadioButton(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                      self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                      BUTTON_WIDTH, self.ROW_HEIGHT, 'h264')
        
        self.addControl(self.label_mjpeg)
        self.addControl(self.radio_mjpeg)
        self.addControl(self.radio_h264)

        self.radio_mjpeg.controlLeft(self.radio_h264)
        self.radio_mjpeg.controlRight(self.radio_h264)
        self.radio_h264.controlLeft(self.radio_mjpeg)
        self.radio_h264.controlRight(self.radio_mjpeg)

    
    # MOTION #######################################################    
    def get_motion_default(self):
        """ Function to get motion config from a single camera respnse """ 
        sound_defaults = self.camera.get_motion_detect_config()[1]
        self.m_enable = int(sound_defaults.get('isEnable'))
        self.m_trigger = int(sound_defaults.get('triggerInterval'))
        self.m_sensitivity = int(sound_defaults.get('sensitivity'))


    def place_motion_enable(self, row):
        """ Enable Motion Detection button """
        
        label_value = 'Motion Detection'
        self.label_m = xbmcgui.ControlLabel(self.x + self.X_SHIFT, self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                            self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)
        
        BUTTON_WIDTH = 160
        
        self.radio_motion = RadioButton(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                        self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                        BUTTON_WIDTH, self.ROW_HEIGHT, self.label_enabled.get(self.m_enable))
        
        self.addControl(self.label_m)
        self.addControl(self.radio_motion)
        
        if self.m_enable == 1:
            self.radio_motion.setSelected(True)

        
    def place_motion_sensitivityconfig(self, row):
        """ Motion Detection Sensitivity control """
        
        label_value = 'Motion Sensitivity'
        self.label_ms = xbmcgui.ControlLabel(self.x + self.X_SHIFT, self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                             self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 40
        LABEL_WIDTH = 160
        SPACE = 20
        
        self.button_m_sensitivityup = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH, self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                             BUTTON_WIDTH, self.ROW_HEIGHT, '+')

        self.label_m_sensitivitysetting = xbmcgui.ControlLabel(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                                               self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                                               LABEL_WIDTH, self.ROW_HEIGHT, self.label_sensitivity.get(self.m_sensitivity), alignment = 6)
        
        self.button_m_sensitivitydown = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + LABEL_WIDTH + SPACE,
                                               self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                               BUTTON_WIDTH, self.ROW_HEIGHT, '-')

        self.addControl(self.label_ms)
        self.addControl(self.button_m_sensitivityup)
        self.addControl(self.label_m_sensitivitysetting)
        self.addControl(self.button_m_sensitivitydown)

        self.button_m_sensitivityup.controlLeft(self.button_m_sensitivitydown)
        self.button_m_sensitivityup.controlRight(self.button_m_sensitivitydown)
        self.button_m_sensitivitydown.controlLeft(self.button_m_sensitivityup)
        self.button_m_sensitivitydown.controlRight(self.button_m_sensitivityup)


    def place_motion_triggerconfig(self, row):
        """ Motion detection trigger interval control """
        
        label_value = 'Motion Trigger Interval'
        self.label_mt = xbmcgui.ControlLabel(self.x + self.X_SHIFT, self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                             self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 40
        LABEL_WIDTH = 160
        SPACE = 20
        
        self.button_m_triggerup = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                         self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                         BUTTON_WIDTH, self.ROW_HEIGHT, '+')

        self.label_m_triggersetting = xbmcgui.ControlLabel(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                                           self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                                           LABEL_WIDTH, self.ROW_HEIGHT, self.label_interval.get(self.m_trigger), alignment = 6)
        
        self.button_m_triggerdown = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + LABEL_WIDTH + SPACE,
                                           self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                           BUTTON_WIDTH, self.ROW_HEIGHT, '-')

        self.addControl(self.label_mt)
        self.addControl(self.button_m_triggerup)
        self.addControl(self.label_m_triggersetting)
        self.addControl(self.button_m_triggerdown)

        self.button_m_triggerup.controlLeft(self.button_m_triggerdown)
        self.button_m_triggerup.controlRight(self.button_m_triggerdown)
        self.button_m_triggerdown.controlLeft(self.button_m_triggerup)
        self.button_m_triggerdown.controlRight(self.button_m_triggerup)


    # SOUND #######################################################
    def get_sound_default(self):
        """ Function to get sound config from a single camera respnse """ 
        sound_defaults = self.camera.get_sound_detect_config()[1]
        self.s_enable = int(sound_defaults.get('isEnable'))
        self.s_trigger = int(sound_defaults.get('triggerInterval'))
        self.s_sensitivity = int(sound_defaults.get('sensitivity'))


    def place_sound_enable(self, row):
        """ Enable sound detection button """
    
        label_value = 'Sound Detection'
        self.label_s = xbmcgui.ControlLabel(self.x + self.X_SHIFT, self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                            self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 160
        
        self.radio_sound = RadioButton(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                        self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                        BUTTON_WIDTH, self.ROW_HEIGHT, self.label_enabled.get(self.s_enable))
        
        self.addControl(self.label_s)
        self.addControl(self.radio_sound)
        
        if self.s_enable == 1:
            self.radio_sound.setSelected(True)


    def place_sound_sensitivityconfig(self, row):
        """ Sound detection sensitivity control """
        
        label_value = 'Sound Sensitivity'
        self.label_ss = xbmcgui.ControlLabel(self.x + self.X_SHIFT, self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                             self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 40
        LABEL_WIDTH = 160
        SPACE = 20
        
        self.button_s_sensitivityup = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                             self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                             BUTTON_WIDTH, self.ROW_HEIGHT, '+')

        self.label_s_sensitivitysetting = xbmcgui.ControlLabel(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                                               self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                                               LABEL_WIDTH, self.ROW_HEIGHT,
                                                               self.label_sensitivity.get(self.s_sensitivity), alignment = 6)
        
        self.button_s_sensitivitydown = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + LABEL_WIDTH + SPACE,
                                               self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                               BUTTON_WIDTH, self.ROW_HEIGHT, '-')

        self.addControl(self.label_ss)
        self.addControl(self.button_s_sensitivityup)
        self.addControl(self.label_s_sensitivitysetting)
        self.addControl(self.button_s_sensitivitydown)

        self.button_s_sensitivityup.controlLeft(self.button_s_sensitivitydown)
        self.button_s_sensitivityup.controlRight(self.button_s_sensitivitydown)
        self.button_s_sensitivitydown.controlLeft(self.button_s_sensitivityup)
        self.button_s_sensitivitydown.controlRight(self.button_s_sensitivityup)

        
    def place_sound_triggerconfig(self, row):
        """ Sound detection trigger interval control """
        
        label_value = 'Sound Trigger Interval'
        self.label_st = xbmcgui.ControlLabel(self.x + self.X_SHIFT, self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                     self.LABEL_WIDTH, self.ROW_HEIGHT, label_value)

        BUTTON_WIDTH = 40
        LABEL_WIDTH = 160
        SPACE = 20
        
        self.button_s_triggerup = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH,
                                         self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                         BUTTON_WIDTH, self.ROW_HEIGHT, '+')

        self.label_s_triggersetting = xbmcgui.ControlLabel(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + SPACE,
                                                           self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                                           LABEL_WIDTH, self.ROW_HEIGHT,
                                                           self.label_interval.get(self.s_trigger), alignment = 6)
        
        self.button_s_triggerdown = Button(self.x + self.X_SHIFT + self.LABEL_WIDTH + BUTTON_WIDTH + LABEL_WIDTH + SPACE,
                                           self.y + self.ROW_START + self.ROW_HEIGHT * row,
                                           BUTTON_WIDTH, self.ROW_HEIGHT, '-')

        self.addControl(self.label_st)
        self.addControl(self.button_s_triggerup)
        self.addControl(self.label_s_triggersetting)
        self.addControl(self.button_s_triggerdown)

        self.button_s_triggerup.controlLeft(self.button_s_triggerdown)
        self.button_s_triggerup.controlRight(self.button_s_triggerdown)
        self.button_s_triggerdown.controlLeft(self.button_s_triggerup)
        self.button_s_triggerdown.controlRight(self.button_s_triggerup)

    
    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU:
            self.close()
        elif action == ACTION_BACKSPACE:
            self.close()

    def onControl(self, control):
        if control == self.window_close_button:     self.close()
        elif control == self.button_close:          self.close()
        elif control == self.radio_irAuto:          self.irAuto_update()
        elif control == self.radio_irOn:            self.irOn_update()
        elif control == self.radio_irOff:           self.irOff_update()
        elif control == self.button_pt_speedup:     self.pt_speedup()
        elif control == self.button_pt_speeddown:   self.pt_speeddown()
        elif control == self.button_z_speedup:      self.z_speedup()
        elif control == self.button_z_speeddown:    self.z_speeddown()
        elif control == self.radio_motion:          self.motion_update()
        elif control == self.button_m_sensitivityup:    self.m_sensitivityup()
        elif control == self.button_m_sensitivitydown:  self.m_sensitivitydown()
        elif control == self.button_m_triggerup:    self.m_triggerup()
        elif control == self.button_m_triggerdown:  self.m_triggerdown()
        elif control == self.radio_sound:           self.sound_update()
        elif control == self.button_s_sensitivityup:    self.s_sensitivityup()
        elif control == self.button_s_sensitivitydown:  self.s_sensitivitydown()
        elif control == self.button_s_triggerup:    self.s_triggerup()
        elif control == self.button_s_triggerdown:  self.s_triggerdown()
        elif control == self.radio_mjpeg:           self.mjpeg_update()
        elif control == self.radio_h264:            self.h264_update()
        

    
    # EVENTS #########################################################
    
    def irAuto_update(self):
        self.radio_irAuto.setSelected(True)
        self.radio_irOn.setSelected(False)
        self.radio_irOff.setSelected(False)
        self.camera.set_ir_config(0)

    def irOn_update(self):
        self.radio_irAuto.setSelected(False)
        self.radio_irOn.setSelected(True)
        self.radio_irOff.setSelected(False)
        self.camera.set_ir_config(1)
        self.camera.set_ir_on()

    def irOff_update(self):
        self.radio_irAuto.setSelected(False)
        self.radio_irOn.setSelected(False)
        self.radio_irOff.setSelected(True)
        self.camera.set_ir_config(1)
        self.camera.set_ir_off()

    def mjpeg_update(self):
        self.radio_mjpeg.setSelected(True) 
        self.radio_h264.setSelected(False) 
        self.camera.enable_mjpeg()

    def h264_update(self):
        self.radio_mjpeg.setSelected(False) 
        self.radio_h264.setSelected(True) 
        self.camera.disable_mjpeg()

    # PTZ EVENTS ##############

    def pt_speedup(self):
        if self.pt_speed < 4:
            self.pt_speed += 1
            self.camera.set_ptz_speed(self.pt_speed)
            self.label_pt_speedsetting.setLabel(self.ptlabel.get(self.pt_speed))

    def pt_speeddown(self):
        if self.pt_speed > 0:
            self.pt_speed -= 1
            self.camera.set_ptz_speed(self.pt_speed)
            self.label_pt_speedsetting.setLabel(self.ptlabel.get(self.pt_speed))

    def z_speedup(self):
        if self.z_speed < 2:
            self.z_speed += 1
            self.camera.set_ptz_zoom_speed(self.z_speed)
            self.label_z_speedsetting.setLabel(self.zlabel.get(self.z_speed))

    def z_speeddown(self):
        if self.z_speed > 0:
            self.z_speed -= 1
            self.camera.set_ptz_zoom_speed(self.z_speed)
            self.label_z_speedsetting.setLabel(self.zlabel.get(self.z_speed))

    # MOTION EVENTS ########################

    def motion_update(self):
        if self.radio_motion.isSelected():
            self.m_enable = 1
            self.camera.enable_motion_detection()                              
        else:
            self.camera.disable_motion_detection()
            self.m_enable = 0
        self.radio_motion.setLabel(self.label_enabled.get(self.m_enable))

    def m_triggerup(self):
        if self.m_trigger < 15:
            self.m_trigger += 1
            self.camera.set_motion_triggerinterval(self.m_trigger)
            self.label_m_triggersetting.setLabel(self.label_interval.get(self.m_trigger))

    def m_triggerdown(self):
        if self.m_trigger > 5:
            self.m_trigger -= 1
            self.camera.set_motion_triggerinterval(self.m_trigger)
            self.label_m_triggersetting.setLabel(self.label_interval.get(self.m_trigger))

    def m_sensitivityup(self):
        #4 -> 3 -> 0 -> 1 -> 2 
        if self.m_sensitivity != 2:
            if self.m_sensitivity < 2:
                self.m_sensitivity += 1
            elif self.m_sensitivity == 4:
               self.m_sensitivity = 3  
            elif self.m_sensitivity == 3:
                self.m_sensitivity = 0
            
            self.camera.set_motion_sensitivity(self.m_sensitivity)
            self.label_m_sensitivitysetting.setLabel(self.label_sensitivity.get(self.m_sensitivity))

    def m_sensitivitydown(self):
        # 2 -> 1 -> 0 -> 3 -> 4
        if self.m_sensitivity != 4:
            if self.m_sensitivity > 0 and self.m_sensitivity < 3:
                self.m_sensitivity -= 1
            elif self.m_sensitivity == 0:
               self.m_sensitivity = 3
            elif self.m_sensitivity == 3:
                self.m_sensitivity = 4
                    
            self.camera.set_motion_sensitivity(self.m_sensitivity)
            self.label_m_sensitivitysetting.setLabel(self.label_sensitivity.get(self.m_sensitivity))

    # SOUND EVENTS ########################

    def sound_update(self):
        if self.radio_sound.isSelected():
            self.s_enable = 1
            self.camera.enable_sound_detection()                              
        else:
            self.camera.disable_sound_detection()
            self.s_enable = 0
        self.radio_sound.setLabel(self.label_enabled.get(self.s_enable))

    def s_triggerup(self):
        if self.s_trigger < 15:
            self.s_trigger += 1
            self.camera.set_sound_triggerinterval(self.s_trigger)
            self.label_s_triggersetting.setLabel(self.label_interval.get(self.s_trigger))

    def s_triggerdown(self):
        if self.s_trigger > 5:
            self.s_trigger -= 1
            self.camera.set_sound_triggerinterval(self.s_trigger)
            self.label_s_triggersetting.setLabel(self.label_interval.get(self.s_trigger))

    def s_sensitivityup(self):
        #4 -> 3 -> 0 -> 1 -> 2 
        if self.s_sensitivity != 2:
            if self.s_sensitivity < 2:
                self.s_sensitivity += 1
            elif self.s_sensitivity == 4:
               self.s_sensitivity = 3 
            elif self.s_sensitivity == 3:
                self.s_sensitivity = 0
            
            self.camera.set_sound_sensitivity(self.s_sensitivity)
            self.label_s_sensitivitysetting.setLabel(self.label_sensitivity.get(self.s_sensitivity))

    def s_sensitivitydown(self):
        # 2 -> 1 -> 0 -> 3 -> 4
        if self.s_sensitivity != 4:
            if self.s_sensitivity > 0 and self.m_sensitivity < 3:
                self.s_sensitivity -= 1
            elif self.s_sensitivity == 0:
               self.s_sensitivity = 3 
            elif self.s_sensitivity == 3:
                self.s_sensitivity = 4
                    
            self.camera.set_sound_sensitivity(self.s_sensitivity)
            self.label_s_sensitivitysetting.setLabel(self.label_sensitivity.get(self.s_sensitivity))


if __name__ == "__main__":
    pass



  



        



            
            
