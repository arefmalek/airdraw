import cv2 as cv
import argparse

def record(fname):    
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
    print("captured")
    if (not cap.isOpened()):
        print("Error opening video file")
        return

    print("waiting to open")
    while cap.isOpened(): # and (cv.waitKey(0) & 0xFF != ord('q')):
        ret, img = cap.read()

        # replay is completed when the video capture no longer has any frames to read.
        if ret:
            cv.imshow('Camera', img)
        else:
            break
        print("img", img.size)


    cap.release()
    cv.destroyAllWindows()

    print("replay complete", fname)


def main():
    parser = argparse.ArgumentParser(
        prog='data.py',
        description='data collections tools'
    )
    parser.add_argument("-m", "--mode")
    parser.add_argument("-f", "--filename")
    args = parser.parse_args()

    if not args.filename.endswith(".mp4"):
        print(f"filename({args.filename}) must end with .mp4")
        return False
    
    if args.mode == 'replay':
        replay(args.filename)
    elif args.mode == "record":
        record(args.filename)
    else:
        print(f"data mode must fall into ['replay', 'record'], provided {args.mode}")
        return False


if __name__ == "__main__":
    main()

