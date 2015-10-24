plugin.video.surveillanceroom

a Kodi add-on by Maikito26

-- Summary  --

If motion or sound is detected a small image preview will slide onto the screen. Pressing select *will* stop any playing media and open the main video feed with basic controls for pan/tilt and mirror/flip. Exit with the back button or click the close control, and the previously playing file will resume. This works for up to 4 cameras simultaneously
Also, there is a menu to select these cameras individually or all of them to play at once.


-- Features --

- Connect up to 4 IP/Foscam Cameras
- Supports credentials for Foscam, but you can overwrite the URL manually to support non-Foscam cameras, or the C model which has RTSP port hard coded to 554.
- Watch in multiple streaming formats, with camera controls displayed overtop of a single camera view.
- Preview cameras while watching content, with Motion and Sound Detection, or by calling it manually using RunScript()
- Open the camera stream from a preview, and will resume what you were watching when you close the stream.
- Logic to determine when preview is allowed to display. Configure which windows not to display for.
- Set a home location to move PTZ enabled Foscam cameras to when Kodi starts


-- Quick Start Guide --

1. Install the Kodi Add-on
2. Open the add-on settings
3. Configure the camera specific settings (additional configure preview settings if desired)
4. Enable the camera that is configured
5. Access the add-on through the Programs or Video add-on windows and view cameras


-- Calling commands from an External Source --
You can call any action available in default.py and encoding it into the URL with the parameters:
	action=
	camera_number=

Some example actions are:

1. Showing a single preview window

	XBMC.RunPlugin(plugin://plugin.video.surveillanceroom?action=show_preview&camera_number=1)  

2. Showing all cameras on fullscreen

	XBMC.RunPlugin(plugin://plugin.video.surveillanceroom?action=all_cameras)

3. Showing a single camera on fullscreen, with controls
	
	XBMC.RunPlugin(plugin://plugin.video.surveillanceroom?action=single_camera&camera_number=1)

4. Showing a single camera on fullscreen, without controls

	XBMC.RunPlugin(plugin://plugin.video.surveillanceroom?action=single_camera_no_controls&camera_number=1)
	
	
Mapping a remote button example:

	<blue>XBMC.RunPlugin(plugin://plugin.video.surveillanceroom?action=show_preview&camera_number=1)</blue>

	
	
This add-on was developed in the following environment:
- Windows 10
- Kodi 15.2
- Foscam HD Camers: F19831w & F19804p, with firmware v2.11.1.118
- D-Link DCS-932L generic IP camera


Credit and thanks to the following add-ons/developers for inspiration and a lot of the groundwork:
 * https://github.com/LS80/script.foscam (http://forum.xbmc.org/showthread.php?tid=190439)
 * https://github.com/RyanMelenaNoesis/Xbmc...ecuritycam (http://forum.xbmc.org/showthread.php?tid=182540)
 * https://github.com/Shigoru/script.securitycams (http://forum.kodi.tv/showthread.php?tid=218815)