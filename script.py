'''
Script for external access
'''   

import xbmc, xbmcaddon, sys
from resources.lib import allcameraplayer

__addon__ = xbmcaddon.Addon('plugin.video.foscam4kodi')
__addonid__ = __addon__.getAddonInfo('id')

    
#Main Code
if __name__ == "__main__":

    try:    
        args = sys.argv[2]
        mode = args[0]
        print 'mode received: ' + str(mode)
    except:
        mode = '0'


    
    #All Cameras Player 
    if mode == '0':
        #xbmc.executebuiltin('RunScript(%s)'%(xbmc.translatePath(('special://home/addons/{0}/allcameraplayer.py').format(__addonid__)).decode('utf-8')))
        allcameraplayer.main()

    
    #Single Cameras Player   
    else:
        pass
        #xbmc.executebuiltin('RunScript(%s,%s)'%(xbmc.translatePath(('special://home/addons/{0}/cameraplayer_new.py').format(__addonid__)).decode('utf-8'), mode))
        
