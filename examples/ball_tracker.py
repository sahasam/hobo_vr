import cv2
import time
import pickle

cap = cv2.VideoCapture(0)

while cap.isOpened() :
    ret, frame = cap.read()

    if not ret :
        print("failed to retrieve image from camera. Aborting")
        exit(1)

    cv2.imshow('imgframe', frame)

    if cv2.waitKey(1) & 0xFF == ord('q') :
        break
    
