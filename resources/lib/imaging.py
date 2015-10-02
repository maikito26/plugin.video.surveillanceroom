import xbmcvfs
import os   #, time
from urllib import urlretrieve
import foscam


def cleanup_images(f, path):  
    monitor.waitForAbort(1)
    for i in xbmcvfs.listdir(path)[1]:
        print 'CLEANUP File to delete ' + str(i) 
        if f in i:
            try:
                xbmcvfs.delete(os.path.join(path, i))
                print 'Success to delete'
            except: pass  


def ImageWorker(monitor, q, path):
    '''
    Thread worker that receives a window to update the image of continuously until that window is closed
    '''

    #error = os.path.join(path, 'error.png')
    
    while not monitor.abortRequested() and not monitor.stopped():
        
        try:
            item = q.get(block = False)
            
            if item[2]:
                frameByMjpeg(item, monitor, path)       #Approx 10fps
            else: 
                frameBySnapshot(item, monitor, path)    #Approx 2-4fps
            

            camera_number = item[0][0]
            cleanup_images('preview_%s.' %camera_number, path)

        except:
            pass

        monitor.waitForAbort(0.5)
        
    




def frameBySnapshot(item, monitor, path):
    camera_settings = item[0]
    camera_number = camera_settings[0]
    snapshotURL = camera_settings[6]
    control = item[1]
    
    #starttime = time.time()
    x = 0
    
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera_number):
    
        filename = os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x)

        try:
            urlretrieve(snapshotURL, filename)
            
            if os.path.exists(filename):
                control.img1.setImage(filename, useCache=False)
                xbmcvfs.delete(os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x - 1))
                control.img2.setImage(filename, useCache=False)
                x += 1

        except Exception, e:
            print ('Camera %s - %s' %(camera_number, str(e)))
            #control.img1.setImage(__error__, useCache=False)

    cleanup_images('preview_%s.' %camera_number, path)
    #fps = (x + 1) / (time.time() - starttime)
    #print "Preview Camera average FPS is " + str(fps) 





def get_mjpeg_frame(stream):
    content_length = ""
    try:
        while not "Length" in content_length: 
            content_length = stream.readline()
        bytes = int(content_length.split(':')[-1])
        content_length = stream.readline()
        return stream.read(bytes)
    
    except requests.RequestException as e:
        print str(e)
        return None
    

def frameByMjpeg(item, monitor, path):
    camera_settings = item[0]
    camera_number = camera_settings[0]
    control = item[1]

    camera = foscam.Camera(camera_settings)
    stream = camera.get_mjpeg_stream()
        
    #starttime = time.time()
    x = 0
    
    while not monitor.abortRequested() and not monitor.stopped() and monitor.preview_window_opened(camera_number):
        
        frame = get_mjpeg_frame(stream)

        if frame:
            filename = os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x)
            with open(filename, 'wb') as jpeg_file:
                jpeg_file.write(frame)
                
        if os.path.exists(filename):
            control.img1.setImage(filename, useCache=False)
            xbmcvfs.delete(os.path.join(path, 'preview_%s.%d.jpg') %(camera_number, x - 1))
            control.img2.setImage(filename, useCache=False)
            x += 1
            
        else:
            print ('Camera %s - %s' %(camera_number, 'Error on MJPEG'))
            #control.img1.setImage(__error__, useCache=False)

    cleanup_images('preview_%s.' %camera_number, path)
    #fps = (x + 1) / (time.time() - starttime)
    #print "Preview Camera average FPS is " + str(fps) 

        








if __name__ == "__main__":
    pass
