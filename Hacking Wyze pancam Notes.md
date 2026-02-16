# Hacking Wyze pancam Notes

* Install [wz_mini_hacks](https://github.com/gtxaspec/wz_mini_hacks/wiki/Setup-&-Installation)
* Enable SSH access on the camera.
* We need to enable two RTP streams, one High res and one low res.
* The camera needs some modification to a boot script and config to support two streams simultaneously.

## Modification of config
* Add or modify the following variables in */opt/wz_mini/wz_mini.conf* 
    <code>
    <pre>
    ENABLE_RTSP="true"
    RTSP_AUTH_DISABLE="false"
    RTSP_LOGIN="admin"
    RTSP_PASSWORD="password"
    RTSP_PORT="8554"
    RTSP_PORT2="8555" #This is new
    RTSP_HI_RES_ENABLED="true"
    RTSP_HI_RES_ENABLE_AUDIO="true" #audio is necessary.
    RTSP_LOW_RES_ENABLED="true"
    RTSP_LOW_RES_ENABLE_AUDIO="true"
    </pre>
    </code>

## Modify a boot script to start 2 streams
* Modify this boot script */opt/wz_mini/etc/network.d/S15v4l2rtspserver*
* The line inside else statement is commented and replaced with two lines.
<code>
<pre>
if [[ "$RTSP_AUTH_DISABLE" == "true" ]]; then
    echo "Starting RTSP server"
    LD_LIBRARY_PATH=/opt/wz_mini/lib LD_PRELOAD=/system/lib/libsetunbuf.so /opt/wz_mini/bin/v4l2rtspserver $AUDIO_CH $AUDIO_FMT -F0 -P "$RTSP_PORT" $DEVICE1 $DEVICE2 > $RTSP.log 2>&1 &
else
    echo "Starting RTSP server"
    # LD_LIBRARY_PATH=/opt/wz_mini/lib LD_PRELOAD=/system/lib/libsetunbuf.so /opt/wz_mini/bin/v4l2rtspserver $AUDIO_CH $AUDIO_FMT -F0 -U "$RTSP_LOGIN":"$RTSP_PASSWORD" -P "$RTSP_PORT" $DEVICE1 $DEVICE2 > $RTSP.log 2>&1 &
    LD_LIBRARY_PATH=/opt/wz_mini/lib LD_PRELOAD=/system/lib/libsetunbuf.so /opt/wz_mini/bin/v4l2rtspserver $AUDIO_CH $AUDIO_FMT -F0 -U "$RTSP_LOGIN":"$RTSP_PASSWORD" -P "$RTSP_PORT" -u unicast -W 1920 -H 1080 $DEVICE1 & > $RTSP.log 2>&1 &
    LD_LIBRARY_PATH=/opt/wz_mini/lib LD_PRELOAD=/system/lib/libsetunbuf.so /opt/wz_mini/bin/v4l2rtspserver $AUDIO_CH $AUDIO_FMT -F0 -U "$RTSP_LOGIN":"$RTSP_PASSWORD" -P "$RTSP_PORT2" -u unicast -W 640 -H 360 $DEVICE2 & > $RTSP.log 2>&1 &
fi
</pre>
</code>

## This enables two RTSP streams
* High res connection at rtsp://admin:Password@IPofCamera:8554/unicast
* High res connection has two streams
  * Stream0 video at resolution 1920x1080, frame rate 15, H264-MPEG4 AVC
  * Stream1 audio PCM S16 BE (s16b) 44.1kHz mono 
* Low res stream at rtsp://admin:Password@IPofCamera:8555/unicast
  * Stream0 video at resolution 640x360 frame rate 15, H264-MPEG4 AVC
  * Stream1 audio PCM S16 BE (s16b) 44.1kHz mono 
* You can test both streams by conecting to VLC and File>Network and paste the URL and play (double click)
