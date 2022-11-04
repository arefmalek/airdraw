import functools

import cv2 as cv

from canvas import Canvas
from hands import HandDetector


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


# def draw_text(color_green, colors, shapeDict, shapeNumber, f, w, x, y):
#     text = getShapeData(shapeDict.get(shapeNumber))
#     for i, line in enumerate(text.split('\n')):
#         y1 = y + i * 50
#         cv.putText(colors, line, (x + w + 10, y1), cv.FONT_HERSHEY_SIMPLEX, 0.9, color_green, 2)
#     cv.drawContours(colors, f, -1, color_green, 20)


def main():
    # Loading the default webcam of PC.
    cap = cv.VideoCapture(0)

    # width and height for 2-D grid
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)

    # initialize the canvas element and hand-detector program
    canvas = Canvas(width, height)
    detector = HandDetector()

    alphabetOriginal = cv.imread('./images/alphabet.jpg')
    shapeContours = getShapeContours(alphabetOriginal)

    while True:
        # Reading the frame from the camera
        ret, frame = cap.read()
        detectFromFrame = cv.imread('./images/background.png')
        alphabet = alphabetOriginal.copy()

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

        # ADD MATCH SHAPES ########################################

        gray_frame = apply_color_convertion(frame=detectFromFrame, color=cv.COLOR_RGB2GRAY)
        ret1, thresh1 = cv.threshold(gray_frame, 200, 255, cv.THRESH_BINARY_INV)
        contours = get_contours(frame=thresh1, mode=cv.RETR_TREE, method=cv.CHAIN_APPROX_NONE)
        cv.drawContours(detectFromFrame, contours, -1, (0, 0, 255), 2)
        cv.imshow('detected', detectFromFrame)
        filtered = []

        for c in contours:
            # if 30000 < cv.contourArea(c):
            filtered.append(c)

        if len(filtered) > 0:
            for detected in filtered:

                for letter in shapeContours:

                    if cv.matchShapes(letter, detected, cv.CONTOURS_MATCH_I2, 0) < 0.1:
                        cv.drawContours(alphabet, letter, -1, (0, 0, 255), 2)
                        cv.imshow("alphabet", alphabet)

        ###########################################################

        cv.imshow("Airdraw", frame)

        stroke = cv.waitKey(1) & 0xff
        if stroke == ord('q') or stroke == 27:  # press 'q' or 'esc' to quit
            break

    cap.release()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
