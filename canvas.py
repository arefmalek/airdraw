import cv2 as cv
import numpy as np

from hands import Gesture, HandDetector

from enum import Enum

# FIXME: 
# use a good spatial query system
# have consistent usage of row, col convention between mediapipe, canvas, and opencv. 
# keep all data intialized at startup and only completely transform in function

class Color(Enum):
    GRAY = (122, 122, 122)
    WHITE = (255, 255, 255)
    BLUE = (255,0,0)
    GREEN =(0,255,0)
    RED = (0,0,255)

class Canvas():
    """ 
    This class is responsible for "drawing" all state onto the screen. 
    This includes the actual dashboard hands interact with as well as lines, backgrounds, etc.

    This component is intended to take (frame, hands_state) -> (update state) -> image to render
    """
    def __init__(self, rows, columns):
        # FIXME: just make this deterministic via list
        self.colors = [
                (Color.BLUE, "BLUE"),
                (Color.GREEN, "GREEN"),
                (Color.RED, "RED"),
                ]
        self.color = Color.BLUE # only really used to initialize lines
        self.lines = {} # whole list of points
        self.currLine = None # this is the line we're adding to 
        self.grid = [[None] * columns] * rows # pointers to our functions
        self.blackout_background = False

    def switch_background(self):
        self.blackout_background = not self.blackout_background

    def get_buttons_coords(self, frame_shape):
        """
        Returns coordinates of the buttons (and colors) to draw on the UI, used to save space later on.
        Should be useful for detecting overlap between fingers and buttons.

        Args:
            frame_shape: tuple describing frame shape
        Return:
            List with elements holding the following schema (button name, button BGR colors, top-left coordinate, bottom-right coordinate)
        """

        # Obtains the proportionally correct buttons for the frame shape given. 
        frame_height, frame_width, _ = frame_shape

        coords = []

        # add clear_button
        # Clear button is manually sized, all other buttons are manually sized
        clear_button_width = int(frame_width *.2) 
        clear_button_height = int(frame_height * .15) 

        clear_button_width_border = int(clear_button_width * .05) 
        clear_button_height_border = int(clear_button_height * .05)

        coords.append(
            (
                "Clear all",
                Color.GRAY.value,
                (clear_button_width_border, clear_button_height_border), 
                (clear_button_width - clear_button_width_border, clear_button_height - clear_button_height_border)
            ))

        n = len(self.colors)
        remaining_width = frame_width - clear_button_width

        color_button_width = int(remaining_width / n)
        color_button_height = int(clear_button_height * 0.7)
        color_button_border_width = int(color_button_width * 0.05)
        color_button_border_height = int(color_button_height * 0.05)
        curr_button_offset_width = clear_button_width

        for color, color_str in self.colors:
            coords.append((
                color_str,
                color.value,
                (curr_button_offset_width  + color_button_border_width, color_button_border_height),
                (curr_button_offset_width  + color_button_width - color_button_border_width, color_button_height - color_button_border_height)
            ))

            curr_button_offset_width += color_button_width
        return coords

    def buttons_overlap(self, buttons_coords, fingertip_point):
        leftCoord, topCoord = buttons_coords[0]
        rightCoord, bottomCoord = buttons_coords[1]

        _, c, r =  fingertip_point
        return leftCoord <= c <= rightCoord and topCoord <= r <= bottomCoord

    def update_state(self, frame_shape, data = {}):
        """
        This function should take in state updates from our hands, and update internal state of the game.
        """
        buttons_coord = self.get_buttons_coords(frame_shape)
        clear_button = buttons_coord[0]
        color_buttons = buttons_coord[1:]

        gesture = data.get("gesture", Gesture.HOVER)

        gesture_finger_points = [v for k, v in data.items() if k.endswith("_tip")]
        # check if any of the active vector points overlap with our buttons coordinates

        # overlap with clear button
        for coord in gesture_finger_points:
            if self.buttons_overlap(clear_button[2:], coord):
                # Clear state.
                self.end_line()
                self.lines = {}
                self.grid = [[None] * len(self.grid[0]) for row in range(len(self.grid))]
                break
        
        # overlap with color button
        for color_button_metadata in color_buttons:
            button_color_str = color_button_metadata[0]
            for coord in gesture_finger_points:
                if self.buttons_overlap(color_button_metadata[2:], coord):
                    if gesture == Gesture.DRAW:
                        self.end_line()
                    # assign the color value to our metadata
                    self.color = [color for color, color_str in self.colors if color_str == button_color_str][0]
        if gesture == Gesture.DRAW:
            midpoint_r, midpoint_c = data.get('origin')
            radius = int(data.get('radius')) # varying sizes

            self.push_point((midpoint_r, midpoint_c))
        elif gesture == Gesture.HOVER:
            self.end_line()
        elif gesture == Gesture.ERASE:
            self.end_line()

            midpoint_r, midpoint_c = data.get('origin')
            radius = int(data.get('radius'))
            self.erase_mode((midpoint_r, midpoint_c), radius)
        elif gesture == Gesture.TRANSLATE:
            self.end_line()

            midpoint_r, midpoint_c = data.get('origin')
            radius = int(data.get('radius'))
            shift = data.get('shift')
            shift = int(shift[0]), int(shift[1])
            self.translate_mode((midpoint_r, midpoint_c), radius, shift)
    
    def draw_canvas(self, frame, data):
        """
        Renders dashboard onto screen
        """
        if self.blackout_background:
            frame = np.zeros_like(frame)

        buttons_coord = self.get_buttons_coords(frame.shape)

        for button_metadata in buttons_coord:
            button_str = button_metadata[0]
            button_color_rgb = button_metadata[1]
            button_left, button_top = button_metadata[2]
            button_right, button_bottom = button_metadata[3]

            frame = cv.rectangle(frame, 
                                (button_left, button_top),
                                (button_right, button_bottom),
                                button_color_rgb, -1)
            cv.putText(frame, button_str, 
                    (button_left + int((button_right - button_left)* .3), int(button_bottom* .5)), 
                    cv.FONT_HERSHEY_SIMPLEX, .5, Color.WHITE.value, 2, cv.LINE_AA)
            # highlight selected color
            if button_color_rgb == self.color.value:
                frame = cv.rectangle(frame, 
                    (button_left, button_top),
                    (button_right, button_bottom),
                    Color.WHITE.value,
                    2)

        gesture = data.get('gesture')
        if gesture == Gesture.DRAW:
            midpoint_r, midpoint_c = data['origin']
            radius = data['radius'] 

            img = frame.copy()
            # purple cuz im royal
            cv.circle(img, (midpoint_c, midpoint_r), int(radius), (255,0,255), -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)
 
        # draw the ring if we're in the eraser mode
        if gesture == Gesture.ERASE:
            # get middle finger and radius of circle to draw
            midpoint_r, midpoint_c = data['origin']
            radius = data['radius']

            # put circle on the map, and add some opacity
            img = frame.copy()
            cv.circle(img, (midpoint_c, midpoint_r), int(radius), (0,255,255), -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)

        elif gesture == Gesture.TRANSLATE:
            midpoint_r, midpoint_c = data['origin']
            radius = data['radius']

            # put circle on the map, and add some opacity
            img = frame.copy()
            cv.circle(img, (midpoint_c, midpoint_r), int(radius), Color.WHITE.value, -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)
        
        frame = self.draw_lines(frame)

        return frame
    
    def update_and_draw(self, frame, data = {}):
        self.update_state(frame.shape, data)
        frame = self.draw_canvas(frame, data)
        return frame

    def push_point(self, point):
        """
        adds a point to draw later on

        Arguments: 
            point: (r, c) pair describing new coordinate of the line
        """

        row, col = point 
        if not 0 <= row < len(self.grid) or not 0 <= col < len(self.grid[0]):
            return

        # if there isn't an active line being drawn, start one
        if self.currLine == None or self.lines[self.currLine.get_origin()].active == False:
            # we need to initialize a line
            line = Line(self.color, point) # start a line with a new color
            self.currLine = line
            self.lines[point] = self.currLine # store origin in the lines
        else:
            # get the current line, add the new point to the linked list
            self.currLine.points.append(point)

        # gotta update our grid
        self.grid[row][col] = self.currLine.get_origin()
        
    def end_line(self):
        """
            deactivates current line 
        """
        if self.currLine != None and len(self.lines) > 0:
            self.lines[self.currLine.get_origin()].active = False
        self.currLine = None

    def draw_lines(self, frame):
        """
        Draws all of the lines we have generated so far by looping through line objects

        Args:
        - frame: The image straight from camera

        Returns:
        Image with all the different lines drawn on top of it
        
        """
        # self.lines = [{"color": "BLUE",
        #               "points": [(1, 2), (5, 9), ...]}, 
        #               {"color": "RED",
        #               "points": [(6, 0), (5, 8), ...]}, 
        for line in self.lines.values():
            for i, point in enumerate(line.points):
                if i == 0:
                    continue
                prev_r, prev_c = line.points[i-1]
                r, c = point
                cv.line(
                        frame, 
                        (prev_c, prev_r), 
                        (c, r), 
                        line.color.value,
                        5
                        )
        return frame

    def translate_mode(self, position, radius, shift):
        """
        Works as following:

        1. gather all lines in the radius
        2. for each line:
            shift each point in the line by the shift variable
        
        This should move each grid point where it needs to be, 
        which leaves is ready to draw on our regular draw function.
        """
        # FIXME: introducing extra lines unnecessarily into the program

        r, c = position
        if shift == (0, 0):
            return

        # we should be able to collect all unique origin points 
        uniqueLines = set()
        xy_euclidean_dist = lambda a1, a2: ((a1[0] - a2[0]) ** 2 + (a1[1] - a2[1]) ** 2) ** 0.5 

        for origin, line in self.lines.items():
            for p in line.points:
                if xy_euclidean_dist(p, position) <= radius:
                    uniqueLines.add(origin)
                    break
        
        # debugging line
        sortedLines = sorted(list(uniqueLines))
        print(sortedLines, [line for line in self.lines.keys()])

        # for each origin point in the circle
        for og_point in sortedLines:
            # Transform original points
            line = self.lines[og_point]
            translation = []
            for r, c in line.points:
                trans_r, trans_c = r + shift[0], c + shift[1]
                # if the translated point is in the grid, add it, otw skip
                if (0 <= trans_r < len(self.grid)) and (0 <= trans_c < len(self.grid[0])):
                    translation.append((trans_r, trans_c))
                else:
                    res = (0 <= trans_r < len(self.grid)) and (0 <= trans_c < len(self.grid[0]))
                    print("failed validation", res)
                    break

            # Check if transformation is valid
            if len(translation) == len(line.points):
                # reset the grid for this line
                self.lines.pop(og_point)
                for r, c in line.points:
                    self.grid[r][c] = None

                # update line state and then add it back to the grid
                line.points = translation
                new_origin = line.get_origin()
                assert(og_point != new_origin)

                # add the points back to the grid
                for r, c in line.points:
                    self.grid[r][c] = line.get_origin() # map the new points on the grid

                # put the value back in the lines
                self.lines[line.get_origin()] = line

    # start of erase mode code
    def erase_mode(self, position, radius):
        """
        Interprets the position of the pointer, 
        deletes lines if they overlap with the pointer

        Arguments:
            position: (x, y) coordinates of the position
            radius: the radius (in pixels) of our eraser
        """
        midpoint_r, midpoint_c = position

        for dr in range(
                max(0, midpoint_r - radius), 
                min(midpoint_r + radius, len(self.grid))
                ):
            for dc in range(
                            max(0, midpoint_c - radius), 
                            min(midpoint_c + radius, len(self.grid[0]))):
                if self.grid[dr][dc] != None:
                    key = self.grid[dr][dc]
                    line = self.lines.pop(key)
                    for (r, c) in line.points:
                        self.grid[r][c] = None


class Line():
    """
    Helper class to represent the lines put on the screen
    """

    def __init__(self, color: Color, origin):
        self.color = color
        self.points = [origin]
        self.active = True

    def get_origin(self):
        return self.points[0]

    def __repr__(self):
        return f"\ncolor({self.color}) \
                \n\tactive({self.active}) \
                \n\tpoints({self.points})"

def replay(fname):
    print("replaying", fname)

    cap = cv.VideoCapture(fname)
    # Use whatever width and height possible
    frame_width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

    canvas = Canvas(frame_height, frame_width)

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
    canvas = Canvas(100, 200)
    line = Line("BLUE", (1, 1))
    line.points.append((10, 5))
    print(line)


if __name__ == '__main__':
    # replay("./hands_basic_gestures.mp4")
    # replay("./buttons_overlap.mp4")
    # replay("./translation_debug.mp4")
    replay("./eraser_debug.mp4")

    # main()
