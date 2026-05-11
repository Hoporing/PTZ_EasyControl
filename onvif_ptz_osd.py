import cv2
import threading
import time
import requests
import urllib3
import argparse
from onvif import ONVIFCamera

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
old_request = requests.Session.request


def bypass_ssl_verification(self, *args, **kwargs):
    kwargs['verify'] = False
    return old_request(self, *args, **kwargs)


requests.Session.request = bypass_ssl_verification

# Global variables to store PTZ data
ptz_pan = 0.0
ptz_tilt = 0.0
ptz_zoom = 0.0
is_running = True


def ptz_polling_worker(ptz_service, profile_token):
    """
    Background thread to continuously poll PTZ status.
    This prevents the main video rendering loop from freezing.
    """
    global ptz_pan, ptz_tilt, ptz_zoom, is_running

    while is_running:
        try:
            # Request current PTZ status
            status = ptz_service.GetStatus({'ProfileToken': profile_token})
            position = status.Position

            if position is not None:
                if hasattr(position, 'PanTilt') and position.PanTilt is not None:
                    ptz_pan = position.PanTilt.x
                    ptz_tilt = position.PanTilt.y
                if hasattr(position, 'Zoom') and position.Zoom is not None:
                    ptz_zoom = position.Zoom.x

            # Wait a bit before polling again to reduce load on the camera
            time.sleep(0.5)

        except Exception as e:
            print(f"[!] Error reading PTZ status: {e}")
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description="ONVIF PTZ Viewer")
    parser.add_argument('--ip', required=True, help="Camera IP address")
    parser.add_argument('--port', type=int, default=80,
                        help="Camera ONVIF port (default: 80)")
    parser.add_argument('--user', required=True, help="Camera username")
    parser.add_argument('--password', required=True, help="Camera password")
    args = parser.parse_args()

    global is_running

    try:
        print("[*] Connecting to ONVIF camera...")
        # Initialize ONVIF Camera
        mycam = ONVIFCamera(args.ip, args.port,
                            args.user, args.password)

        # Create media and PTZ services
        media_service = mycam.create_media_service()
        ptz_service = mycam.create_ptz_service()

        # Get camera profiles
        profiles = media_service.GetProfiles()
        if not profiles:
            print("[!] No media profiles found on the camera.")
            return

        # Try to find an H.264 profile to avoid OpenCV HEVC decoding errors
        profile = profiles[0]  # Fallback to the first profile
        for p in profiles:
            try:
                if hasattr(p, 'VideoEncoderConfiguration') and p.VideoEncoderConfiguration.Encoding == 'H264':
                    profile = p
                    print(
                        f"[*] Selected H.264 profile to prevent OpenCV H.265/HEVC playback errors.")
                    break
            except Exception:
                pass

        profile_token = profile.token

        print("[*] Retrieving RTSP Streaming URI...")
        # Request Stream URI
        stream_setup = {'Stream': 'RTP-Unicast',
                        'Transport': {'Protocol': 'RTSP'}}
        obj = media_service.create_type('GetStreamUri')
        obj.ProfileToken = profile_token
        obj.StreamSetup = stream_setup
        res = media_service.GetStreamUri(obj)
        stream_uri = res.Uri

        # Automatically embed credentials in the URI for OpenCV
        if stream_uri.startswith('rtsp://'):
            import urllib.parse
            user = urllib.parse.quote(args.user)
            passwd = urllib.parse.quote(args.password)
            # Insert auth info right after rtsp://
            stream_uri = stream_uri.replace(
                'rtsp://', f'rtsp://{user}:{passwd}@', 1)

        # Hide password in terminal output for security
        safe_uri = stream_uri
        if 'passwd' in locals():
            safe_uri = stream_uri.replace(f':{passwd}@', ':***@')

        print(f"[*] Stream URI: {safe_uri}")

        print("[*] Opening Video stream...")
        # Force TCP transport for RTSP to prevent packet corruption/HEVC decoding errors
        import os
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

        cap = cv2.VideoCapture(stream_uri, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print(
                "[!] Failed to open video stream. Check if OpenCV can read the RTSP stream.")
            return

        print("[*] Starting PTZ polling thread...")
        ptz_thread = threading.Thread(target=ptz_polling_worker, args=(
            ptz_service, profile_token), daemon=True)
        ptz_thread.start()

        print("[*] Starting Video Display. Press 'q' to quit.")
        # Create a resizable window
        cv2.namedWindow('ONVIF PTZ Viewer', cv2.WINDOW_NORMAL)

        while is_running:
            ret, frame = cap.read()
            if not ret:
                print("[!] Failed to grab frame from stream.")
                break

            # Extract frame dimensions for adaptive scaling
            h, w = frame.shape[:2]

            # Adaptive font scale
            font_scale = max(0.5, w / 1920.0)

            # Explicit thickness to guarantee exact values without math truncation
            if w >= 3800:       # UHD 4K
                thickness = 9
            elif w >= 2500:     # QHD 1440p
                thickness = 5
            elif w >= 1900:     # FHD 1080p
                thickness = 3
            else:               # HD 720p or lower
                thickness = 2
            # Adaptive padding (3% from left, 5% from top)
            padding_x = max(10, int(w * 0.03))
            padding_y = max(20, int(h * 0.05))

            # Create OSD text with current PTZ values
            osd_text = f"PAN: {ptz_pan:+.2f} | TILT: {ptz_tilt:+.2f} | ZOOM: {ptz_zoom:+.2f}"

            # Draw OSD on the video frame
            cv2.putText(frame, osd_text, (padding_x, padding_y), cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale, (82, 63, 245), thickness, cv2.LINE_AA)

            # Show the video window
            cv2.imshow('ONVIF PTZ Viewer', frame)

            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"[!] An error occurred: {e}")

    finally:
        # Cleanup and exit cleanly
        print("[*] Shutting down...")
        is_running = False
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
