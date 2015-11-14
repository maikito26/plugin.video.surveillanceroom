"""
plugin.video.surveillanceroom
A Kodi Add-on by Maikito26

Main Menu and External Functionality
"""

import sys, os, urllib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
from resources.lib import settings, monitor, allcameraplayer, cameraplayer, camerasettings, utils, previewgui
from resources.lib.ipcam_api_wrapper import CameraAPIWrapper as Camera

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


def addDirectoryItem(name, url = None, isFolder = False, icon = None, fanart = None, li = None, parameters = {}):
    """
    Function which adds the directory line item into the Kodi navigation menu
    """

    if li == None:
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
    
    for camera_number in "123456":
        
        if settings.enabled_camera(camera_number):
            
            list_label = settings.getCameraName(camera_number)
            
            # List submenus for each enabled camera
            addDirectoryItem(name =  list_label + ' ' + utils.translation(32029),
                             isFolder = True,
                             icon = utils.get_icon(camera_number),
                             fanart = utils.get_fanart(camera_number),
                             parameters = {'action': 'advanced_camera',
                                           'camera_number': camera_number})
    

    # Toggle Preview Ability to be activated by alarms
    addDirectoryItem(name = utils.translation(32217),
                     icon = utils.get_icon('settings'), 
                     fanart = utils.get_fanart('default'),
                     parameters = {'action': 'toggle_preview'})

    # Add-on Settings  
    addDirectoryItem(name = utils.translation(32028),
                     icon = utils.get_icon('settings'), 
                     fanart = utils.get_fanart('default'),
                     parameters = {'action': 'settings'})

    # Restart the preview service
    addDirectoryItem(name = 'Restart Preview Service',
                     icon = utils.get_icon('settings'), 
                     fanart = utils.get_fanart('default'),
                     parameters = {'action': 'restart_service'})
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    


def main_menu():                                                
    """ First Level Menu to access main functions """

    if settings.atLeastOneCamera():

        # All Camera Player
        addDirectoryItem(name = utils.translation(32027),
                         icon = utils.get_icon('default'),
                         fanart = utils.get_fanart('default'),
                         parameters = {'action': 'all_cameras'})

        for camera_number in "123456":
            
            if settings.enabled_camera(camera_number):
                
                camera = Camera(camera_number)
                list_label = settings.getCameraName(camera_number)

                # Build Context Menu
                li = li = xbmcgui.ListItem(list_label)
                context_items = []

                if settings.getSetting('enabled_preview', camera_number) == 'true':
                    #Show Preview
                    context_items.append((utils.translation(32210), 'RunPlugin(plugin://plugin.video.surveillanceroom?action=show_preview&camera_number=%s)' %camera_number))

                    #Disable Preview
                    context_items.append((utils.translation(32212), 'RunPlugin(plugin://plugin.video.surveillanceroom?action=disable_preview&camera_number=%s)' %camera_number))
                else:
                    #Enable Preview
                    context_items.append((utils.translation(32211), 'RunPlugin(plugin://plugin.video.surveillanceroom?action=enable_preview&camera_number=%s)' %camera_number))
                
                camera_type = settings.getCameraType(camera_number)
                if camera_type < 3:
                    #Play Stream no Controls
                    context_items.append((utils.translation(32214), 'RunPlugin(plugin://plugin.video.surveillanceroom?action=single_camera_no_controls&camera_number=%s)' %camera_number))

                    #Camera Settings
                    context_items.append((utils.translation(32215), 'RunPlugin(plugin://plugin.video.surveillanceroom?action=camera_settings&camera_number=%s)' %camera_number))

                # Update Fanart
                if settings.getSetting_int('fanart') == 1:
                    context_items.append((utils.translation(32213), 'RunPlugin(plugin://plugin.video.surveillanceroom?action=update_fanart&camera_number=%s)' %camera_number))
                    
                li.addContextMenuItems(context_items, replaceItems=True)

                # Fanart URL
                new_art_url = None
                if camera.Connected(monitor):
                    new_art_url = camera.getSnapShotUrl()
                else:
                    if camera.Connected(monitor, False):
                        new_art_url = camera.getSnapShotUrl()
                
                # Single Camera Player for enabled cameras
                addDirectoryItem(name = list_label, 
                                 icon = utils.get_icon(camera_number),
                                 fanart = utils.get_fanart(camera_number, new_art_url),
                                 li = li, 
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
    monitor = monitor.AddonMonitor()
    utils.log(2, 'Handle: %s;  Params: %s;  action: %s' %(handle, params, action))

    
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
        cameraplayer.play(camera_number, monitor)
        

    # Single Camera Stream without Controls   
    elif action == 'single_camera_no_controls':
        cameraplayer.play(camera_number, monitor, False)


    # Reboot Camera  
    elif action == 'reboot':
        with Camera(camera_number) as camera:
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
            if settings.getSetting_int('cond_manual_toggle', camera_number) == 1 and monitor.previewOpened(camera_number):
                monitor.closeRequest(camera_number)
            else:
                monitor.openRequest_manual(camera_number)                
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
        monitor.togglePreview()

    
    # Update Fanart
    elif action == 'update_fanart':
        camera = Camera(camera_number)
        if camera.Connected(monitor, False):
            utils.get_fanart(camera_number, camera.getSnapShotUrl(), update = True)
            xbmc.executebuiltin('Container.Refresh')
            
        else:
            utils.notify(utils.translation(32222))


    # Restart Preview Service
    elif action == 'restart_service':
        monitor.stop()


    # Preliminary attempt to show an overlay based on a URL, not fully tested and does not close on its own yet
    elif action == 'show_preview_custom':
        url = params.get('url', '')
        if url != '':
            monitor.overrideURL(camera_number, url)
            monitor.openRequest_manual(camera_number)
        monitor.waitForAbort(2)
        monitor.clear_overrideURL(camera_number)
        
        
