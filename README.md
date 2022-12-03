# Universidad Austral 

## Vision Artificial 2022

### Integrantes: Katia Cammisa, Alejo Ramirez Gismondi, Matias Gayo, Numa Leone Elizalde

# Air Draw
![Demo of my trying out the hands](./demo.gif)


## Setup
<b>NOTE</b> This setup is just for what I use (Ubuntu 20.04). While I am willing to bet this will work for windows and unix, just be safe!
### Virtual environment
`python3 -m venv venv`
### Install Dependencies
`source ./venv/bin/activate`

`pip3 install -r requirements.txt`
### Run program
`python3 airdraw.py`

## Available Gestures

### Drawing
![Drawing directly on screen](./demo_gifs/drawing.gif)

To draw, you need to show the camera your hand with one finger up. This mode lets you draw any movement you do with the tip of that finger. 

### Hovering
![Hovering over drawings on screen](./demo_gifs/hovering.gif)

To hover, you need to show the camera your hand with only two fingers up. This mode lets you move your hand freely without drawing, or deleting anything you've previously drawn.

### Erasing
![Erasing earlier drawings on screen](./demo_gifs/eraser.gif)

To delete, you need to show the camera yout hand with three fingers up. This mode lets you delete any line that you have previously drawn, completely.


## Why?
I've seen tons of attempts of this sort of thing with HSV masks, and while it's more true to image processing that openCV caters for, I was sort of against letting our own styluses [go to waste](https://money.cnn.com/2015/09/10/technology/apple-pencil-steve-jobs-stylus/index.html).
Once I found out about [mediapipe](https://google.github.io/mediapipe/), I decided I would give this thing a shot! What you see is my attempt at materializing the idea, there is a more detailed [writeup](https://arefmalek.github.io/blog/Airdraw/) on my blog. 

## How?
Like I mentioned before, the ML workhorse here is definitely mediapipe. They've got awesome ML solutions so we can quickly gather data on the hand and use what we gather rather quickly. Other than that I pretty reliantly used OpenCV for image manipulation and NumPy for some basic dot products and because OpenCV uses numpy to represent images.

The conversion from hand data to lines / functionality is primarily done with some Python, basic linear algebra, and OpenCV. I'll leave the rest in the blog post. 

## What's next?
Truthfully, I'm not too sure. I got a ton of great suggestions, and I've been battling the urge to just change the whole repository to C++ instead of Python (only hesitating factor was setting up CMake honestly). If anyone is willing to get started on it, please feel free to fork / put up a Pull Request! 

Thanks for reading :)
