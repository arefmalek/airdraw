import cv2 as cv
import numpy as np

from hands import Gesture, HandDetector
from util import xy_euclidean_dist

from enum import Enum

# FIXME: 
# use a good spatial query system (is just iterating over literally every point the best we can do?) 
# Gauging this would need the following:
#   How many data points could i realistically collect over a 2-minute episode?
#   How much does it cost to iterate and compare versus 
#       1. storing waypoints in a grid, and then searching every pixel in the grid
#       2. Storing all points in some sort of query system (intuition screaming quadtree).
# have consistent usage of row, col convention between mediapipe, canvas, and opencv. 
# keep all data intialized at startup and only completely transform in function

class Color(Enum):
    """Please remember these are in BGR coordinates!"""
    GRAY = (122, 122, 122)
    WHITE = (255, 255, 255)
    BLUE = (255,0,0)
    GREEN =(0,255,0)
    RED = (0,0,255)
    PURPLE = (255, 0, 255)
    YELLOW = (0, 255, 255)

class Shape(Enum):
    CIRCLE = Color.BLUE
    SQUARE = Color.GRAY
    LINE = Color.GREEN

class Canvas():
    """ 
    This class is responsible for "drawing" all state onto the screen. 
    This includes the actual dashboard hands interact with as well as lines, backgrounds, etc.

    This component is intended to take (frame, hands_state) -> (update state) -> image to render
    """
    def __init__(self, rows, columns):
        # FIXME: just make this deterministic via list
        self.colors = [ Color.BLUE, Color.GREEN, Color.RED ]
        self.shapes = [ Shape.LINE, Shape.CIRCLE, Shape.SQUARE ]
        self.rows = rows
        self.columns = columns
        self.color = Color.BLUE # only really used to initialize lines
        self.shape = Shape.LINE
        self.lines = {} # whole list of points
        self.circles = [] # whole list of points
        self.squares = [] # whole list of squares
        self.currLine = Line(None, self.color)# this is the line we're adding to 
        self.currLine.active = False
        self.currCircle = Circle((-1, -1), -1, self.color)# this is the line we're adding to 
        self.currCircle.active = False
        self.currSquare = Square((-1, -1), (-1, -1), self.color)
        self.currSquare.active = False
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
            List with elements holding the following schema: (button name, button BGR colors, top-left coordinate, bottom-right coordinate)
            Ordering of the elements is as follows:
                1. Clear all button
                2. Color buttons
                3. Shape buttons
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

        num_colors = len(self.colors)
        remaining_width = frame_width - clear_button_width

        color_button_width = remaining_width // num_colors 
        color_button_height = int(clear_button_height * 0.7)
        color_button_border_width = int(color_button_width * 0.05)
        color_button_border_height = int(color_button_height * 0.05)
        curr_button_offset_width = clear_button_width

        # FIXME: use color.name instead?
        for color in self.colors:
            coords.append((
                color.name,
                color.value,
                (curr_button_offset_width  + color_button_border_width, color_button_border_height),
                (curr_button_offset_width  + color_button_width - color_button_border_width, color_button_height - color_button_border_height)
            ))

            curr_button_offset_width += color_button_width
        
        num_shapes = len(Shape)
        remaining_height = frame_height - clear_button_height
        shape_button_height = (remaining_height // num_shapes)
        shape_button_width = int(clear_button_width * 0.7)
        shape_button_border_height = int(shape_button_height * 0.05)
        shape_button_border_width = int(shape_button_width * 0.05)

        curr_button_offset_height = clear_button_height

        for shape in Shape:
            coords.append((
                shape.name,
                shape.value.value,
                (shape_button_border_width, curr_button_offset_height + shape_button_border_height),
                (shape_button_width - shape_button_border_width, curr_button_offset_height + shape_button_height - shape_button_border_height)
            ))

            curr_button_offset_height += shape_button_height
        
        return coords

    def buttons_overlap(self, buttons_coords, fingertip_point):
        leftCoord, topCoord = buttons_coords[0]
        rightCoord, bottomCoord = buttons_coords[1]

        r, c =  fingertip_point
        return leftCoord <= c <= rightCoord and topCoord <= r <= bottomCoord

    def update_state(self, frame_shape, data = {}):
        """
        This function should take in state updates from our hands, and update internal state of the game.
        """
        buttons_coord = self.get_buttons_coords(frame_shape)
        clear_button = buttons_coord[0]
        button_offset = 1
        color_buttons = buttons_coord[button_offset:button_offset+len(self.colors)]
        button_offset += len(self.colors)
        shape_buttons = buttons_coord[button_offset:button_offset+len(Shape)]

        gesture = data.get("gesture", Gesture.HOVER)

        gesture_finger_points = [v for k, v in data.items() if k.endswith("_tip")]
        # check if any of the active vector points overlap with our buttons coordinates

        # overlap with clear button
        for coord in gesture_finger_points:
            if self.buttons_overlap(clear_button[2:], coord):
                # Clear state.
                self.end_drawing()
                self.lines = {}
                self.circles = []
                self.squares = []
                break
        
        # overlap with color button
        for color_button_metadata in color_buttons:
            button_color_str = color_button_metadata[0]
            for coord in gesture_finger_points:
                if self.buttons_overlap(color_button_metadata[2:], coord):
                    new_color = [color for color in self.colors if color.name == button_color_str][0]
                    if gesture == Gesture.DRAW:
                        self.end_drawing()
                    # assign the color value to our metadata
                    self.color = new_color

        # overlap with shape button
        for shape_button_metadata in shape_buttons:
            shape_str = shape_button_metadata[0]
            for coord in gesture_finger_points:
                if self.buttons_overlap(shape_button_metadata[2:], coord):
                    new_shape = [shape for shape in self.shapes if shape.name == shape_str][0]
                    if new_shape != self.shape and Gesture.DRAW:
                        self.end_drawing()
                    self.shape = new_shape

        if gesture == Gesture.DRAW:
            midpoint_r, midpoint_c = data.get('origin')
            radius = int(data.get('radius')) # varying sizes

            if self.shape == Shape.LINE:
                self.push_point((midpoint_r, midpoint_c))
            if self.shape == Shape.CIRCLE:
                self.update_circle((midpoint_r, midpoint_c))
            if self.shape == Shape.SQUARE:
                self.update_square((midpoint_r, midpoint_c))

        elif gesture == Gesture.HOVER:
            self.end_drawing()
        elif gesture == Gesture.ERASE:
            midpoint_r, midpoint_c = data.get('origin')
            radius = int(data.get('radius'))
            self.erase_mode((midpoint_r, midpoint_c), radius)
        elif gesture == Gesture.TRANSLATE:
            self.end_drawing()

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

            # Draw button background
            frame = cv.rectangle(frame, 
                                (button_left, button_top),
                                (button_right, button_bottom),
                                button_color_rgb, -1)

            button_width = button_right - button_left
            button_height = button_bottom - button_top

            # Draw shape icon if shape button
            if button_str in [shape.name for shape in Shape]:
                center_x = button_left + button_width // 2
                center_y = button_top + button_height // 2
                icon_size = min(button_width, button_height) // 3
                if button_str == "LINE":
                    cv.line(frame, (center_x - icon_size, center_y), (center_x + icon_size, center_y), (255,255,255), 3)
                elif button_str == "CIRCLE":
                    cv.circle(frame, (center_x, center_y), icon_size, (255,255,255), 3)
                elif button_str == "SQUARE":
                    cv.rectangle(frame, (center_x - icon_size, center_y - icon_size), (center_x + icon_size, center_y + icon_size), (255,255,255), 3)

            # Draw text for color buttons and clear
            if button_str not in [shape.name for shape in Shape]:
                cv.putText(frame, button_str, 
                        (button_left + int((button_width)* .3), int(button_top + button_height * .5)), 
                        cv.FONT_HERSHEY_SIMPLEX, .5, Color.WHITE.value, 2, cv.LINE_AA)

            # highlight selected color/shape
            if button_str == self.color.name or button_str == self.shape.name:
                frame = cv.rectangle(frame, 
                    (button_left, button_top),
                    (button_right, button_bottom),
                    Color.WHITE.value,
                    3)

        gesture = data.get('gesture')
        if gesture == Gesture.DRAW:
            midpoint_r, midpoint_c = data['origin']
            radius = data['radius'] 

            img = frame.copy()
            # purple cuz im royal
            cv.circle(img, (midpoint_c, midpoint_r), int(radius), Color.PURPLE.value, -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)
 
        # draw the ring if we're in the eraser mode
        if gesture == Gesture.ERASE:
            # get middle finger and radius of circle to draw
            midpoint_r, midpoint_c = data['origin']
            radius = data['radius']

            # put circle on the map, and add some opacity
            img = frame.copy()
            cv.circle(img, (midpoint_c, midpoint_r), int(radius), Color.YELLOW.value, -1)
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
        frame = self.draw_circles(frame)
        frame = self.draw_squares(frame)

        return frame
    
    def update_and_draw(self, frame, data = {}):
        self.update_state(frame.shape, data)
        frame = self.draw_canvas(frame, data)
        return frame

    def update_circle(self, new_point):
        """ Maintain state of the currently drawn circle. If it doesnt exist, initialize it and pass pointer to self.circles"""
        point_row, point_col = new_point

        if not (0 <= point_row < self.rows and 0 <= point_col < self.columns):
            return
        
        if self.currCircle.active == False:
            self.currCircle = Circle((point_row, point_col), 5, self.color)
            self.circles.append(self.currCircle)
        else:
            dist = int(xy_euclidean_dist(self.currCircle.origin, new_point))
            self.currCircle.radius = dist
    
    def update_square(self, new_point):
        """Updates state of the currently drawn square (resizing it). If it doesn't exist, initialize it and pass pointer to self.squares"""
        point_row, point_col = new_point

        if not (0 <= point_row < self.rows and 0 <= point_col < self.columns):
            return

        if self.currSquare.active == False:
            # just initialize with some size
            self.currSquare = Square(new_point, (point_row + 5, point_col + 5), self.color)
            self.squares.append(self.currSquare)
        else:
            self.currSquare.opposite = new_point

    def push_point(self, point):
        """
        adds a point to draw later on

        Arguments: 
            point: (r, c) pair describing new coordinate of the line
        """

        row, col = point 
        if not 0 <= row < self.rows or not 0 <= col < self.columns:
            return
        # TODO: replace hashmap approach with just generic list
        # if there isn't an active line being drawn, start one
        if self.currLine.active == False:
            # we need to initialize a line
            line = Line(self.color, point) # start a line with a new color
            self.currLine = line
            self.lines[point] = self.currLine # store origin in the lines
        else:
            # get the current line, add the new point to the linked list
            self.currLine.points.append(point)

    def end_drawing(self):
        """Ends active drawing"""
        self.currLine.active = False
        self.currCircle.active = False
        self.currSquare.active = False

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
    
    def draw_circles(self, frame):
        for circle in self.circles:
            orig_row, orig_col = circle.origin
            cv.circle(frame, (orig_col, orig_row), circle.radius, circle.color.value, 3)
        return frame
    
    def draw_squares(self, frame):
        for square in self.squares:
            topRow, leftCol, bottomRow, rightCol = square.get_coords()
            frame = cv.rectangle(
                frame,
                (leftCol, topRow),
                (rightCol, bottomRow),
                square.color.value,
                5
            )
        return frame


    def translate_mode(self, position, radius, shift):
        """
        Works as following:

        1. gather all lines in the radius
        2. for each line:
            shift each point in the line by the shift variable
        
       """
        # FIXME: introducing extra lines unnecessarily into the program

        r, c = position
        if shift == (0, 0):
            return

        # we should be able to collect all unique origin points 
        uniqueLines = set()
        for origin, line in self.lines.items():
            for p in line.points:
                if xy_euclidean_dist(p, position) <= radius:
                    uniqueLines.add(origin)
                    break
        
        # debugging line
        sortedLines = sorted(list(uniqueLines))

        # for each origin point in the circle
        for og_point in sortedLines:
            # Transform original points
            line = self.lines[og_point]
            translation = []
            for r, c in line.points:
                trans_r, trans_c = r + shift[0], c + shift[1]
                if (0 <= trans_r < self.rows) and (0 <= trans_c < self.columns):
                    translation.append((trans_r, trans_c))
                else:
                    break

            # Check if transformation is valid
            if len(translation) == len(line.points):
                self.lines.pop(og_point)

                line.points = translation
                new_origin = line.get_origin()
                assert(og_point != new_origin)

                # put the value back in the lines
                self.lines[line.get_origin()] = line
        
        for i, circle in enumerate(self.circles):                
            if circle.overlaps_circle(position, radius):
                new_origin = (circle.origin[0] + shift[0], circle.origin[1] + shift[1])
                circle.origin = new_origin

        for i, square in enumerate(self.squares):
            if square.overlaps_circle(position, radius):
                new_anchor = square.anchor[0] + shift[0], square.anchor[1] + shift[1]
                new_opposite = square.opposite[0] + shift[0], square.opposite[1] + shift[1]
                square.anchor = new_anchor
                square.opposite = new_opposite

    # start of erase mode code
    def erase_mode(self, position, radius):
        """
        Interprets the position of the pointer, 
        deletes lines if they overlap with the pointer

        Arguments:
            position: (x, y) coordinates of the position
            radius: the radius (in pixels) of our eraser
        """
        origin_points = []
        for origin, lines in self.lines.items():
            for point in lines.points:
                if xy_euclidean_dist(point, position) <= radius:
                    origin_points.append(origin)
                    break

        for origins in origin_points:
            self.lines.pop(origins)

        circles_to_keep = []
        for circle in self.circles:
            if circle.overlaps_circle(position, radius):
                continue
            else:
                circles_to_keep.append(circle)
        self.circles = circles_to_keep

        squares_to_keep = []
        for square in self.squares:
            if square.overlaps_circle(position, radius):
                continue
            else:
                squares_to_keep.append(square)

        self.squares = squares_to_keep

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

class Circle():
    """Helper class to place circles on screen"""
    def __init__(self, origin, radius: int, color: Color):
        self.origin = origin
        self.radius = radius
        self.color = color
        self.active = True
    
    def get_radius(self):
        return self.radius
    
    def overlaps_circle(self, point, other_radius) -> bool:
        dist = xy_euclidean_dist(self.origin, point)
        return max(self.radius - other_radius, 0) <= dist <= self.radius + other_radius

    
    def __repr__(self):
        return f"Origin:{self.origin}\tRadius:{self.radius}\tColor:{self.color}"


class Square():
    def __init__(self, anchor, opposite, color: Color):
        self.anchor = anchor
        self.opposite = opposite
        self.color = color
        self.active = True

    def get_coords(self):
        topRow = min(self.anchor[0], self.opposite[0])
        bottomRow = max(self.anchor[0], self.opposite[0])
        leftCol = min(self.anchor[1], self.opposite[1])
        rightCol = max(self.anchor[1], self.opposite[1])
        return (topRow, leftCol, bottomRow, rightCol)
    
    def get_height(self):
        topRow, leftCol, bottomRow, rightCol = self.get_coords()
        return (bottomRow - topRow)

    def get_width(self):
        topRow, leftCol, bottomRow, rightCol = self.get_coords()
        return (rightCol - leftCol)

    def overlaps_circle(self, point, radius) -> bool:
        """
        Returns true if the border of our square overlaps with the circle.
        Args
            point: (row, col) of the query point
        
        Math here - https://stackoverflow.com/a/402010
        """
        point_r, point_c = point

        topRow, leftCol, bottomRow, rightCol = self.get_coords()
        square_center_row = (topRow + bottomRow) // 2
        square_center_col = (leftCol + rightCol) // 2

        point_dist_r = abs(point_r - square_center_row) # compare against height
        point_dist_c = abs(point_c - square_center_col) # compare against width
        half_height = self.get_height() // 2
        half_width = self.get_width() // 2
        square_border_row_dist = abs(point_dist_r - half_height)
        square_border_col_dist = abs(point_dist_c - half_width)

        # Too far from the rectangle
        if (point_dist_r > (half_height + radius)): return False
        if (point_dist_c > (half_width + radius)): return False

        # Too close to the origin
        if (point_dist_r < (half_height - radius) and point_dist_c < (half_width - radius)): return False

        # If this code does what I think, it means that 
        # the row is in [half_height - radius, half_height + radius] 
        # the col is in [half_width - radius, half_width + radius]
        assert(half_width - radius <= point_dist_c <= half_width + radius or half_height - radius <= point_dist_r <= half_height + radius)

        # Point is within 
        if (point_dist_r > half_width and point_dist_c > half_height):
            cornerDist = (square_border_col_dist) ** 2 + (square_border_row_dist) ** 2
            return cornerDist <= radius**2
        
        return True

    def __repr__(self):
        topRow, leftCol, bottomRow, rightCol = self.get_coords()
        return f"topLeft: {(topRow, leftCol)}\tbottomRight:{(bottomRow, rightCol)}\tcolor:{self.color}"

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
    replay("./hands_drawing_ui.mp4")
    # replay("./eraser_debug.mp4")

    # main()
