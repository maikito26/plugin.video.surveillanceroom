'''
Text Here
'''


import sys, os, urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from resources.lib import monitor, allcameraplayer
from resources.lib.settings import getSettings, translation
from resources.lib.cameraplayer import playCameraVideo

__addon__ = xbmcaddon.Addon() 
__addonid__ = __addon__.getAddonInfo('id') 
__path__ = xbmc.translatePath(('special://home/addons/{0}').format(__addonid__)).decode('utf-8')                 
    

atLeastOneCamera, cameras = getSettings(settings_to_get = 'features') 

def param_to_dict(parameters):
    '''
    Convert parameters encoded in a URL to a dict
    '''
    
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict




def addDirectoryItem(name, url = None, isFolder = False, parameters = {}):
    '''
    Add Text Later
    '''
    
    li = xbmcgui.ListItem(name) #, iconImage="DefaultTVShows.png", thumbnailImage=iconimage)  --> To be added later
    li.setInfo(type="Video", infoLabels={"Title": name}) 
    #li.setProperty("fanart_image", defaultFanart)      --> To be added later

    if url == None:
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=isFolder)



def advanced_camera_menu(camera_number):                                                
    '''
           [
           0:  [0]camera_number
           
           1:  [1]host  [2]port  [3]username  [4]password  [5]name  [6]snapshot  [7]rtsp  
               [8]mpjeg  [9]cameratype  [10]cameraplayer_source  [11]allcameraplayer_source
               
           2:  [12]pan_tilt  [13]zoom  [14]motionsupport  [15]soundsupport
           
           3:  [16]preview_enabled  [17]duration  [18]location  [19]scaling  [20]motion_enabled
                   [21]sound_enabled  [22]check_interval  [23]preview_source  [24]trigger_interval
           ]

    '''
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    camera = cameras[ int(camera_number) - 1 ]

    if camera[6] != '':
        addDirectoryItem(translation(32036), url = camera[6])
    
    if camera[7] != '':
        addDirectoryItem(translation(32037), url = camera[7])

    if camera[8] != '':
        addDirectoryItem(translation(32038), url = camera[8])

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)


def advanced_menu():                                                
    '''
    Add Text Later
    '''

    for camera in cameras:
        
        list_label = camera[5]
        if list_label == '':
            list_label = translation(32000 + int(camera[0]))
            
        addDirectoryItem(translation(32012) + ' - ' + list_label, isFolder = True, parameters={ 'mode': 'advanced_camera', 'camera_number': camera[0] } )
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
   

def main_menu():                                                
    '''
    Add Text Later
    '''

    if atLeastOneCamera:
        addDirectoryItem(translation(32007), parameters={ 'mode': 'all_cameras' } )

        for camera in cameras:
            
            list_label = camera[5]
            if list_label == '':
                list_label = translation(32000 + int(camera[0]))
                
            addDirectoryItem(list_label, parameters={ 'mode': camera[0] } )

    #addDirectoryItem(translation(32012), isFolder = True, parameters={ 'mode': 'advanced' } )
    addDirectoryItem(translation(32011), parameters={ 'mode': 'settings' } )
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    

    



if __name__ == "__main__":
        
    handle = int(sys.argv[1])
    params = param_to_dict(sys.argv[2])
    mode = params.get('mode', ' ')


    # Main Menu
    if mode == ' ':
        main_menu()


    # Settings
    elif mode == 'settings':
        __addon__.openSettings()
        xbmc.executebuiltin('Container.Refresh')


    # Advanced Menu
    elif mode == 'advanced':
        advanced_menu()


    # Advanced Camera Menu
    elif mode == 'advanced_camera':
        camera_number = params.get('camera_number', '')
        advanced_camera_menu(camera_number)
        

    # All Cameras Player   
    elif mode == 'all_cameras':
        #xbmc.executebuiltin('RunScript(plugin.video.mycam, 0)')     #External Access Link
        allcameraplayer.Main()
    

    # Single Camera Stream   
    else: 
        monitor = monitor.AddonMonitor()
        playCameraVideo(mode, monitor)

