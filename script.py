'''
Script for external access

xbmc.executebuiltin()
    RunScript(plugin.video.foscam4kodi,fullscreen,0)
    RunScript(plugin.video.foscam4kodi,preview,2)

    #xbmc.executebuiltin('RunScript(%s,%s)'%(xbmc.translatePath(('special://home/addons/{0}/cameraplayer_new.py').format(__addonid__)).decode('utf-8'), mode))
'''   

import xbmc, xbmcaddon, sys

__addon__ = xbmcaddon.Addon('plugin.video.foscam4kodi')
__addonid__ = __addon__.getAddonInfo('id')

    
#Main Code
if __name__ == "__main__":

    print str(sys.argv)

    try:
        calltype = sys.argv[1]
        mode = sys.argv[2]

    except:
        pass

    
    #Cameras Player 
    if calltype == 'fullscreen':
        if mode == '0':
            from resources.lib import allcameraplayer
            allcameraplayer.Main()
            
        else:
            from resources.lib import monitor
            monitor = monitor.AddonMonitor()
            
            from resources.lib import cameraplayer
            cameraplayer.playCameraVideo(mode, monitor)
    
    #Preview 
    elif calltype == 'preview':
        from resources.lib import monitor
        monitor = monitor.AddonMonitor()
        
        if mode == '0':
            pass
        else:
            monitor.script_called(mode)
    
