import cv2 as cv
import mediapipe as mp
import math

capture = cv.VideoCapture(0)
hands = mp.solutions.hands.Hands(min_detection_confidence=0.55, min_tracking_confidence=0.8)
error_code, frame = capture.read()
h, w, c = frame.shape

while True:
    error_code, frame = capture.read()
    frame = cv.flip(frame, 1)
    hands_points = []

    if error_code == True:
        recHands = hands.process(frame)
        if recHands.multi_hand_landmarks != None:
            hand_idx = 0
            for hand in recHands.multi_hand_landmarks:
                hand_points = []
                hand_point = 0
                for datapoint_id, point in enumerate(hand.landmark):
                    hand_points.append(point)
                    if hand_point != 0:
                        if (hand_point - 1) % 4 != 0:
                            cv.line(frame, (int(hand_points[hand_point].x * w),
                                                int(hand_points[hand_point].y * h)),
                                           (int(hand_points[hand_point - 1].x * w),
                                                int(hand_points[hand_point - 1].y * h)),
                                          (0, 255, 0), 2)
                        cv.circle(frame, (int(hand_points[hand_point - 1].x * w),
                                                int(hand_points[hand_point - 1].y * h)),
                                          4, (0, 0, 255), cv.FILLED)
                    hand_point += 1
                cv.circle(frame, (int(hand_points[20].x * w),
                                         int(hand_points[20].y * h)),
                                  4, (0, 0, 255), cv.FILLED)

                for near_wrist_point in (1, 5, 9, 13, 17):
                    cv.line(frame, (int(hand_points[0].x * w), int(hand_points[0].y * h)),
                                   (int(hand_points[near_wrist_point].x * w), int(hand_points[near_wrist_point].y * h)),
                                  (0, 255, 0), 2)

                x1, y1, x2, y2, x3, y3 = (hand_points[4].x * w, hand_points[4].y * h,
                                          hand_points[6].x * w, hand_points[6].y * h,
                                          hand_points[8].x * w, hand_points[8].y * h)
                calc_thumb_index, calc_dot_index = (math.sqrt(pow(x1 - x3, 2) + pow(y1 - y3, 2)),
                                                    math.sqrt(pow(x2 - x3, 2) + pow(y2 - y3, 2)))
                # print("calc_thumb_index: " + str(calc_thumb_index) + ", calc_dot_index: " + str(calc_dot_index))
                if calc_thumb_index < calc_dot_index:
                    frame = cv.putText(frame, "Activated", (20, 40), fontFace=cv.FONT_HERSHEY_TRIPLEX,
                                           fontScale=1.0, color=(0, 255, 0), thickness=2)
                else:
                    frame = cv.putText(frame, "Pending", (20, 40), fontFace=cv.FONT_HERSHEY_TRIPLEX,
                                       fontScale=1.0, color=(0, 255, 0), thickness=2)
            hand_idx += 1
        cv.imshow('Video', frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

capture.release()
cv.destroyAllWindows()