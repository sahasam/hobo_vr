"""
calculate camera distortion matrix

saves matrix to 
"""
import os
import cv2
import numpy as np

images_location = os.path.join(os.path.dirname(__file__), 'calibration_images/')

def main() :
    # Checkerboard dimensions that the method looks for
    CHECKERBOARD = (6,9)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    objectpoints = []
    imagepoints = []

    objp = np.zeros((1,CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
    objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1,2)

    #cap = cv2.VideoCapture('checkerboardVideo.mp4')

    for image_path in os.listdir(images_location) :
        #ret, frame = cap.read()

        #if not ret :
            #print("failed to read from cap")
            #exit(1)

        input_path = os.path.join(images_location, image_path)
        frame = cv2.imread(input_path)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        cv2.imshow('grayscale', gray)

        #find 2d points in image where chessboard corners are
        ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)

        if ret :
           objectpoints.append(objp) 

           corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
           imagepoints.append(corners2)

           drawn_corners = cv2.drawChessboardCorners(frame, CHECKERBOARD, corners2, ret)
           drawn_corners_resized = cv2.resize(drawn_corners, (1920, 1080))

        cv2.imshow('drawn_corners_resized', drawn_corners_resized)

        cv2.waitKey(0)
        #if cv2.waitKey(1) & 0xFF == ord('q') :
            #break

    cv2.destroyAllWindows()
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objectpoints, imagepoints, gray.shape[::-1], None, None)

    print("camera matrix: ")
    print(mtx)
        

if __name__ == "__main__" :
    main()