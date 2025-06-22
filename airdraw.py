import numpy as np
import cv2 as cv
from hands import HandDetector
from canvas import Canvas


def replay(fname):
    print("replaying", fname)

    cap = cv.VideoCapture(fname)
    # Use whatever width and height possible
    frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    canvas = Canvas(frame_width, frame_height)

    if (not cap.isOpened()):
        print("Error opening video file")
        return

    detector = HandDetector()
    while cap.isOpened() and (cv.waitKey(0) & 0xFF != ord('q')):
        ret, img = cap.read()

        # replay is completed when the video capture no longer has any frames to read.
        if ret:

            gesture_metadata = detector.get_gesture_metadata(img)

            img = canvas.update_and_draw(img, gesture_metadata)
            detector.draw_landmarks(img)

            cv.imshow('Camera', img)
        else:
            break

    cap.release()
    cv.destroyAllWindows()

    print("replay complete", fname)

def main():
    # Loading the default webcam of PC.
    cap = cv.VideoCapture(0)
    
    # width and height for 2-D grid
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH) + 0.5)
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT) + 0.5)

    # Set a larger window size (e.g., 1280x960)
    window_name = "Airdraw"
    cv.namedWindow(window_name, cv.WINDOW_NORMAL)
    cv.resizeWindow(window_name, 1280, 960)

    # initialize the canvas element and hand-detector program
    canvas = Canvas(height, width)
    detector = HandDetector()
    print(width, height)
    
    # Keep looping
    while True:
        # Reading the frame from the camera
        ret, frame = cap.read()
        frame = cv.flip(frame, 1)

        gesture_metadata = detector.get_gesture_metadata(frame)

        frame = canvas.update_and_draw(frame, gesture_metadata)
        detector.draw_landmarks(frame)

        # --- UI POLISH: Draw border and title ---
        border_color = (0, 255, 255)
        border_thickness = 8
        frame_height, frame_width = frame.shape[:2]
        cv.rectangle(frame, (0, 0), (frame_width-1, frame_height-1), border_color, border_thickness)
        # --- END UI POLISH ---

        cv.imshow(window_name, frame)
    
        stroke = cv.waitKey(1) & 0xff  
        if stroke == ord('b'): # press 'b' to switch backgrounds (camera/black)
            canvas.switch_background()
        if stroke == ord('s'): # press 's' to save current drawing
            save_path = "airdraw_saved.png"
            cv.imwrite(save_path, frame)
            print(f"Drawing saved as {save_path}")
        if stroke == ord('q') or stroke == 27: # press 'q' or 'esc' to quit
            break
    
    cap.release()
    cv.destroyAllWindows()

if __name__ == '__main__':
    main()
