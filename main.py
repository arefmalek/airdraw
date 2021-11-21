import numpy as np
import cv2 as cv
from hands import handDetector

# 1. set up drawing capability where we hold down to draw a line
# 2. set up couple of groups (red, green, blue)
# 3. profit??


colors = [
        (255,0,0), # blue
        (0,255,0), # green
        (0,0,255), # red
        ]
# Loading the default webcam of PC.
points = []
cap = cv.VideoCapture(0)
detector = handDetector()

width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)

fourcc = cv.VideoWriter_fourcc(*'MP4V')
out = cv.VideoWriter('./output.mp4', fourcc, 20.0, (width,  height))


# Keep looping
while True:
    # Reading the frame from the camera
    ret, frame = cap.read()
    frame = cv.flip(frame, 1)

    
    frame = detector.detect_hands(frame)
    landmark_list = detector.detect_landmarks(frame.shape)
    dotProduct = 2

    if len(landmark_list) != 0:
        dotProduct = detector.detect_finger_mode(landmark_list)
    
    # add the point of data onto the stack
    if dotProduct < .9:
        dr, dd = landmark_list[8][1:]

        rows, cols, _ = frame.shape
        if 0 < dr < cols and 0 < dd < rows:
            points.append((dr, dd))
        
    # Adding the colour buttons to the live frame for colour access
    # frame = cv.rectangle(frame, (40,1), (140,65), (122,122,122), -1)
    # frame = cv.rectangle(frame, (160,1), (255,65), colors[0], -1)
    # frame = cv.rectangle(frame, (275,1), (370,65), colors[1], -1)
    # frame = cv.rectangle(frame, (390,1), (485,65), colors[2], -1)


    # cv.putText(frame, "CLEAR ALL", (49, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)
    # cv.putText(frame, "BLUE", (185, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)
    # cv.putText(frame, "GREEN", (298, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)
    # cv.putText(frame, "RED", (420, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)


    # draw the stack 
    for i, pt in enumerate(points):
        if i == 0:
            continue
        prev_dr, prev_dd = points[i-1]
        dr, dd = pt
        cv.line(frame, (prev_dr, prev_dd), (dr, dd), colors[2], 5)

    out.write(frame)
    cv.imshow("buttons", frame)

    stroke = cv.waitKey(1) & 0xff  
    if stroke == ord('q') or stroke == 27: # press 'q' or 'esc' to quit
        break

cap.release()
out.release()
cv.destroyAllWindows()