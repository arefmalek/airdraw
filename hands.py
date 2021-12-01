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
    
    def detect_finger_mode(self, landmarks, threshhold=0.9):
        """
        This function takes in the image with detected hand signs and tells us
        if we are in drawing mode or not

        we do this by getting the dot product of 2 vectors (of index and middle
        fingers)

        Arguments:
            landmarks: finger points
            threshhold: value of 
        returns:
            True if dotProduct is above threshhold (drawing mode off), False otherwise
        """
        vectorize = lambda u, v: [v[i] - u[i] for i in range(len(v))]
        index_vector = vectorize(landmarks[6], landmarks[8])
        middle_vector = vectorize(landmarks[10], landmarks[12])
        val = np.dot(index_vector, middle_vector)

        vector_magnitude = lambda vector: sum(dim**2 for dim in vector)**.5
        val /= (vector_magnitude(index_vector) * vector_magnitude(middle_vector))
        if threshhold == None: # just for debugging purposes
            return val
        return val < threshhold

def main():

    cap = cv.VideoCapture(0)
    detector = HandDetector()

    while True:
        _, img = cap.read()
        img = cv.flip(img, 1)
        img = detector.detect_hands(img)

        landmark_list = detector.detect_landmarks(img.shape)
        if len(landmark_list) != 0:
            val = detector.detect_finger_mode(landmark_list, threshhold=None)
            cv.putText(img, f"Dot Product: {val:.4f}", (50, 50),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv.LINE_AA)

        cv.imshow('Camera', img)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()
