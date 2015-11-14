"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

Wrapper for Camera API

"""
import utils, settings
import ipcam_api_foscamhd, ipcam_api_foscamsd, ipcam_api_generic

FOSCAM_HD = 0
FOSCAM_SD = 1
FOSCAM_HD_OVERRIDE = 2
GENERIC_IPCAM = 3

SINGLE_CAMERA_PLAYER = 0
ALL_CAMERA_PLAYER = 1
PREVIEW_WINDOW = 2

class CameraAPIWrapper(object):
    '''A python implementation of the foscam HD816W'''

    def __init__(self, camera_number, daemon = False, verbose = True):

        self.camera_number = str(camera_number)
        self.camera_type = settings.getCameraType(self.camera_number)
        camera_settings = self.getCameraSettings()

        # This is where we determine which API to use!
        if self.camera_type == FOSCAM_HD:
            self.camera = ipcam_api_foscamhd.FoscamCamera(camera_settings, daemon, verbose)
            
        elif self.camera_type == FOSCAM_SD:
            self.camera = ipcam_api_foscamsd.FoscamCamera(camera_settings, daemon, verbose)

        elif self.camera_type == FOSCAM_HD_OVERRIDE:
            self.camera = ipcam_api_foscamhd.FoscamCameraOverride(camera_settings, daemon, verbose)

        elif self.camera_type == GENERIC_IPCAM:
            self.camera = ipcam_api_generic.GenericIPCam(camera_settings, daemon, verbose)

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
	return None

    def getCameraSettings(self):
        """ Returns the login details of the camera """
        #utils.log(4, 'SETTINGS :: Use Cache: %s;  Camera %s;  Camera Type: %s' %(useCache, self.camera_number, self.camera_type)) 

        ''' Foscam Camera '''      
        if self.camera_type != GENERIC_IPCAM:
              
            host = settings.getSetting('host', self.camera_number)
            if not host:
                utils.log(3, 'SETTINGS :: Camera %s - No host specified.' %self.camera_number)
                host = ''
            
            port = settings.getSetting('port', self.camera_number)
            if not port:
                utils.log(3, 'SETTINGS :: Camera %s - No port specified.' %self.camera_number)
                port = ''
            
            username = settings.getSetting('user', self.camera_number)
            invalid = settings.invalid_user_char(username)
            if invalid:
                utils.log(3, 'SETTINGS :: Camera %s - Invalid character in user name: %s' %(self.camera_number, invalid))
                username = ''
            
            password = settings.getSetting('pass', self.camera_number)
            invalid = settings.invalid_password_char(password)
            if invalid:
                utils.log(3, 'SETTINGS :: Camera %s - Invalid character in password: %s' %(self.camera_number, invalid))
                password = ''

            return [self.camera_number, host, port, username, password]
                        
        else:
            ''' Generic IP Camera '''                   
            return [self.camera_number, '', '', '', '']

    def Connected(self, monitor = None, useCache = True):
        # Camera test and caching logic
        if monitor:
            if useCache:
                utils.log(2, 'SETTINGS :: Camera %s - Checking previous test result...' %self.camera_number)
                return monitor.testResult(self.camera_number)
                    
            else:
                if self.camera_type != GENERIC_IPCAM:
                    utils.log(2, 'SETTINGS :: Camera %s - Testing connection...' %self.camera_number)

                    success_code, response = self.camera.get_dev_state()
                    monitor.write_testResult(self.camera_number, success_code)
                
                    if success_code != 0:
                        return False
            
                    utils.log(2, 'SETTINGS :: Successful connection to Camera %s' %self.camera_number)

                    # MJPEG Enable - for Service Run.  Ensures MJPEG URLs are Successful  MAYBE MOVE THIS LATER SOMEWHERE??? 
                    if settings.getSetting_int('stream', self.camera_number) == 1 or \
                       settings.getSetting_int('allstream', self.camera_number) != 1 or \
                       settings.getSetting_int('preview_stream', self.camera_number) != 1:
                        self.enable_mjpeg()

                else:
                    # Set result for Generic IP Camera
                    monitor.write_testResult(self.camera_number, 0)

                return True
        return False

    @property
    def number(self): 
        return self.camera_number

    @property
    def _type(self): 
        return self.camera_type
    
    @property
    def url(self): 
        return self.camera.url

    @property
    def video_url(self): 
	return self.camera.video_url

    @property
    def mjpeg_url(self): 
	return self.camera.mjpeg_url

    @property
    def snapshot_url(self):
	return self.camera.snapshot_url

    @property
    def ptz_sensitivity(self):
        return self.ptz_get_sensitivity()

    # *********************** SETTING COMMANDS ***********************

    def ptz_get_sensitivity(self):
        if self.camera_type == FOSCAM_HD or self.camera_type == FOSCAM_HD_OVERRIDE:
            return settings.getSetting_float('ptz_hd_sensitivity%s' %self.camera_number) / 10
        elif self.camera_type == FOSCAM_SD:
            return self.camera.ptz_set_sensitivity(settings.getSetting('ptz_sd_sensitivity%s' %self.camera_number))

    def getUrl(self, source, stream_type):
        '''
            Source                     Stream_type:
             0 Video Stream:            0 Video;  1 Mjpeg    
             1 All Camera Player:       0 Mjpeg;  1 Snapshot;  2 Mjpeg
             2 Preview:                 0 Mjpeg;  1 Snapshot;  2 Mjpeg
        '''
        
        if (source != SINGLE_CAMERA_PLAYER and stream_type != 1) or (source == SINGLE_CAMERA_PLAYER and stream_type == 1):
            return self.camera.mjpeg_url   
        elif (source == SINGLE_CAMERA_PLAYER and stream_type == 0):
            return self.camera.video_url   
        else:
            return self.camera.snapshot_url
    
    def getStreamType(self, source):
        '''
        Source:   0 Video Stream;  1 All Camera Player;  2 Preview
        '''
        
        if source == SINGLE_CAMERA_PLAYER:
            return settings.getSetting_int('stream', self.camera_number)        
        elif source == ALL_CAMERA_PLAYER:
            return settings.getSetting_int('allstream', self.camera_number)
        elif source == PREVIEW_WINDOW:
            return settings.getSetting_int('preview_stream', self.camera_number)
    
    def getStreamUrl(self, source, stream_type = None):
        '''
        Source:   0 Video Stream;  1 All Camera Player;  2 Preview
        '''
        if not stream_type:
            stream_type = self.getStreamType(source)
            
        return self.getUrl(source, stream_type)

    def getSnapShotUrl(self):
        return self.getStreamUrl(1, 1)

    def resetLocation(self):
        if settings.getSetting_int('ptz', self.camera_number) > 0:
            reset_mode = settings.getSetting_int('conn', self.camera_number)
            if reset_mode > 0:
                if reset_mode == 2:
                    reset_mode = 3
                self.camera.ptz_home_location(reset_mode)
                utils.log(2, 'SETTINGS :: Reset Camera %s to the home location' %self.camera_number)

    def getTriggerInterval(self, motion_enabled, sound_enabled):
        """ Gets the alarm trigger interval from the camera """
        trigger_interval = settings.getSetting_int('interval', self.camera_number)

        if self.camera_type != FOSCAM_SD and \
           self.camera_type != GENERIC_IPCAM:
            motion_trigger_interval = int(self.camera.get_motion_detect_config()[1]['triggerInterval'])
            sound_trigger_interval = int(self.camera.get_sound_detect_config()[1]['triggerInterval'])
        
            if motion_enabled and sound_enabled:    trigger_interval = min(motion_trigger_interval, sound_trigger_interval)    
            elif motion_enabled:                    trigger_interval = motion_trigger_interval  
            elif sound_enabled:                     trigger_interval = sound_trigger_interval
            
        return trigger_interval


    # *********************** PASSTHROUGH COMMANDS ***********************
    def get_dev_state(self): 
        return self.camera.get_dev_state()

    def is_alarm_active(self, motion_enabled, sound_enabled):
        return self.camera.is_alarm_active(motion_enabled, sound_enabled)


    # *************** AV Functions ******************
    def enable_mjpeg(self):
        if self.camera_type != FOSCAM_SD and \
           self.camera_type != GENERIC_IPCAM:
            return self.camera.enable_mjpeg()
        return None
            
    def disable_mjpeg(self):
        if self.camera_type != FOSCAM_SD and \
           self.camera_type != GENERIC_IPCAM:
            return self.camera.disable_mjpeg()
        return None
        
    def set_snapshot_config(self, quality, callback = None):
	return self.camera.set_snapshot_config(quality)
		
    def get_snapshot_config(self, callback = None):
	return self.camera.get_snapshot_config()

    def set_ir_on(self, callback=None):
	return self.camera.set_ir_on()

    def set_ir_off(self, callback=None):
	return self.camera.set_ir_off()

    def get_ir_config(self, callback=None):
	return self.camera.get_ir_config()

    def set_ir_config(self, mode, callback=None):
	return self.camera.set_ir_config(mode)

    def mirror_video(self, is_mirror = None, callback = None):
        return self.camera.mirror_video(is_mirror)

    def flip_video(self, is_flip = None, callback = None):
        return self.camera.flip_video(is_flip)

    def get_mirror_and_flip_setting(self, callback = None):
        return self.camera.get_mirror_and_flip_setting()


        
    # *************** Device Managing Functions *******************
    def get_dev_name(self, callback = None):
        return self.camera.get_dev_name()

    def set_dev_name(self, devname, callback = None):
        return self.camera.set_dev_name(devname)

    def set_pwr_freq(self, mode, callback = None):
        return self.camera.set_pwr_freq(mode)

    def get_osd_setting(self, callback = None):
        return self.camera.get_osd_setting()
    
    def reboot(self, callback = None): 
        return self.camera.reboot()

    # *************** PTZ Control Functions *******************
    def ptz_move_up(self, callback = None):
        return self.camera.ptz_move_up()

    def ptz_move_down(self, callback = None):
        return self.camera.ptz_move_down()

    def ptz_move_left(self, callback = None):
        return self.camera.ptz_move_left()

    def ptz_move_right(self, callback = None):
        return self.camera.ptz_move_right()

    def ptz_move_top_left(self, callback = None):
        return self.camera.ptz_move_top_left()

    def ptz_move_top_right(self, callback = None):
        return self.camera.ptz_move_top_right()

    def ptz_move_bottom_left(self, callback = None):
        return self.camera.ptz_move_bottom_left()

    def ptz_move_bottom_right(self, callback = None):
        return self.camera.ptz_move_bottom_right()

    def ptz_stop_run(self, callback = None):
        return self.camera.ptz_stop_run()

    def ptz_reset(self, callback = None):
        return self.camera.ptz_reset()

    def ptz_home_location(self, mode, callback = None):
        return self.camera.ptz_home_location(mode)
                    
    def ptz_get_preset(self, callback = None):
        return self.camera.ptz_get_preset()
    
    def ptz_goto_preset(self, name, callback = None):
        return self.camera.ptz_goto_preset(name)

    def ptz_add_preset(self, name = None, callback = None):
        return self.camera.ptz_add_preset(name)

    def ptz_delete_preset(self, name = None, callback = None):
        return self.camera.ptz_delete_preset(name)

    def get_ptz_speed(self, callback = None):
        return self.camera.get_ptz_speed()

    def set_ptz_speed(self, speed, callback = None):
        return self.camera.set_ptz_speed(speed)

    def get_ptz_selftestmode(self, callback = None):
        return self.camera.get_ptz_selfttestmode()

    def set_ptz_selftestmode(self, mode = 0, callback = None):
        return self.camera.set_ptz_selftestmode(mode)

    def ptz_zoom_in(self, callback = None):
        return self.camera.ptz_zoom_in()

    def ptz_zoom_out(self, callback = None):
        return self.camera.ptz_zoom_out()

    def ptz_zoom_stop(self, callback = None):
        return self.camera.ptz_zoom_stop()

    def get_ptz_zoom_speed(self, callback = None):
        return self.camera.get_ptz_zoom_speed()

    def set_ptz_zoom_speed(self, speed, callback = None):
        return self.camera.set_ptz_zoom_speed(speed)


    # *************** Sound Alarm Functions *******************
    def get_sound_detect_config(self, callback = None):
	return self.camera.get_sound_detect_config()

    def enable_sound_detection(self):
        return self.camera.enable_sound_detection()

    def disable_sound_detection(self):
        return self.camera.disable_sound_detection()

    def get_sound_sensitivity(self):
        return self.camera.get_sound_sensitivity()
    
    def set_sound_sensitivity(self, level):
        return self.camera.set_sound_sensitivity(level)

    def get_sound_triggerinterval(self):
        return self.camera.get_sound_trigger_interval()
    
    def set_sound_triggerinterval(self, interval):
        return self.camera.set_sound_triggerinterval(interval)

    # *************** Motion Alarm Functions *******************
    def get_motion_detect_config(self, callback = None):
        return self.camera.get_motion_detect_config()

    def enable_motion_detection(self):
        return self.camera.enable_motion_detection()

    def disable_motion_detection(self):
        return self.camera.disable_motion_detection()

    def get_motion_sensitivity(self):
        return self.camera.get_motion_sensitivity()
    
    def set_motion_sensitivity(self, level):
        return self.camera.set_motion_sensitivity(level)

    def get_motion_triggerinterval(self):
        return self.camera.get_motion_triggerinterval()
    
    def set_motion_triggerinterval(self, interval):
        return self.camera.set_motion_triggerinterval(interval)

    

   
