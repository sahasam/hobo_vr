import threading
import time
import cv2

cap1 = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(1)

lock = threading.Lock()

def camera_read_thread(frame) :
    while True :
        with lock :
            frame = cap1.read()[1]
        cv2.imshow('frame', frame) 
        cv2.waitKey(int(1/25 * 1000)) 

        with lock :
            frame = cap2.read()[1]
        cv2.imshow('frame', frame)
        if cv2.waitKey(int(1/25 * 1000)) & 0xFF == ord('q') :
            break

frame = cap1.read()[1]
t1 = threading.Thread(target=camera_read_thread, args=(frame, ))
t1.setDaemon(True)
t1.start()

while True :
    with lock: 
        cv2.imshow("frame from main thread", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q') :
        break
    
cv2.destroyAllWindows()
cap1.release()
cap2.release()