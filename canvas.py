import cv2 as cv

"""
TODO:
- Requiring the finger to intersect the same pixel position as the line kinda
  sucks, I'm thinking we use a quadtree to give us a ~5 pixel radius
"""
class Canvas():
    """ 
    class that deals with drawing onto the screen
    Operates the dashboard of the screen (colors, clear all) as well as
    draw lines onto the screen
    """

    def __init__(self, width, height):
        self.colors = {
                "BLUE": (255,0,0),
                "GREEN": (0,255,0),
                "RED": (0,0,255),
                }
        self.color = "GREEN" # only really used to initialize lines
        self.lines = {}
        self.currLine = None
        # has to be python grid b/c I'm storing strings
        # no numpy :( gotta use cpp soon
        self.grid = [[None] * width for row in range(height)]
        print(len(self.grid), len(self.grid[0]))

    # TODO: support multiple colors
    def draw_dashboard(self, frame, gesture = "HOVER", point = (-1, -1)):
        """
        Creates the dashboard based on the current status

        Arguments:    
            frame: numpy array representing the current image
            gesture: the alignment of the hand
            point: the x, y coordinates corresponding to the finger if in drawing mode.
                    defaults to (-1, -1) because we may not even have the 

        """
        frame_height, frame_width, _ = frame.shape
        x, y = point

        # add clear_button
        clear_button_width = int(frame_width *.2) # clear button always takes 20% of screen space
        clear_button_height = int(frame_height * .15) # all button take up 15% of screen height
        width_border = int(clear_button_width * .05) # 5% padding in both directions
        height_border = int(clear_button_height * .05)

        frame = cv.rectangle(frame, (width_border, height_border), 
                            (clear_button_width - width_border,clear_button_height - height_border),
                            (122, 122, 122), -1)
        cv.putText(frame, "CLEAR ALL", (49,33), cv.FONT_HERSHEY_SIMPLEX, 
                        .5, (255, 255, 255), 2, cv.LINE_AA)
        
        # clear output!
        if (width_border <= x <= clear_button_width - width_border and 
            height_border <= y <= clear_button_height):
            self.lines = {}

        # we have less space now
        current_width  = frame_width - clear_button_width
        button_width = int(current_width / len(self.colors))
        button_height = clear_button_height
        width_border = int(button_width * .05)
        height_border = int(button_height *.05)

        x_dist = clear_button_width
        
        for name_color, color_arr in self.colors.items():
            # start drawing the button
            frame = cv.rectangle(frame, (x_dist + width_border, height_border), 
                                        (x_dist + button_width - width_border, button_height - height_border),
                                color_arr, -1)
            
            cv.putText(frame, name_color, (x_dist + int(button_width * .4), int(button_height*.4)),
                        cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                        cv.LINE_AA)
            # just changing inputs if we hover over there
            if gesture == "DRAW" and \
                (height_border <= y <= button_height - height_border and \
                x_dist + width_border <= x <= x_dist + button_width - width_border):
                self.color = name_color
                self.end_line()
            if name_color == self.color:
                frame = cv.rectangle(frame, 
                (x_dist + width_border, height_border), 
                (x_dist + button_width - width_border, button_height - height_border),
                (255, 255, 255), 5)
            x_dist += button_width

        cv.putText(frame, f"Mode: {gesture}", 
                (width_border, int(button_height * 2)),
                cv.FONT_HERSHEY_SIMPLEX,
                3, self.colors[self.color], 3, cv.LINE_AA)

        return frame

    def push_point(self, point):
        """
        adds a point to draw later on

        Arguments:
            point: (x, y) pair representing the coordinates of the current
            index finger (assuming we are in drawing mode)
        
        """
        if len(self.lines) == 0 or self.currLine == None or self.lines[self.currLine].active == False:
            # we need to initialize a line
            line = Line(self.color, point) # start a line with a new color
            self.currLine = str(line)
            self.lines[self.currLine] = line
        else:
            self.lines[self.currLine].points.append(point)

        # gotta update our grid
        dleft, dtop = point 
        # dleft is distance from left border, 
        # dtop distance from top border
        self.grid[dtop][dleft] = self.currLine
        
    def end_line(self):
        """
            deactivates current line 
        """
        if self.currLine != None and len(self.lines) > 0:
            self.lines[self.currLine].active = False

    def draw_lines(self, frame):
        """
        Draws all of the lines we have generated so far
        """
        # self.lines = [{"color": "BLUE",
        #               "points": [(1, 2), (5, 9), ...]}, 
        #               {"color": "RED",
        #               "points": [(6, 0), (5, 8), ...]}, 
        for line in self.lines.values():
            for i, point in enumerate(line.points):
                if i == 0:
                    continue
                prev_dr, prev_dd = line.points[i-1]
                dr, dd = point
                cv.line(
                        frame, 
                        (prev_dr, prev_dd), 
                        (dr, dd), 
                        self.colors[line.color],
                        5
                        )
        return frame

    # start of erase mode code
    def erase_mode(self, position):
        """
        Interprets the position of the pointer, 
        deletes lines if they overlap with the pointer

        Arguments:
            position: (x, y) coordinates of the position
        """
        dleft, dtop = position

        print(position, self.grid[dtop][dleft])
        if self.grid[dtop][dleft] != None:
            key = self.grid[dtop][dleft]
            line = self.lines.pop(key)
            for point in line.points:
                x, y = point
                self.grid[y][x] = None
        self.currLine = None

class Line():
    """
    Helper class to represent the lines put on the screen
    """

    def __init__(self, color, origin):
        self.color = color
        self.points = [origin]
        self.active = True

    def __repr__(self):
        return f"\tcolor({self.color})\n \
                \tactive({self.active})\n \
                points({self.points[0]})"
def main():
    canvas = Canvas()
    line = Line("BLUE")
    line.points.append((10, 5))
    print(line)


if __name__ == '__main__':
    main()
