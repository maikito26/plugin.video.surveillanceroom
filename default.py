"""
plugin.video.surveillanceroom
A Kodi Add-on by Maikito26

Main Menu and External Functionality
"""

import sys, os, urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
from resources.lib import settings, monitor, allcameraplayer, cameraplayer, camerasettings, foscam2
from resources.lib import utils

__addon__ = xbmcaddon.Addon() 
__addonid__ = __addon__.getAddonInfo('id') 
_path = xbmc.translatePath(('special://home/addons/{0}').format(__addonid__)).decode('utf-8')                 


def param_to_dict(parameters):
    """
    Convert parameters encoded in a URL to a dict
    """
    
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addDirectoryItem(name, url = None, isFolder = False, icon = None, fanart = None, parameters = {}):
    """
    Function which adds the directory line item into the Kodi navigation menu
    """
    
    li = xbmcgui.ListItem(name)
    
    if icon != None:
        li.setIconImage(icon)
        li.setArt({'thumb': icon,
                   'poster': icon})
        
    if fanart != None:
        li.setArt({'fanart': fanart,
                   'landscape': fanart})
        
    li.setInfo(type = 'Video',
               infoLabels = {'Title': name}) 

    if url == None:
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    
    return xbmcplugin.addDirectoryItem(handle = handle,
                                       url = url,
                                       listitem = li,
                                       isFolder = isFolder)





def advanced_camera_menu(camera_number):                                                
    """ Third Level Advanced Menu for additional IP Camera Functions """
    
    #EXTENDED MENU IDEAS
    #FPS Test
    #Force Show preview mjpeg / snapshot
    #Show snapshot

    if settings.getSetting('enabled_preview', camera_number) == 'true':
        
        #Show Preview
        addDirectoryItem(name = utils.translation(32210),
                     icon = utils.get_icon('settings'),
                     fanart = utils.get_fanart(camera_number),
                     parameters = {'action': 'show_preview',
                                   'camera_number': camera_number})
        
        #Disable Preview
        addDirectoryItem(name = utils.translation(32212),
                         icon = utils.get_icon('settings'),
                         fanart = utils.get_fanart(camera_number),
                         parameters = {'action': 'disable_preview',
                                       'camera_number': camera_number})

    else:
        
        #Enable Preview
        addDirectoryItem(name = utils.translation(32211),
                         icon = utils.get_icon('settings'),
                         fanart = utils.get_fanart(camera_number),
                         parameters = {'action': 'enable_preview',
                                       'camera_number': camera_number})

    if settings.getSetting_int('fanart') == 1:
        
        #Update Fanart
        addDirectoryItem(name = utils.translation(32213),
                         icon = utils.get_icon('settings'),
                         fanart = utils.get_fanart(camera_number),
                         parameters = {'action': 'update_fanart',
                                       'camera_number': camera_number})
    
    camera_type = settings.getCameraType(camera_number)
    
    if camera_type < 3:

        #Play Stream no Controls
        addDirectoryItem(name = utils.translation(32214),
                         icon = utils.get_icon('settings'),
                         fanart = utils.get_fanart(camera_number),
                         parameters = {'action': 'single_camera_no_controls',
                                       'camera_number': camera_number})
        
        
        #Camera Settings
        addDirectoryItem(name = utils.translation(32215),
                         icon = utils.get_icon('settings'),
                         fanart = utils.get_fanart(camera_number),
                         parameters = {'action': 'camera_settings',
                                       'camera_number': camera_number})

        #Reboot Camera
        addDirectoryItem(name = utils.translation(32216),
                         icon = utils.get_icon('settings'),
                         fanart = utils.get_fanart(camera_number),
                         parameters = {'action': 'reboot',
                                       'camera_number': camera_number})


    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

    

def advanced_menu():                                                
    """ Second Level Menu which provides advanced options """

    # Toggle Preview Ability to be activated by alarms
    addDirectoryItem(name = utils.translation(32217),
                     icon = utils.get_icon('settings'), 
                     fanart = utils.get_fanart('default'),
                     parameters = {'action': 'toggle_preview'})
    
    for camera_number in "1234":
        
        if settings.enabled_camera(camera_number):
            
            camera_settings = settings.getBasicSettings(camera_number)
            list_label = settings.getCameraName(camera_number)
            
            # List submenus for each enabled camera
            addDirectoryItem(name =  list_label + ' ' + utils.translation(32029),
                             isFolder = True,
                             icon = utils.get_icon(camera_number),
                             fanart = utils.get_fanart(camera_number),
                             parameters = {'action': 'advanced_camera',
                                           'camera_number': camera_number})
    '''
    # Restart the preview service
    addDirectoryItem(name = 'Restart Preview Service',
                     icon = utils.get_icon('settings'), 
                     fanart = utils.get_fanart('default'),
                     parameters = {'action': 'restart_service'})
    '''

    # Add-on Settings  
    addDirectoryItem(name = utils.translation(32028),
                     icon = utils.get_icon('settings'), 
                     fanart = utils.get_fanart('default'),
                     parameters = {'action': 'settings'})
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    


