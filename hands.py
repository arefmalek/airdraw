import cv2 as cv
import mediapipe as mp
import numpy as np
from enum import Enum
from collections import deque

from util import xy_euclidean_dist, vectorize, cos_angle
class Gesture(Enum):
    DRAW = 'DRAW'
    HOVER = 'HOVER'
    ERASE = 'ERASE'
    TRANSLATE = 'TRANSLATE'

class LandmarkBuffer():
    """Helper RingBuffer class to abstract away averaging logic"""

    def __init__(self, max_size):
        self.buf = deque([], maxlen=max_size)

    def push_landmark(self, element):
        self.buf.append(element)
    
    def average_landmarks(self):
        assert(len(self.buf) > 0)
        res = [[0]*3 for i in range(21)]
        num_points = len(self.buf)
        
        for landmark in self.buf:
            for i, vec in enumerate(landmark):
                res[i][0] += vec[0]
                res[i][1] += vec[1]
                res[i][2] += vec[2]
        
        for i, vec in enumerate(res):
            res[i][0] /= num_points
            res[i][1] /= num_points
            res[i][2] /= num_points

        return res

    def displacement(self):
        """Calculates the residual from the last two landmarks"""
        res = [[0]*3 for i in range(21)]
        num_points = len(self.buf)
        if num_points < 2 or any([len(landmark) != 21 for landmark in self.buf]):
            return res
        
        for i in range(21):
            for j in range(3):
                res[i][j] = self.buf[-1][i][j] - self.buf[-2][i][j]
        return res

