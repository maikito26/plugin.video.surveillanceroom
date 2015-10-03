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



def main_menu():                                                
    '''
    Add Text Later
    '''
    
    atLeastOneCamera, cameras = getSettings(settings_to_get = 'enabled') 

    if atLeastOneCamera:
        addDirectoryItem(translation(32007), parameters={ 'mode': 'all_cameras' } )

        for camera in cameras:                                  
            list_label = (32000 + int(camera[0]))
            addDirectoryItem(translation(list_label), parameters={ 'mode': camera[0] } )

    addDirectoryItem(translation(32011), parameters={ 'mode': 'settings' } )
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

    



if __name__ == "__main__":
        
    handle = int(sys.argv[1])
    params = param_to_dict(sys.argv[2])
    mode = params.get('mode', ' ')
    monitor = monitor.AddonMonitor()


    # Main Menu
    if mode == ' ':
        main_menu()


    # Settings
    elif mode == 'settings':
        __addon__.openSettings()
        xbmc.executebuiltin('Container.Refresh')


    # All Cameras Player   
    elif mode == 'all_cameras':
        #xbmc.executebuiltin('RunScript(plugin.video.mycam, 0)')     #External Access Link
        allcameraplayer.Main()
        

    # Single Camera Stream   
    else:
        settings_ok, cameras = getSettings(settings_to_get = 'features', cameras_to_get = mode)
        camera = cameras[0]
        if settings_ok:
            playCameraVideo(camera, monitor)

