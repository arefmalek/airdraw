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

## Why?
I've seen tons of tries of this sort of thing with HSV masks, and while it's more true to image processing that openCV caters for, I was sort of against letting our own styluses [go to waste](https://github.com/arefmalek/airdraw/blob/main/demo.gif)
Once I found out about [mediapipe](https://google.github.io/mediapipe/), I decided I would give this thing a shot! What you see is the first run-through of the project. I have a more detailed explanation on my blog post.

## How?
Like I mentioned before, the ML workhorse here is definitely mediapipe. They've got awesome ML solutions so we can quickly gather data on the hand and use what we gather rather quickly. Other than that I pretty reliantly used OpenCV for image manipulation and NumPy for some basic dot products and because OpenCV uses numpy to represent images.
