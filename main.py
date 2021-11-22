import numpy as np
import cv2 as cv
from hands import HandDetector
from canvas import Canvas


# 1. set up drawing capability where we hold down to draw a line
# 2. set up couple of groups (red, green, blue)
# 3. profit??


# Loading the default webcam of PC.
canvas = Canvas()
detector = HandDetector()

cap = cv.VideoCapture(0)


# recording video stuff I need 
width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)


# Keep looping
while True:
    # Reading the frame from the camera
    ret, frame = cap.read()
    frame = cv.flip(frame, 1)

    
    frame = detector.detect_hands(frame)
    landmark_list = detector.detect_landmarks(frame.shape)
    drawing = False

    if len(landmark_list) != 0:
        drawing = detector.detect_finger_mode(landmark_list)
    
    # add the point of data onto the stack
    if drawing:
        dr, dd = landmark_list[8][1:]

        rows, cols, _ = frame.shape
        if 0 < dr < cols and 0 < dd < rows:
            canvas.push_point((dr, dd))
    else:
        canvas.end_line()

    # draw the stack 
    frame = canvas.draw_lines(frame)
    
    cv.imshow("buttons", frame)

    stroke = cv.waitKey(1) & 0xff  
    if stroke == ord('q') or stroke == 27: # press 'q' or 'esc' to quit
        break

cap.release()
cv.destroyAllWindows()
