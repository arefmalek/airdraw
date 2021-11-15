import numpy as np
import cv2 as cv


drawing = False # true if mouse is pressed
mode = True # if True, draw rectangle. Press 'm' to toggle to curve
ix,iy = -1,-1
# mouse callback function


# 1. set up drawing capability where we hold down to draw a line
# 2. set up couple of groups (red, green, blue)
# 3. profit??


colors = [
        (255,0,0), # blue
        (0,255,0), # green
        (0,0,255), # red
        ]
# Loading the default webcam of PC.
cap = cv.VideoCapture(0)

# Keep looping
while True:
    # Reading the frame from the camera
    ret, frame = cap.read()

    # Adding the colour buttons to the live frame for colour access
    frame = cv.rectangle(frame, (40,1), (140,65), (122,122,122), -1)
    frame = cv.rectangle(frame, (160,1), (255,65), colors[0], -1)
    frame = cv.rectangle(frame, (275,1), (370,65), colors[1], -1)
    frame = cv.rectangle(frame, (390,1), (485,65), colors[2], -1)


    cv.putText(frame, "CLEAR ALL", (49, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(frame, "BLUE", (185, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(frame, "GREEN", (298, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(frame, "RED", (420, 33), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv.LINE_AA)



    cv.imshow("buttons", frame)

    stroke = cv.waitKey(1) & 0xff  
    if stroke == ord('q') or stroke == 27: # press 'q' or 'esc' to quit
        break
    print("here")

cap.release()
cv.destroyAllWindows()

