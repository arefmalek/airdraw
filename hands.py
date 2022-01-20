import cv2 as cv
import mediapipe as mp
import numpy as np


class HandDetector():
    """
    class that deals with the hand processing of the project
    """

    def __init__(self, mode = False, max_hands = 1):
        # setup
        self.max_hands = max_hands
        self.mode = mode
        # hand drawing stuff
        self.hands = mp.solutions.hands.Hands(self.mode, self.max_hands)
        self.drawing = mp.solutions.drawing_utils

    def detect_hands(self, img, draw=True):
        """
        Detects hands from images and draws them if requested

        returns image with annotations
        """
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB) # I think we need RGB
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks and draw:
            for hand_landmark in self.results.multi_hand_landmarks:
                self.drawing.draw_landmarks(img, hand_landmark,
                        mp.solutions.hands.HAND_CONNECTIONS)
        return img


    def detect_landmarks(self, shape: tuple):
        """
        Detecting hands from given image
        args:
            - img: image to grab hands from
        returns:
            - list of landmarks on the hand
        """
        landmarks = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[0] # should only be one
            for id, landmark in enumerate(my_hand.landmark):
                height, width, _ = shape
                x, y = int(landmark.x * width), int(landmark.y * height)
                landmarks.append([id, x, y])

        return landmarks
    
    def detect_gesture(self, landmarks, threshhold=0.90, debug=False):
        """
        This function determines which "mode" we are in, signified by the
        hand-signs someone indicates when we are drawing

        Arguments:
            landmarks: finger points
            threshhold: value we need in order to change 'modes'
            debug: "haha...what do you think?" - Stephan A smith
        returns:
            String that matches the gesture we have
        """
        vectorize = lambda u, v: [v[i] - u[i] for i in range(len(v))]

        palm_index_vector = vectorize(landmarks[0], landmarks[5])
        index_vector = vectorize(landmarks[5], landmarks[8])
        middle_vector = vectorize(landmarks[9], landmarks[12])
        ring_vector = vectorize(landmarks[13], landmarks[16])

        vector_magnitude = lambda vector: sum(dim**2 for dim in vector)**.5
        cos_angle = lambda u, v: np.dot(u, v) / (vector_magnitude(u)
                * vector_magnitude(v))

        # really just to debug
        if debug:
            return cos_angle(index_vector, middle_vector)

        # index finger pointing out, middle finger tucked, ring finger tucked
        if cos_angle(index_vector, middle_vector) < threshhold and \
                cos_angle(index_vector, ring_vector) < threshhold:
           return "DRAW"
        # index finger pointing out, middle finger pointing, ring finger
        # tucked
        elif cos_angle(index_vector, middle_vector) > threshhold and \
        cos_angle(index_vector, ring_vector) < threshhold:
            return "HOVER"

        # index finger pointing out, middle finger pointing, ring finger
        # pointing
        elif cos_angle(index_vector, middle_vector) > threshhold and \
        cos_angle(index_vector, ring_vector) > threshhold:
            return "ERASE"


        # otherwise hover
        return "HOVER"

def main():

    cap = cv.VideoCapture(0)
    detector = HandDetector()

    while True:
        _, img = cap.read()
        img = cv.flip(img, 1)
        img = detector.detect_hands(img)

        landmark_list = detector.detect_landmarks(img.shape)
        if len(landmark_list) != 0:
            val = detector.detect_gesture(landmark_list, threshhold=0.9,
                    )
            cv.putText(img, f"Mode: {val}", (50, 50),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv.LINE_AA)

        cv.imshow('Camera', img)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
