import cv2 as cv

"""
TODO:

"""
class Canvas():
    """ 
    class that deals with drawing onto the screen
    Operates the dashboard of the screen (colors, clear all) as well as
    draw lines onto the screen
    """

    def __init__(self, columns, rows):
        self.colors = {
                "BLUE": (255,0,0),
                "GREEN": (0,255,0),
                "RED": (0,0,255),
                }
        self.color = "GREEN" # only really used to initialize lines
        self.lines = {} # whole list of points
        self.currLine = None # this is the line we're adding to 
        self.grid = [[None] * columns for row in range(rows)] # pointers to our functions

    # TODO: support multiple colors
    def draw_dashboard(self, frame, gesture = "HOVER", data = {}):
        """
        Creates the dashboard based on the current status

        Arguments:    
            frame: numpy array representing the current image
            gesture: the alignment of the hand
            point: the x, y coordinates corresponding to the finger if in drawing mode.
                    defaults to (-1, -1) because we may not even have the 

        """
        frame_height, frame_width, _ = frame.shape

        # find index finger
        idx_finger = (-1, -1, -1) # filler
        if data.get('idx_finger') != None:
            idx_finger = data['idx_finger']
        _, c, r = idx_finger 

        # add clear_button
        clear_button_width = int(frame_width *.2) # clear button always takes 20% of screen space
        clear_button_height = int(frame_height * .15) # all button take up 15% of screen height
        width_border = int(clear_button_width * .05) # 5% padding in both directions
        height_border = int(clear_button_height * .05)

        # gray 'clear all' button drawn on
        frame = cv.rectangle(frame, (width_border, height_border), 
                            (clear_button_width - width_border,clear_button_height - height_border),
                            (122, 122, 122), -1)
        cv.putText(frame, "CLEAR ALL", 
                (int(clear_button_width * .3),int(clear_button_height * .5)), 
                cv.FONT_HERSHEY_SIMPLEX, 
                        .5, (255, 255, 255), 2, cv.LINE_AA)
        
        # clear output!
        if (width_border <= c <= clear_button_width - width_border and 
            height_border <= r <= clear_button_height):
            self.lines = {}
            self.grid = [[None] * len(self.grid[0]) for row in range(len(self.grid))]

        # we have less space now, draw the buttons
        current_width  = frame_width - clear_button_width
        button_width = int(current_width / len(self.colors))
        button_height = clear_button_height
        width_border = int(button_width * .05)
        height_border = int(button_height *.05)

        x_dist = clear_button_width
        
        for name_color, color_arr in self.colors.items():
            # start drawing the button
            frame = cv.rectangle(frame, 
                                (x_dist + width_border, height_border), 
                                (x_dist + button_width - width_border, button_height - height_border),
                                color_arr, 
                                -1)
            # if we're in drawing mode and hover over this button, 
            # end line and chane color
            if gesture == "DRAW" and \
                (height_border <= r <= button_height - height_border and \
                x_dist + width_border <= c <= x_dist + button_width - width_border):
                self.end_line()
                self.color = name_color
            # highlight the color we've selected
            if name_color == self.color:
                frame = cv.rectangle(frame, 
                                    (x_dist + width_border, height_border), 
                                    (x_dist + button_width - width_border, button_height - height_border),
                                    (255, 255, 255),
                                    5)
            x_dist += button_width

        cv.putText(frame, f"Mode: {gesture}", 
                (width_border, int(button_height * 2)),
                cv.FONT_HERSHEY_SIMPLEX,
                2, self.colors[self.color], 3, cv.LINE_AA)
        
        # draw the ring if we're in the eraser mode
        if gesture == "ERASE":
            # get middle finger and radius of circle to draw
            distance = data['radius']
            _, mid_r, mid_c = data['mid_fing_tip']

            # put circle on the map, and add some opacity
            img = frame.copy()
            cv.circle(img, (mid_r, mid_c), int(distance*.5), (0,255,255), -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)
        elif gesture == "TRANSLATE":
            distance = data['radius']
            _, c, r = data['idx_finger']

            # put circle on the map, and add some opacity
            img = frame.copy()
            cv.circle(img, (c, r), int(distance*.5), (255,255,255), -1)
            alpha = 0.4
            frame = cv.addWeighted(frame, alpha, img, 1-alpha, 0)
        return frame

    def push_point(self, point):
        """
        adds a point to draw later on

        Arguments:
            point: (x, y) pair representing the coordinates of the current
            index finger (assuming we are in drawing mode)
        
        """

        # if there isn't an active line being drawn, start one
        if len(self.lines) == 0 or self.currLine == None or self.lines[self.currLine.get_origin()].active == False:
            # we need to initialize a line
            line = Line(self.color, point) # start a line with a new color
            self.currLine = line
            self.lines[point] = self.currLine # store origin in the lines
        else:
            # get the current line, add the new point to the linked list
            self.currLine.points.append(point)

        # gotta update our grid
        row, col = point 
        # dleft is distance from left border, 
        # dtop distance from top border
        self.grid[row][col] = self.currLine.get_origin()
        
    def end_line(self):
        """
            deactivates current line 
        """
        if self.currLine != None and len(self.lines) > 0:
            self.lines[self.currLine.get_origin()].active = False

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
                prev_y, prev_x = line.points[i-1]
                y, x = point
                cv.line(
                        frame, 
                        (prev_x, prev_y), 
                        (x, y), 
                        self.colors[line.color],
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
        # TODO: maybe speedup by looking to implement by "closest pair" approach
        r, c = position

        # we should be able to collect all unique origin points 
        uniqueLines = set()

        # for each point in the radius
        for dr in range(
                max(0, r - radius), 
                min(r + radius, len(self.grid) - 1)):
            for dc in range(
                    max(0, c - radius), 
                    min(c + radius, len(self.grid[0]) - 1)):
                # if we have some point in the line
                if self.grid[dr][dc] != None:
                    # get the origin point of this line
                    uniqueLines.add(self.grid[dr][dc])
        

        # for each origin point in the circle
        for og_point in uniqueLines:
            # remove original reference to the line and original grid values
            line = self.lines.pop(og_point)
            for r, c in line.points:
                self.grid[r][c] = None

            translation = []
            for r, c in line.points:
                trans_r, trans_c = r + shift[0], c + shift[1]
                # if the translated point is in the grid, add it, otw skip
                if (0 <= trans_r < len(self.grid)) and (0 <= trans_c < len(self.grid[0])):
                    translation.append((trans_r, trans_c))
                else:
                    break
            
            # if each point can be translated, change points arr
            if len(translation) == len(line.points):
                line.points = translation
            # otherwise we dont translate the point


#            # map the shift to the values of the line
#            line.points = list(map(lambda x: (x[0] + shift[0], x[1] + shift[1]), line.points))

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
            radius: the radius (in pixels) of our 
        """
        dleft, dtop = position

        self.currLine = None
        for dr in range(max(0, dleft - radius), 
                min(dleft + radius, len(self.grid[0]))):
            for dc in range(
                            max(0, dtop - radius), 
                            min(dtop + radius, len(self.grid))):
                if self.grid[dc][dr] != None:
                    key = self.grid[dc][dr]
                    line = self.lines.pop(key)
                    for (r, c) in line.points:
                        self.grid[r][c] = None


class Line():
    """
    Helper class to represent the lines put on the screen
    """

    def __init__(self, color, origin):
        self.color = color
        self.points = [origin]
        self.active = True

    def get_origin(self):
        return self.points[0]

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
