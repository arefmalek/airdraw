import numpy as np
import cv2 as cv
from hands import HandDetector
from canvas import Canvas


def main():
    # Loading the default webcam of PC.
    cap = cv.VideoCapture(0)
    
    # width and height for 2-D grid
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)
 
    # initialize the canvas element and hand-detector program
    canvas = Canvas(width, height)
    detector = HandDetector()
    
    
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
                    # stop current line
                    canvas.end_line()

                    # We find the distance 
                    mid_fing = landmark_list[12]
                    euclidean_dist= lambda a, b: sum( [(a[i]- b[i])**2 for i in
                        range(len(a))])**.5
                    distance = euclidean_dist(idx_finger, mid_fing)
                    _, mid_r, mid_c = mid_fing

                    # put circle on the map, and add some opacity
                    img = frame.copy()
                    cv.circle(img, (mid_r, mid_c), int(distance*.5), (0,255,255), -1)
                    alpha = 0.4
                    frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)


                    canvas.erase_mode((mid_r, mid_c), int(distance * 0.25))

                elif gesture == "HOVER":
                    canvas.end_line()
        else:
            frame = canvas.draw_dashboard(frame)
            canvas.end_line()
    
        # draw the stack 
        frame = canvas.draw_lines(frame)
        
        cv.imshow("Airdraw", frame)
    
        stroke = cv.waitKey(1) & 0xff  
        if stroke == ord('q') or stroke == 27: # press 'q' or 'esc' to quit
            break
    
    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()
