from time import time
import urllib
import xml.etree.ElementTree as ET
import requests
import xbmc


ALARM_DURATION = 60


class CameraXMLResponse(object):
    ''' A dictionary-like container which parses the XML response to a CGI request '''

    RESULT_MSG = { 0: "Success",
                  -1: "CGI request string format error",
                  -2: "Username or password error",
                  -3: "Access denied",
                  -4: "CGI execute failure",
                  -5: "Timeout"
                  }

    def __init__(self, response):
        self._xml = response.text

        try: 
            self._xml_root = ET.fromstring(self._xml)

            result = self._xml_root.find('result')
            self._result_value = int(result.text)
            self._xml_root.remove(result)
        except:
            self._result_value = 0
            pass 

    def __nonzero__(self):
        return self._result_value == 0
    
    def __str__(self):
        return self._xml

    def __getitem__(self, key):
        return int(self._xml_root.find(key).text)

    def __iter__(self):
        return (element.tag for element in self._xml_root)

    keys = __iter__

    def items(self):
        return ((element.tag, int(element.text)) for element in self._xml_root)

    def values(self):
        return (int(element.text) for element in self._xml_root)

    @property
    def status(self):
        return self._result_value

    @property
    def message(self):
        return self.RESULT_MSG[self._result_value]


class SetConfigCommand(object):
    def __init__(self, camera, cmd):
        self.camera = camera
        self.cmd = cmd
        
        get_cmd = self.cmd.replace("set", "get")
        self._config = dict(self.camera.send_command(get_cmd).items())

    def __setitem__(self, key, value):
        self._config[key] = value

    def send(self):
        return self.camera.send_command(self.cmd, **self._config)


class Camera(object):
    def __init__(self, c):
        self.camera_number = c[0]
        host = c[1]
        port = c[2]
        username = c[3]
        password = c[4]
        self._cmdUrl = "http://{0}:{1}/cgi-bin/CGIProxy.fcgi?cmd={{0}}&usr={2}&pwd={3}".format(host, port, username, password)
        self._streamUrl = "http://{0}:{1}/cgi-bin/CGIStream.cgi?cmd={{cmd}}&usr={2}&pwd={3}&".format(host, port, username, password)
        self._videoUrl = "rtsp://{0}:{1}@{2}:{3}/videoMain".format(username, password, host, port)
        self._videoSubUrl = "rtsp://{0}:{1}@{2}:{3}/videoSub".format(username, password, host, port)

    @property
    def video_url(self):
        return self._videoUrl

    @property
    def video_sub_url(self):
        return self._videoSubUrl

    @property
    def mjpeg_url(self):
        return self._streamUrl.format(cmd='GetMJStream')

    @property
    def snapshot_url(self):
        return self._cmdUrl.format('snapPicture2')

    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return None
		
			
    def send_command(self, cmd, data=False, **params):
        url = self._cmdUrl.format(cmd)
        if params:
            url += "&" + urllib.urlencode(params)

        #common.log_verbose(url)
        try:
            response = requests.get(url, timeout=2.000) #Added timeout
        except (requests.RequestException) as e:
            xbmc.log(str(e), xbmc.LOGERROR)
            return False
        else:
            if not response:
                return False
            elif data:
                return response.content
            else:
                #common.log_verbose(response)
                xml_resp = CameraXMLResponse(response)
                #common.log_verbose(xml_resp)
                if not xml_resp:
                    xbmc.log(xml_resp.message, xbmc.LOGERROR)
                return xml_resp

    def test(self):
        response = self.send_command("getDevState")
        if response:
            msg = response.message
        else:
            msg = "Error connecting to Camera " + self.camera_number
        return bool(response), msg
    
    def move(self, direction):
        status = self.send_command("ptzMove" + direction.capitalize())
        if not status:
            return status
        xbmc.sleep(500)
        status = self.send_command("ptzStopRun")
        if not status:
            return status
        return True

    def get_mirror_and_flip(self):
        return self.send_command("getMirrorAndFlipSetting").values()

    def toggle_mirror_flip(self, action, enable):
        return self.send_command(action.lower() + "Video", {"is" + action.capitalize(): int(enable)})

    def set_ir_on(self):
        return self.send_command('openInfraLed')

    def set_ir_off(self):
        return self.send_command('closeInfraLed')

    def get_motion_detect_config(self):
        return self.send_command('getMotionDetectConfig')

    def get_sound_detect_config(self):
        return self.send_command('getAudioAlarmConfig')
    
    def get_device_state(self):
        return self.send_command('getDevState')

    def get_snapshot_config(self):
        return self.send_command('getSnapConfig')

    def set_motion_detect_config(self):
        return SetConfigCommand(self, 'setMotionDetectConfig')
    
    def set_sound_detect_config(self):
        return SetConfigCommand(self, 'setAudioAlarmConfig')
    
    def set_snapshot_config(self):
        return SetConfigCommand(self, 'setSnapConfig')
    
    def get_snapshot(self):
        return self.send_command('snapPicture2', data=True)

    def enable_mjpeg(self):
        return self.send_command('setSubStreamFormat', format=1)

    def get_mjpeg_stream(self):
        self.enable_mjpeg()
        try:
            stream = requests.get(self.mjpeg_url, stream=True).raw
            stream.readline()
            return stream
        except requests.RequestException as e:
            print str(e)
            return None
