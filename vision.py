try:
    import cv2
    import numpy as np
except:
    print("Couldn't load cv2")
import math
import subprocess

jpeg = None

def cvThread(cX):
    subprocess.call(['v4l2-ctl', '-c', 'exposure_auto=1'])
    subprocess.call(['v4l2-ctl', '-c', 'exposure_absolute=5'])
    subprocess.call(['v4l2-ctl', '-c', 'brightness=10'])

    global jpeg
    def findCenter(cnt):
        M = cv2.moments(cnt)
        #print(M["m00"])
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        return (cX, cY)

    def expand(rect):
        rect = (rect[0], (abs(rect[1][0]) + 4, abs(rect[1][1]) + 4), rect[2])
        return rect

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        frame = cv2.resize(frame, (160, 120))
        frame2 = cv2.resize(frame, (80, 60))
        scaleY = frame.shape[0] / frame2.shape[0]
        scaleX = frame.shape[1] / frame2.shape[1]
        offsetY = 10 * scaleY
        frame2 = frame2[10:,:]
        lower_green = np.array([50,160,27], np.uint8)
        upper_green = np.array([70,255,255], np.uint8)

        #gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        hsv_green = cv2.cvtColor(frame2,cv2.COLOR_BGR2HSV)
        thresh= cv2.inRange(hsv_green, lower_green, upper_green)

        #ret, thresh = cv2.threshold(hsv_green, 32, 255, cv2.THRESH_BINARY)
        #ret, thresh = cv2.threshold(gray, 32, 255, cv2.THRESH_BINARY)
        im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        contours = [np.int0(cv2.boxPoints(expand(cv2.minAreaRect(contour)))) for contour in contours]
        contours = [(cnt, cv2.contourArea(cnt), findCenter(cnt)) for cnt in contours]
        #contours = filter(lambda cnt: cv2.contourArea(cnt) > 0.0, contours)
        def key(cnt):
            try:
                return cnt[1]
            except:
                return 0.0
        largest_areas = sorted(contours, key=key)
        #cv2.drawContours(frame, largest_areas[-2:], -1, (0,255,0), 3)
        if len(largest_areas) >= 2:
            try:
                pair = largest_areas[-2:]
                #search for pairs
                # pair = None
                # best = None
                # for i in range(0, len(contours)):
                #     for j in range(0, len(contours)):
                #         if i != j:
                #             try:
                #                 x1, y1 = contours[i][2]
                #                 x2, y2 = contours[j][2]
                #                 a1 = contours[i][1]
                #                 a2 = contours[j][1]
                #                 if a2 > 8 and a1 > 8:
                #                     dx = .5 *(x2 - x1)
                #                     dy = 3.0 * (y2 - y1)
                #                     score = 0.2 * (abs(x1 - 40) + abs(x2 - 40)) + abs(a1 - a2) + math.sqrt(dx * dx + dy * dy)
                #                     if pair is not None:
                #                         if score < best:
                #                             best = score
                #                             pair = (contours[i], contours[j])
                #                     else:
                #                         pair = (contours[i], contours[j])
                #                         best = score
                #             except Exception as e:
                #                 print(e)
                # print("best: " + str(best))
                #cv2.drawContours(frame2, [cnt[0] for cnt in contours], -1, (0,0,255), 1)
                #cv2.drawContours(frame2, [pair[0][0], pair[1][0]], -1, (0,255,0), 1)
                x1, y1 = pair[0][2]
                x2, y2 = pair[1][2]
                cv2.circle(frame, (int(x1 * scaleX), int(y1 * scaleY + offsetY)), 4, (255, 0, 0))
                cv2.circle(frame, (int(x2 * scaleX), int(y2 * scaleY + offsetY)), 4, (255, 0, 0))
                cX.cx = (x1 + x2) / 2
                #print(cX.cx)
                cX.cy = (y1 + y2) / 2
                cv2.circle(frame, (int(cX.cx * scaleX), int(cX.cy * scaleY + offsetY)), 4, (255, 0, 255))
            except Exception as e:
                cX.cx = None
                print(e)
        else:
            cX.cx = None
            print("No contours")

        jpeg = frame

        #cv2.circle(frame, (cX, cY), 7, (255, 255, 255), -1)
        #cv2.putText(frame, "center", (cX - 20, cY - 20),
        #   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cap.release()

def flaskThread():
    from flask import Flask, render_template, Response

    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    def gen():
        while True:
            if jpeg != None:
                ret, tmp = cv2.imencode('.jpg', jpeg)
                jpg = tmp.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n\r\n')

    @app.route('/video_feed')
    def video_feed():
        return Response(gen(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    print("Running")
    app.run(host='0.0.0.0', port=5800, debug=False)
