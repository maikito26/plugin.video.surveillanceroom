"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

"""

import utils, settings

class GenericIPCam(object):
    '''A python implementation of a Generic IP Camera'''

    def __init__(self, camera_settings, daemon = False, verbose = True):
        '''
        If ``daemon`` is True, the command will be sent unblockedly.
        '''
        self.daemon = daemon
        self.verbose = verbose
        self.camera_number = camera_settings[0]
        #self.host = camera_settings[1]
        #self.port = camera_settings[2]
        #self.usr = camera_settings[3]
        #self.pwd = camera_settings[4]

    @property
    def video_url(self):
        _videoUrl = settings.getSetting('stream_url', self.camera_number)
        return _videoUrl

    @property
    def mjpeg_url(self):
        _mjpegUrl = settings.getSetting('mjpeg_url', self.camera_number)
        return _mjpegUrl

    @property
    def snapshot_url(self):
        _snapshotUrl = settings.getSetting('snapshot_url', self.camera_number)
        return _snapshotUrl

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):		
	return None

