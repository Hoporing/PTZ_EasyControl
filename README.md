![Banner](assets/Hoporing_Banner.png)

# PTZ_EasyControl

ONVIF Protocol 기반 PTZ Camera Viewer.  
RTSP Stream을 재생하면서 현재 Pan / Tilt / Zoom 값을 OSD로 실시간 표시합니다.

---

## 실행 화면

![Demo](assets/ptz.gif)

---

## 주요 기능

- **ONVIF 연결** — IP / Port / 계정 정보로 Camera에 연결
- **RTSP Streaming** — OpenCV + FFmpeg (TCP Transport 강제)
- **PTZ OSD Overlay** — Pan / Tilt / Zoom 값을 영상 위에 실시간 표시
- **Background Polling** — PTZ 상태를 별도 Thread에서 0.5초 주기로 갱신 (Video Loop 영향 없음)
- **해상도 적응형 OSD** — 720p / 1080p / 1440p / 4K별 Font Size 및 Thickness 자동 조정
- **H.264 Profile 자동 선택** — HEVC Decoding 오류 방지

---

## 기술 스택

| 분류 | 내용 |
|------|------|
| 언어 | Python 3.12+ |
| Camera Protocol | ONVIF (python-onvif-zeep) |
| Video | OpenCV, FFmpeg (RTSP) |

---

## 설치 및 실행

```bash
git clone https://github.com/Hoporing/PTZ_EasyControl.git
cd PTZ_EasyControl

pip install onvif-zeep opencv-python requests urllib3

python onvif_ptz_osd.py --ip <Camera IP> --user <ID> --password <PW>
```

**옵션:**
```
--ip        Camera IP 주소 (필수)
--port      ONVIF Port (기본값: 80)
--user      Username (필수)
--password  Password (필수)
```

`q` 키로 종료

---

## Zoom 배율 제어 (CGI API)

일부 Camera는 CGI API로 Zoom 배율을 직접 조회/설정할 수 있습니다.

```bash
# 현재 Zoom 배율 조회
python camera_zoom_test.py -i <Camera IP> -u admin -p <PW> -a get

# Zoom 배율 설정
python camera_zoom_test.py -i <Camera IP> -u admin -p <PW> -a set -z <값>
```

---

## License

[MIT License](LICENSE)
