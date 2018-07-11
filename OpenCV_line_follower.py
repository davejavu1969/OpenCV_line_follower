#!/usr/bin/env python
# coding: Latin

# Load library functions we want
import time
import os
import sys
import threading
import picamera
import picamera.array
import cv2
import numpy

print('Libraries loaded')

# Global values
global running
global camera
global processor
global debug

# Camera settings
imageWidth = 320  # Camera image width
imageHeight = 240  # Camera image height
frameRate = 5  # Camera image capture frame rate

# Image stream processing thread
class StreamProcessor(threading.Thread):
    
    def __init__(self):
        super(StreamProcessor, self).__init__()
        self.stream = picamera.array.PiRGBArray(camera)
        self.event = threading.Event()
        self.terminated = False
        self.start()
        self.begin = 0

    def run(self):
        # This method runs in a separate thread
        while not self.terminated:
            # Wait for an image to be written to the stream
            if self.event.wait(1):
                try:
                    # Read the image and do some processing on it
                    self.stream.seek(0)
                    self.ProcessImage(self.stream.array, colour)
                finally:
                    # Reset the stream and event
                    self.stream.seek(0)
                    self.stream.truncate()
                    self.event.clear()

    # Image processing function
    def ProcessImage(self, image, colour):
        #image = image[140:360, 40:270]
        # View the original image seen by the camera.
        if debug:
            cv2.imshow('original', image)
            #cv2.imwrite('original.png', image)
            cv2.waitKey(0)

        # Blur the image
        image = cv2.medianBlur(image, 5)
        if debug:
            cv2.imshow('blur', image)
            #cv2.imwrite('blur.png', image)
            cv2.waitKey(0)

		#Convert to grayscale and find line contours
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        blur=cv2.GaussianBlur(gray,(5,5),0)#blur the grayscale image
        blur2=cv2.bitwise_not(blur)
        ret,th1 = cv2.threshold(blur2,35,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)#using threshold remave noise
        ret1,th2 = cv2.threshold(th1,127,255,cv2.THRESH_BINARY_INV)# invert the pixels of the image frame
        _, contours, _= cv2.findContours(th2,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE) #find the contours
        cv2.drawContours(blur2,contours,-1,(0,255,0),3)
        cv2.imshow('blur',blur2)
        #cv2.imwrite('blur2.png', blur2)
        if debug:
        	cv2.imshow('image',image) #show image
        
        try:
            for cnt in contours:
               if cnt is not None:
                   area = cv2.contourArea(cnt)# find the area of contour
                   if area>=500 :
                        # find moment and centroid
                        M = cv2.moments(cnt)
                        cx = int(M['m10']/M['m00'])
                        cy = int(M['m01']/M['m00'])
                        print('CX:',cx)
                        if cx <= 110:
                            print('GO LEFT')
                            #Enter your motor controller code here
                        
                        elif cx >= 118:
                            print('GO RIGHT')
                            #Enter your motor controller code here

                        elif cx >= 111 and cx <= 117:
                            print('GO STRAIGHT')
                            #Enter your motor controller code here
                            
                        else:
                            print('LOST')

        except KeyboardInterrupt:
          # User pressed CTRL-C, reset GPIO settings
          
        quit()

    
# Image capture thread
class ImageCapture(threading.Thread):
    def __init__(self):
        super(ImageCapture, self).__init__()
        self.start()

    def run(self):
        global camera
        global processor
        print('Start the stream using the video port')
        camera.capture_sequence(self.TriggerStream(), format='bgr', use_video_port=True)
        print('Terminating camera processing...')
        processor.terminated = True
        processor.join()
        print('Processing terminated.')

    # Stream delegation loop
    def TriggerStream(self):
        global running
        while running:
            if processor.event.is_set():
                time.sleep(0.01)
            else:
                yield processor.stream
                processor.event.set()


# Startup sequence
print('Setup camera')
camera = picamera.PiCamera()
camera.resolution = (imageWidth, imageHeight)
camera.framerate = frameRate
imageCentreX = imageWidth / 2.0
imageCentreY = imageHeight / 2.0

print('Setup the stream processing thread')
processor = StreamProcessor()

print('Wait ...')
time.sleep(2)
print('Primed and ready Player One...')
raw_input()
captureThread = ImageCapture()
    
# Tell each thread to stop, and wait for them to end
running = False
captureThread.join()
processor.terminated = True
processor.join()
del camera
print('Program terminated.')