class HandDetector():
    """
    This class defines the interaction the program will have with Mediapipe. It is essentially a wrapper layer around MP.

    This class will define how Airdraw will be passing information to and receiving information from Mediapipe. 
    Successful implementation of this class should involve no image rendering, but rather just state transformation of hands, gestures, and other metadata used from Mediapipe.
    """

    def __init__(self, mode = False, max_hands = 1):
        # setup
        self.max_hands = max_hands
        self.mode = mode
        # hand drawing stuff
        self.hands = mp.solutions.hands.Hands(self.mode, self.max_hands)
        self.drawing = mp.solutions.drawing_utils
        self.hand_connections = mp.solutions.hands.HAND_CONNECTIONS
        # will be used for translation
        self.translation_buffer = LandmarkBuffer(5)
        # we have 0 velocity to start translation

    def detect_landmarks(self, frame):
        """
        Noting all the points of one's hand in the image.

        args:
            - frame: np array representing image input. used to resize the prediction against mediapipe (will just use the builtin api soon though).
       returns:
            - list of landmarks on the hand in order of size and position
        """
        img_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB) # I think we need RGB
        self.results = self.hands.process(img_rgb)

        landmarks = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[0] # should only be one
            for idx, landmark in enumerate(my_hand.landmark):
                height, width, _ = frame.shape
                x, y = int(landmark.x * width), int(landmark.y * height)
                landmarks.append((idx, x, y))

        return landmarks
    
    def draw_landmarks(self, img):
        """
        Draws hand landmarks on image. Breaks rules of class being only "img"->hand current state, but I think this looks the best so I'm keeping it this way.
        """
        if self.results.multi_hand_landmarks:
           for hand_landmark in self.results.multi_hand_landmarks:
               self.drawing.draw_landmarks(img, hand_landmark, mp.solutions.hands.HAND_CONNECTIONS)

   
    def detect_gesture(self, landmarks, threshhold=0.70, debug=False):
        """
        This function determines which "mode" we are in, signified by the
        hand-signs someone indicates when we are drawing

        Arguments:
            landmarks: finger points
            threshhold: value we need in order to change 'modes'
        returns:
            String that matches the gesture we have
        """

        # adding all vectors
        # palm vectors
        palm_index_vector = vectorize(landmarks[0], landmarks[5])
        palm_mid_vector = vectorize(landmarks[0], landmarks[9])
        palm_ring_vector = vectorize(landmarks[0], landmarks[13])
        palm_pinky_vector = vectorize(landmarks[0], landmarks[17])

        # index vectors, each start from first knuckle of the hand
        index_vector = vectorize(landmarks[6], landmarks[8])
        middle_vector = vectorize(landmarks[10], landmarks[12])
        ring_vector = vectorize(landmarks[14], landmarks[16])
        pinky_vector = vectorize(landmarks[18], landmarks[20])

        # really just to debug
        if debug:
            return cos_angle(index_vector, palm_index_vector)

        # index finger pointing out, 
        # middle/ring/pinky finger tucked
        if cos_angle(palm_index_vector, index_vector) > threshhold and \
            cos_angle(index_vector, middle_vector) < 0 and \
                cos_angle(index_vector, ring_vector) < 0 and \
                    cos_angle(index_vector, pinky_vector) < 0:
           return Gesture.HOVER

        # index/middle finger pointing out, 
        # ring/pinky finger tucked
        if cos_angle(palm_index_vector, index_vector) > threshhold and \
            cos_angle(palm_mid_vector, middle_vector) > threshhold and \
                cos_angle(index_vector, ring_vector) < 0 and \
                    cos_angle(index_vector, pinky_vector) < 0:
            return Gesture.DRAW

        # index/middle/ring finger pointing out
        # pinky finger tucked
        if cos_angle(palm_index_vector, index_vector) > threshhold and \
            cos_angle(index_vector, middle_vector) > 0.90 and \
            cos_angle(index_vector, ring_vector) > 0.90 and \
                    cos_angle(palm_pinky_vector, pinky_vector) < 0:
           return Gesture.ERASE
        
        # add the stuff relative to knuckles
        if cos_angle(palm_index_vector, index_vector) > threshhold and \
            cos_angle(palm_pinky_vector, pinky_vector) > threshhold and \
                cos_angle(index_vector, middle_vector) < 0 and \
                    cos_angle(index_vector, ring_vector) < 0:
            return Gesture.TRANSLATE
        
        # otherwise hover
        return Gesture.HOVER
    
    def get_gesture_metadata(self, frame):
        """
        Calls MP on frame and returns metadata about gesture determined.
        Args: 
            - frame: np array defining our image.
        Returns: 
            - returns a dict defining gesture as well as metadata to draw output with.
        """

        landmark_list = self.detect_landmarks(frame)
        if len(landmark_list) == 0 or np.sum(landmark_list) == 0:
            return {}
        
        self.translation_buffer.push_landmark(landmark_list)
        average_landmark_list = self.translation_buffer.average_landmarks()
        gesture = self.detect_gesture(average_landmark_list)

        # only extract the row, col before sending it literally anywhere else
        _, index_c, index_r = average_landmark_list[8]
        _, mid_c, mid_r = average_landmark_list[12]
        _, ring_c, ring_r = average_landmark_list[16]
        _, pinky_c, pinky_r = average_landmark_list[20]

        # just writing in finger info
        index_fing_tip = (index_r, index_c) # coordinates of tip of index fing
        mid_fing_tip = (mid_r, mid_c)
        ring_fing_tip = (ring_r, ring_c)
        pinky_fing_tip = (pinky_r, pinky_c)

        # data sent to canvas:
        # formatted in row, column format because I index the internal grid that way.
        post = {'gesture': gesture, 
                'idx_fing_tip': index_fing_tip,
                'mid_fing_tip' : mid_fing_tip,
                'ring_fing_tip': ring_fing_tip,
                'pinky_fing_tip': pinky_fing_tip,
                'origin': None,
                'radius': None,
                'shift': None,
            }
        
        if gesture == Gesture.DRAW:
            distance = xy_euclidean_dist(index_fing_tip, mid_fing_tip)

            index_r, index_c = index_fing_tip
            mid_r, mid_c = mid_fing_tip

            midpoint_r, midpoint_c = int((index_r + mid_r) * 0.5), int((index_c + mid_c) * 0.5)

            post['origin'] = (midpoint_r, midpoint_c)
            post['radius'] = distance * 0.5

        elif gesture == Gesture.ERASE:
            distance = xy_euclidean_dist(index_fing_tip, ring_fing_tip)
            index_r, index_c = index_fing_tip
            ring_r, ring_c = ring_fing_tip

            midpoint_r, midpoint_c = int((index_r + ring_r) * 0.5), int((index_c + ring_c) * 0.5)

            post['origin'] = (midpoint_r, midpoint_c)
            post['radius'] = distance * 0.5

        # Add additonal info based off of info the gesture we got
        elif gesture == Gesture.TRANSLATE:
            distance = xy_euclidean_dist(index_fing_tip, pinky_fing_tip)

            index_r, index_c = index_fing_tip
            pinky_r, pinky_c = pinky_fing_tip

            midpoint_r, midpoint_c = int((index_r + pinky_r) * 0.5), int((index_c + pinky_c) * 0.5)

            post['origin'] = (midpoint_r, midpoint_c)
            post['radius'] = distance * 0.5

            # Calculate and store the shift
            displacement = self.translation_buffer.displacement()

            index_displacement = displacement[8]
            _, index_c_displacement, index_r_displacement = index_displacement

            post['shift'] = (index_r_displacement, index_c_displacement)
            
        elif gesture  == Gesture.HOVER:
            index_r, index_c = index_fing_tip
            midpoint_r, midpoint_c = int(index_r), int(index_c)
        
 
        # Update previous position position with current point
        return post

def replay(fname):
    print("replaying", fname)

    cap = cv.VideoCapture(fname)
    detector = HandDetector()

    if (not cap.isOpened()):
        print("Error opening video file")
        return

    while cap.isOpened() and (cv.waitKey(0) & 0xFF != ord('q')):
        ret, img = cap.read()

        # replay is completed when the video capture no longer has any frames to read.
        if ret:
            landmark_list = detector.detect_landmarks(img)
            detector.draw_landmarks(img)

            if len(landmark_list) != 0:
                val = detector.detect_gesture(landmark_list, threshhold=0.9)
                cv.putText(img, f"Mode: {val.value}", (50, 50),
                        cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv.LINE_AA)



            cv.imshow('Camera', img)
        else:
            break

    cap.release()
    cv.destroyAllWindows()

    print("replay complete", fname)

def live_demo():
    cap = cv.VideoCapture(0)
    detector = HandDetector()

    while True:
        _, img = cap.read()
        img = cv.flip(img, 1)

        landmark_list = detector.detect_landmarks(img)

        detector.draw_landmarks(img)

        if len(landmark_list) != 0:
            val = detector.detect_gesture(landmark_list, threshhold=0.9)
            cv.putText(img, f"Mode: {val.value}", (50, 50),
                    cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv.LINE_AA)

        cv.imshow('Camera', img)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    replay('hands_basic_gestures.mp4')
