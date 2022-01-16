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
    cap = cv.VideoCapture(0)
    
    # width and height for 2-D grid
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)
 
    canvas = Canvas(width, height)
    detector = HandDetector()
    
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
        gesture = None 
    
        if len(landmark_list) != 0:
            gesture = detector.detect_gesture(landmark_list)
        

        # if we have a gesture, deal with it
        if gesture != None:
            idx_finger = landmark_list[8] # coordinates of tip of index fing
            _, r, c = idx_finger
    
            frame = canvas.draw_dashboard(frame, gesture, (r, c))
    
            rows, cols, _ = frame.shape

            if (0 < r < cols and 0 < c < rows):
                if gesture == "DRAW":
                    canvas.push_point((r, c))
                elif gesture == "ERASE":
                    euclidean_dist= lambda a, b: sum( [(a[i]- b[i])**2 for i in
                        range(len(a))])**.5
                    mid_fing = landmark_list[12]

                    distance = euclidean_dist(idx_finger, mid_fing)
                    canvas.end_line()
                    canvas.erase_mode((r, c), int(distance * 0.25))
                    # TODO: incorporate erapse function
                elif gesture == "HOVER":
                    canvas.end_line()
        else:
            frame = canvas.draw_dashboard(frame)
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
    main(recording = True)
