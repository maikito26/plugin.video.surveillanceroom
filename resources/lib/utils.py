"""
plugin.video.surveillanceroom

A Kodi add-on by Maikito26

Supporting functions that have no dependencies from the main add-on
"""

import xbmc, xbmcaddon, xbmcvfs, xbmcgui
import os, urllib, requests, sys
import sqlite3 as lite
import socket


__addon__ = xbmcaddon.Addon() 
__addonid__ = __addon__.getAddonInfo('id')
__version__ = __addon__.getAddonInfo('version')
__icon__  = __addon__.getAddonInfo('icon').decode("utf-8")
__path__ = xbmc.translatePath(('special://home/addons/{0}').format(__addonid__)).decode('utf-8')  
__data_path__ = xbmc.translatePath('special://profile/addon_data/%s' %__addonid__ ).decode('utf-8')
__log_level__ = int(__addon__.getSetting('log_level'))
__log_info__ = __addonid__ + ' v' + __version__ + ': '
TIMEOUT = int(__addon__.getSetting('request_timeout'))
socket.setdefaulttimeout(TIMEOUT)

_atleast_python27 = False
if '2.7.' in sys.version:
    _atleast_python27 = True

# Makes sure folder path exists
if not xbmcvfs.exists(__data_path__):
    try:
        xbmcvfs.mkdir(__data_path__)
    except:
        pass

def translation(id): 
    return __addon__.getLocalizedString(id)

def dialog_ok(msg):
    addon_name = translation(32000)
    xbmcgui.Dialog().ok(addon_name, msg)

def notify(msg):        
    if 'true' in __addon__.getSetting('notifications'):
        addon_name = translation(32000)
        xbmcgui.Dialog().notification(addon_name, msg, icon = __icon__) 

def log(level=4, value=''):
    msg = str(value)
    if level == 3:                              #Error
        xbmc.log(__log_info__ + 'ERROR   : ' + msg, xbmc.LOGERROR)

    elif __log_level__ > 0 and level == 1: #Normal
        xbmc.log(__log_info__ + 'NORMAL  : ' + msg, xbmc.LOGNOTICE)

    elif __log_level__ > 1 and level == 2:                  #Verbose
        xbmc.log(__log_info__ + 'VERBOSE : ' + msg, xbmc.LOGNOTICE)
        
    elif __log_level__ > 2 and level == 4:                            #DEBUG
        xbmc.log(__log_info__ + 'DEBUG   : ' + msg, xbmc.LOGNOTICE)
  
def cleanup_images():
    """ Final Cleanup of images when Kodi shuts down """
    
    for i in xbmcvfs.listdir(__data_path__)[1]:
        if (i <> 'settings.xml') and (not 'fanart_camera' in i):
            xbmcvfs.delete(os.path.join(__data_path__, i))
            log(4, 'CLEANUP IMAGES :: %s' %i)

def remove_leftover_images(filename_prefix):
    """ Attempts to remove leftover images after player stops """

    for i in xbmcvfs.listdir(__data_path__)[1]:
        if filename_prefix in i:
            xbmcvfs.delete(os.path.join(__data_path__, i))
            log(4, 'CLEANUP IMAGES :: %s' %i)
            
            
def remove_cached_art(art):
    """ Removes cached art from textures database and cached folder """
    
    _db_path = xbmc.translatePath('special://home/userdata/Database').decode('utf-8')
    _tbn_path = xbmc.translatePath('special://home/userdata/Thumbnails').decode('utf-8')
    db = None
    
    try:         
        db = lite.connect(os.path.join(_db_path, 'Textures13.db'))
        db = db.cursor()

        #Get cached image name to remove                  
        db.execute("SELECT cachedurl FROM texture WHERE url = '%s';" %art)
        data = db.fetchone()
        
        try:
            
            log(4, 'Removing Cached Art :: SQL Output: %s' %data[0])
            file_to_delete = os.path.join(_tbn_path, data[0])
            log(4, 'Removing Cached Art :: File to be removed: %s' %file_to_delete)

            xbmcvfs.delete(file_to_delete)
            db.execute("DELETE FROM texture WHERE url = '%s';" %art)

        except:
            pass
        
    except lite.Error, e:
        log(3, "Error %s:" %e.args[0])
        #sys.exit(1)
        
    finally:
        if db:
            db.close()
            
    try:
        log(4, 'Removing Original Artwork if Exists :: File to be removed: %s' %art)
        xbmcvfs.delete(art)
        
    except:
        pass

def get_icon(name_or_number):
    """ Determines which icon to display """
    
    if name_or_number == 'default':
        icon = os.path.join(__path__, 'icon.png')
        
    elif name_or_number == 'settings':
        icon = os.path.join(__path__, 'resources', 'media', 'icon-settings.png')
        
    elif name_or_number == 'advanced':
        icon = os.path.join(__path__, 'resources', 'media', 'icon-advanced-menu.png')
        
    else:
        camera_type = int(__addon__.getSetting('type%s' %name_or_number))
        ptz = int(__addon__.getSetting('ptz%s' %name_or_number))
        
        if camera_type < 3 and ptz > 0:
            icon = os.path.join(__path__, 'resources', 'media', 'icon-foscam-hd-ptz.png')
            
        elif camera_type < 3:
            icon = os.path.join(__path__, 'resources', 'media', 'icon-foscam-hd.png')
            
        else:
            icon = os.path.join(__path__, 'resources', 'media', 'icon-generic.png')

    return icon

def get_fanart(name_or_number, new_art_url = None):
    """ Determines which fanart to show """
    
    if str(name_or_number) == 'default':
        fanart = os.path.join(__path__, 'fanart.jpg')
        
    else:
        fanart = os.path.join(__data_path__,'fanart_camera' + str(name_or_number) + '.jpg')

        if new_art_url:
            remove_cached_art(fanart)

        if not xbmcvfs.exists(fanart):            
            try:
                log(4, 'Retrieving new Fanart for camera %s : %s' %(name_or_number, new_art_url))
                urllib.urlretrieve(new_art_url, fanart)
            except:
                log(4, 'Failed to Retrieve Snapshot from camera %s.' %name_or_number)
                fanart = os.path.join(__path__, 'fanart.jpg')

    return fanart

def get_mjpeg_frame(stream, filename):
    """ Extracts JPEG image from MJPEG """
   
    line  = ''
    try:
        while not 'length' in line.lower():
            if '500 - Internal Server Error' in line:
                return False
            #log(4, 'GETMJPEGFRAME: %s' %line)
            line = stream.readline()

        bytes = int(line.split(':')[-1])
        
        while len(line) > 3:
            line = stream.readline()
            
        frame = stream.read(bytes)
   
    except requests.RequestException as e:
        log(3, str(e))
        return False

    if frame:
        with open(filename, 'wb') as jpeg_file:
            jpeg_file.write(frame)

    return True





