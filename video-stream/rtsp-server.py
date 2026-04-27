import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib

Gst.init(None)

server = GstRtspServer.RTSPServer()
server.set_service("8554")

mounts = server.get_mount_points()

factory = GstRtspServer.RTSPMediaFactory()
#    libcamerasrc ae-enable=false exposure-time=66000 analogue-gain=18.0  !
factory.set_launch("""
    libcamerasrc exposure-time-mode=1 exposure-time=40000 analogue-gain-mode=1 analogue-gain=15.0
    awb-mode=1 !
    video/x-raw,width=960,height=720,framerate=15/1,format=NV12,interlace-mode=progressive !
    queue !
    videoconvert !
    x264enc tune=zerolatency bitrate=1000 speed-preset=ultrafast !
    h264parse config-interval=-1 !
    video/x-h264,stream-format=byte-stream,alignment=au !
    rtph264pay name=pay0 pt=96
""")
factory.set_shared(True)

mounts.add_factory("/stream", factory)
server.attach(None)

print("RTSP-server kjører på rtsp://<PI_IP>:8554/stream")
GLib.MainLoop().run()
