import numpy as np
import cv2 as cv
from hands import HandDetector
from canvas import Canvas


def record(cap):
    """
    helper function to set up to create a video writer to record demos with

    Arguments:
        cap: the videocapture object we get data from
    """
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)
    
    fourcc = cv.VideoWriter_fourcc(*'MP4V')
    out = cv.VideoWriter('./output.mp4', fourcc, 20.0, (width,  height))
    return out

def main(recording = False):
    # Loading the default webcam of PC.
    canvas = Canvas()
    detector = HandDetector()
    
    cap = cv.VideoCapture(0)
    
    out = None
    if recording:
        out = record(cap)
    
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
    
            frame = canvas.draw_color_data(frame, (dr, dd))
    
            rows, cols, _ = frame.shape
            if 0 < dr < cols and 0 < dd < rows:
                canvas.push_point((dr, dd))
        else:
            frame = canvas.draw_color_data(frame)
            canvas.end_line()
    
        # draw the stack 
        frame = canvas.draw_lines(frame)
        
        if recording:
            out.write(frame)
        cv.imshow("buttons", frame)
    
        stroke = cv.waitKey(1) & 0xff  
        if stroke == ord('q') or stroke == 27: # press 'q' or 'esc' to quit
            break
    
    if recording:
        out.release()
    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()
