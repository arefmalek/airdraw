import cv2 as cv

def record(fname):
    if not fname.endswith(".mp4"):
        print("filename must be mp4 extension. Please try again")

    print("recording ", fname)
    cam = cv.VideoCapture(0)

    # Use whatever width and height possible
    frame_width = int(cam.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cam.get(cv.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    out = cv.VideoWriter(fname, fourcc, 60.0, (frame_width, frame_height))

    while True:
        _, img = cam.read()
        img = cv.flip(img, 1)

        out.write(img)

        cv.imshow('Recording', img)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    
    out.release()
    cam.release()
    cv.destroyAllWindows()
    print("recording complete. shutting down.")


def replay(fname):
    print("replaying", fname)

    cap = cv.VideoCapture(fname)

    if (not cap.isOpened()):
        print("Error opening video file")
        return

    while cap.isOpened() and (cv.waitKey(0) & 0xFF != ord('q')):
        ret, img = cap.read()

        # replay is completed when the video capture no longer has any frames to read.
        if ret:
            cv.imshow('Camera', img)
        else:
            break

    cap.release()
    cv.destroyAllWindows()

    print("replay complete", fname)

if __name__ == "__main__":
    print("what file name are we going to record/replay?")
    fname = input()
    print("record or replay (y for record, n for replay, everything else ignored)")
    mode = input()

    if mode == 'y':
        record(fname)
    elif mode == 'n':
        replay(fname)

