import cv2 as cv

class Canvas():
    """ 
    class that deals with drawing onto the screen
    """

    def __init__(self):
        self.colors = {
                "BLUE": (255,0,0),
                "GREEN": (0,255,0),
                "RED": (0,0,255)
                }
        self.color = "GREEN" # only really used to initialize lines
        self.lines = []

    # TODO: support multiple colors
    def draw_color_data(self, frame, point = (0, 0)):
        """
        Draw the boxes that show colors, as well as the current selected option
            frame: numpy array representing the current image
        """
        height, width, _ = frame.shape
        x, y = point

        # add clear_button
        frame = cv.rectangle(frame, (40, 1), (140, 65), (122, 122, 122), -1)
        cv.putText(frame, "CLEAR ALL", (49,33), cv.FONT_HERSHEY_SIMPLEX, 
                .5, (255, 255, 255), 2, cv.LINE_AA)

        if (1 <= y <= 65 and 40 <= x <= 140):
            self.lines = []
        
        button_width = int((width - 150) / len(self.colors) - 20)
        x_dist = 160
        
        for name_color, color_arr in self.colors.items():
            # start drawing the button
            frame = cv.rectangle(frame, (x_dist, 1), (x_dist + button_width, 65),
                    color_arr, -1)
            # put text into the button
            cv.putText(frame, name_color, (x_dist + 10, 33),
                    cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2,
                    cv.LINE_AA)
            # just changing inputs if we hover over there
            if (1 <= y <= 65 and x_dist <= x <= x_dist + button_width):
                # button change!
                self.color = name_color
                self.end_line()
            if name_color == self.color:
                frame = cv.rectangle(frame, (x_dist, 1), (x_dist
                    + button_width, 65), (0, 255, 255), 5)
            x_dist += button_width + 20
        return frame

    def push_point(self, point):
        """
        adds a point to draw later on

        Arguments:
            point: (x, y) pair representing the coordinates of the current
            index finger (assuming we are in drawing mode)
        
        """
        if len(self.lines) == 0 or self.lines[-1].active == False:
            # we need to initialize a line
            line = Line(self.color) # start a line with a new color
            self.lines.append(line)

        # lines are like this
        self.lines[-1].points.append(point)
        
    def end_line(self):
        """
            deactivates current line 
        """
        if len(self.lines) > 0:
            self.lines[-1].active = False

    def draw_lines(self, frame):
        """
        Draws all of the lines we have generated so far
        """
        # self.lines = [{"color": "BLUE",
        #               "points": [(1, 2), (5, 9), ...]}, 
        #               {"color": "RED",
        #               "points": [(6, 0), (5, 8), ...]}, 
        for line in self.lines:
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

class Line():
    """
    Helper class to represent the lines I put on the screen
    """

    def __init__(self, color):
        self.color = color
        self.points = []
        self.active = True

    def __repr__(self):
        return f"\tcolor({self.color})\n \
                \tactive({self.active})\n \
                points({self.points})"
def main():
    canvas = Canvas()
    line = Line("BLUE")
    line.points.append((10, 5))
    print(line)


if __name__ == '__main__':
    main()
