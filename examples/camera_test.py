import cv2

cap = cv2.VideoCapture(0)


cap.set(cv2.CAP_PROP_EXPOSURE, -9)

print(cap.get(cv2.CAP_PROP_EXPOSURE))
print(cap.get(cv2.CAP_PROP_SATURATION))

while True :
    frame = cap.read()[1]

    cv2.imshow('imgframe', frame)

    if cv2.waitKey(1) & 0xFF == ord('q') :
        break

cv2.destroyAllWindows()
cap.release()