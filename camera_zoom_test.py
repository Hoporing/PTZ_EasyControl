import requests
import argparse


def get_zoom_step(ip, username, password):
    url = f"http://{ip}/cgi-bin/ptz/control.php?app=get&position_step=get"
    auth = requests.auth.HTTPBasicAuth(username, password)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        print(f"[{ip}] 줌 배율 읽어오기 요청: {url}")
        response = requests.get(url, auth=auth, headers=headers, timeout=5)
        response.raise_for_status()

        print("요청 성공!")
        print("결과 데이터:\n")
        print(response.text.strip())
        return response.text
    except Exception as e:
        print(f"요청 실패: {e}")
        return None


def set_zoom_step(ip, zoom_val, username, password):
    url = f"http://{ip}/cgi-bin/ptz/control.php?app=get&position_step=set&zoom_step={zoom_val}&channel=0"
    auth = requests.auth.HTTPBasicAuth(username, password)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        print(f"[{ip}] 줌 배율 설정 요청 (값: {zoom_val}): {url}")
        response = requests.get(url, auth=auth, headers=headers, timeout=5)
        response.raise_for_status()

        print("요청 성공!")
        print("결과 데이터:\n")
        print(response.text.strip())
        return response.text
    except Exception as e:
        print(f"요청 실패: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="카메라 줌 배율(CGI API) 제어 스크립트")
    parser.add_argument("-i", "--ip", required=True, help="카메라 IP 주소")
    parser.add_argument("-u", "--user", default="admin", help="아이디")
    parser.add_argument("-p", "--password", required=True, help="비밀번호")

    parser.add_argument(
        "-a", "--action", choices=["get", "set"], default="get")
    parser.add_argument("-z", "--zoom", type=int, help="설정할 줌 값 (set 모드 단위)")

    args = parser.parse_args()

    if args.action == "get":
        get_zoom_step(args.ip, args.user, args.password)
    elif args.action == "set":
        if args.zoom is None:
            print("오류: --zoom (-z) 값을 입력해주세요.")
        else:
            set_zoom_step(args.ip, args.zoom, args.user, args.password)