def main_menu():                                                
    """ First Level Menu to access main functions """

    if settings.atLeastOneCamera():

        # All Camera Player
        addDirectoryItem(name = utils.translation(32027),
                         icon = utils.get_icon('default'),
                         fanart = utils.get_fanart('default'),
                         parameters = {'action': 'all_cameras'})

        for camera_number in "1234":
            
            if settings.enabled_camera(camera_number):
                
                camera_settings = settings.getBasicSettings(camera_number)
                list_label = settings.getCameraName(camera_number)

                new_art_url = None
                if camera_settings:
                    new_art_url = settings.getNewArt(camera_number)
                    utils.log(4, 'Get New Fanart Enabled: %s' %new_art_url)

                # Single Camera Player for enabled cameras
                addDirectoryItem(name = list_label,
                                 icon = utils.get_icon(camera_number),
                                 fanart = utils.get_fanart(camera_number, new_art_url),
                                 parameters = {'action': 'single_camera',
                                               'camera_number': camera_number})

        # Link to Second Level Advanced Menu
        addDirectoryItem(name = utils.translation(32029),
                         isFolder = True,
                         icon = utils.get_icon('advanced'), 
                         fanart = utils.get_fanart('default'),
                         parameters={'action': 'advanced'})

    else:

        # Add-on Settings if no cameras are configured
        addDirectoryItem(name = utils.translation(32028),
                     icon = utils.get_icon('settings'), 
                     fanart = utils.get_fanart('default'),
                     parameters = {'action': 'settings'})

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    utils.cleanup_images()     


if __name__ == "__main__":
    
    handle = int(sys.argv[1])
    params = param_to_dict(sys.argv[2])
    action = params.get('action', ' ')
    camera_number = params.get('camera_number', '')
    utils.log(4, 'Handle: %s;  Params: %s;  action: %s' %(handle, params, action))

    
    # Main Menu
    if action == ' ':
        main_menu()


    # Settings
    elif action == 'settings':
        __addon__.openSettings()
        xbmc.executebuiltin('Container.Refresh')


    # Advanced Menu
    elif action == 'advanced':
        advanced_menu()


    # Advanced Camera Menu
    elif action == 'advanced_camera':
        advanced_camera_menu(camera_number)
        

    # All Cameras Player   
    elif action == 'all_cameras':
        allcameraplayer.play()
    

    # Single Camera Stream   
    elif action == 'single_camera': 
        monitor = monitor.AddonMonitor()
        cameraplayer.play(camera_number, monitor)
        

    # Single Camera Stream without Controls   
    elif action == 'single_camera_no_controls': 
        monitor = monitor.AddonMonitor()
        cameraplayer.play(camera_number, monitor, 3)


    # Reboot Camera  
    elif action == 'reboot':
        with foscam2.FoscamCamera(settings.getBasicSettings(camera_number)) as camera:
            response = camera.reboot()
            if response[0] == 0:
                utils.dialog_ok(utils.translation(32218))
            else:
                utils.dialog_ok(utils.translation(32219))


    # Camera settings 
    elif action == 'camera_settings':
        window = camerasettings.CameraSettingsWindow(camera_number)
        window.doModal()
        del window
        utils.dialog_ok(utils.translation(32220))


    # Show Preview 
    elif action == 'show_preview':
        if settings.enabled_preview(camera_number):
            monitor = monitor.AddonMonitor()
            monitor.set_script(camera_number)
        else:
            utils.notify(utils.translation(32228))


    # Disable Preview 
    elif action == 'disable_preview':
        settings.setSetting('enabled_preview', camera_number, 'false')
        xbmc.executebuiltin('Container.Refresh')

        
    # Enable Preview 
    elif action == 'enable_preview':
        settings.setSetting('enabled_preview', camera_number, 'true')
        xbmc.executebuiltin('Container.Refresh')


    # Toggle All Preview
    elif action == 'toggle_preview':
        monitor = monitor.AddonMonitor()
        monitor.toggle_preview()

    
    # Update Fanart
    elif action == 'update_fanart':
        new_art_url = settings.getNewArt(camera_number, 0)
        print camera_number
        print new_art_url
        utils.get_fanart(camera_number, new_art_url)
        utils.notify(utils.translation(32221))
        xbmc.executebuiltin('Container.Refresh')


    # Restart Preview Service
    elif action == 'restart_service':
        pass
