import functools
import math

import cv2 as cv
import numpy as np

from canvas import Canvas
from hands import HandDetector
from machine.utils.label_converters import int_to_label
from machine.utils.training_model import train_model


def getShapeData():
    shapeDict = list(map(chr, range(97, 123)))
    return shapeDict


def getShapeContours(alphabet):
    gray2 = cv.cvtColor(alphabet, cv.COLOR_RGB2GRAY)
    ret2, thresh2 = cv.threshold(gray2, 127, 255, cv.THRESH_BINARY)
    contours, hierarchy = cv.findContours(thresh2, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    cv.drawContours(alphabet, contours, -1, (0, 250, 0), 10)
    cv.imshow("alphabet", alphabet)
    return contours


def apply_color_convertion(frame, color):
    return cv.cvtColor(frame, color)


def get_contours(frame, mode, method):
    contours, hierarchy = cv.findContours(frame, mode, method)
    return contours


def most_repeated(lst):
    return max(set(lst), key=lst.count)


def machineDetection(detectFromFrame, lastMatches, model):
    gray_frame = apply_color_convertion(frame=detectFromFrame, color=cv.COLOR_RGB2GRAY)
    ret1, thresh1 = cv.threshold(gray_frame, 200, 255, cv.THRESH_BINARY_INV)
    contours = get_contours(frame=thresh1, mode=cv.RETR_EXTERNAL, method=cv.CHAIN_APPROX_NONE)
    cv.drawContours(detectFromFrame, contours, -1, (0, 0, 255), 2)
    cv.imshow('detected', detectFromFrame)
    filtered = contours
    if len(filtered) > 0:
        for detected in filtered:
            moments = cv.moments(detected)
            huMoments = cv.HuMoments(moments)
            for i in range(0, 7):
                a = 1
                if abs(huMoments[i]) > 0.0001:
                    a = huMoments[i]
                huMoments[i] = -1 * math.copysign(1.0, huMoments[i]) * math.log10(abs(a))
            sample = np.array(huMoments, dtype=np.float32)  # numpy
            testResponse = model.predict(sample)[1]
            lastMatches.append(testResponse[0][0])
            matchedNumber = most_repeated(lastMatches)
            print(int_to_label(int(matchedNumber)))


def main():
    # Loading the default webcam of PC.
    cap = cv.VideoCapture(0)

    # width and height for 2-D grid
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)

    # initialize the canvas element and hand-detector program
    canvas = Canvas(width, height)
    detector = HandDetector()

    model = train_model()
    lastMatches = []

    while True:
        # Reading the frame from the camera
        ret, frame = cap.read()
        detectFromFrame = cv.imread('./images/background.png')

        frame = cv.flip(frame, 1)

        frame = detector.detect_hands(frame)
        landmark_list = detector.detect_landmarks(frame.shape)
        gesture = None

        if len(landmark_list) != 0:
            gesture = detector.detect_gesture(landmark_list)

        # if we have a gesture, deal with it
        if gesture != None:
            idx_finger = landmark_list[8]  # coordinates of tip of index fing
            _, r, c = idx_finger

            frame = canvas.draw_dashboard(frame, gesture, (r, c))

            rows, cols, _ = frame.shape

            if 0 < r < cols and 0 < c < rows:
                if gesture == "DRAW":
                    canvas.push_point((r, c))
                elif gesture == "ERASE":
                    # stop current line
                    canvas.end_line()

                    # We find the distance
                    mid_fing = landmark_list[12]
                    euclidean_dist = lambda a, b: sum([(a[i] - b[i]) ** 2 for i in
                                                       range(len(a))]) ** .5
                    distance = euclidean_dist(idx_finger, mid_fing)
                    _, mid_r, mid_c = mid_fing

                    # put circle on the map, and add some opacity
                    img = frame.copy()
                    cv.circle(img, (mid_r, mid_c), int(distance * .5), (0, 255, 255), -1)
                    alpha = 0.4
                    frame = cv.addWeighted(frame, alpha, img, 1 - alpha, 0)

                    canvas.erase_mode((mid_r, mid_c), int(distance * 0.25))

                elif gesture == "HOVER":
                    canvas.end_line()
        else:
            frame = canvas.draw_dashboard(frame)
            canvas.end_line()

        # draw the stack
        frame = canvas.draw_lines(frame)
        detectFromFrame = canvas.draw_lines(detectFromFrame)

        # ADD Machine ########################################

        machineDetection(detectFromFrame, lastMatches, model)

        ###########################################################

        cv.imshow("Airdraw", frame)
        while len(lastMatches) >= 60:
            lastMatches.pop(0)

        stroke = cv.waitKey(1) & 0xff
        if stroke == ord('q') or stroke == 27:  # press 'q' or 'esc' to quit
            break

    cap.release()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
