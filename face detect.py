import face_recognition
import numpy as np
import cv2 as cv
from facenet_pytorch import MTCNN
import torch
import os
import datetime

# import serial

import mediapipe as mp
import math

featuresPath = 'Encoded_dataset\\Features'
labelsPath = 'Encoded_dataset\\Labels'
features = []
labels = []
no_encoded_faces = 0
device = ''
hands = mp.solutions.hands.Hands(min_detection_confidence=0.55, min_tracking_confidence=0.8)

def extract_Encoded_Dataset():
    global device, labels, no_encoded_faces, features
    idx = 0
    for subDir in os.listdir(featuresPath):
        f = []
        fTemp = np.load(f'Encoded_dataset\\Features\\feature {idx}.npy')[0].tolist()
        for fIdx in range(len(fTemp)):
            f.append(np.asarray(fTemp[fIdx]))
        features.append(f)
        idx += 1

    no_encoded_faces = idx
    idx = 0
    for subDir in os.listdir(labelsPath):
        labels.append(np.load(f'Encoded_dataset\\Labels\\label {idx}.npy')[0].tolist())
        idx += 1

    if torch.cuda.is_available():
        device = 'cuda:0'
    else:
        device = 'cpu'

def saveToFile(known_person, frame, boxes, names):
    if known_person is True:
        path = f'Capture\\Known person'
    else:
        path = f'Capture\\Stranger'
    time = str(datetime.datetime.now()).split('.')[0]
    time = time.replace('-', '_').replace(':', '_').replace(' ', ' Time ')

    fileName = f''
    for i in range(len(boxes)):
        fileName += f'{names[i]} '

    fileName += f'Date {time}.jpg'
    print(f'Path: {os.path.join(path, fileName)}')

    cv.imwrite(os.path.join(path, fileName), frame)

def classify(img, error_in_detect, detect, names, confidences):
        en = face_recognition.face_encodings(img, face_recognition.face_locations(img))
        if len(en) > 0:
            confidence = 0.0
            for index in range(no_encoded_faces):
                en = face_recognition.face_encodings(img, face_recognition.face_locations(img))[0]
                matches = face_recognition.compare_faces(features[index], en, tolerance=0.45)

                if matches.count(True) / len(matches) > 0.75:
                    name = labels[index][matches.index(True)]
                    names.append(name)
                    confidences.append(round(matches.count(True) / len(matches), 2))
                    known_person = True
                    break
                elif index == no_encoded_faces - 1:
                    name = "Stranger"
                    names.append("Unknown")
                    confidences.append(round(1 - matches.count(True) / len(matches), 2))
                    known_person = False

        else:
            names.append("Parse error")
            confidences.append(0.0)
            known_person = False

        return known_person

def hand_gesture_capture(frame):
    hands_points = []
    h, w, c = frame.shape
    mode = False

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
                frame = cv.putText(frame, "Classified", (20, 40), fontFace=cv.FONT_HERSHEY_TRIPLEX,
                                   fontScale=1.0, color=(0, 255, 0), thickness=2)
                mode = True
            else:
                frame = cv.putText(frame, "Pending", (20, 40), fontFace=cv.FONT_HERSHEY_TRIPLEX,
                                   fontScale=1.0, color=(0, 255, 0), thickness=2)
        hand_idx += 1
    # cv.imshow('Video', frame)
    return mode, frame
def run():
    global device, labels, no_encoded_faces, features
    mtcnn = MTCNN(keep_all=True, device=device)

    capture = cv.VideoCapture(0)

    names = []
    confidences = []

    # ser = serial.Serial('COM14', 9600)
    while True:
        isSuccess, frame = capture.read()
        frame = cv.flip(frame, 1)
        name = None

        if isSuccess:
            mode, frame = hand_gesture_capture(frame)

            boxes, prob, points = mtcnn.detect(frame, landmarks=True)
            known_person = False

            if boxes is not None:
                idx = 0
                detect = False

                for box in boxes:
                    x1, y1, x2, y2 = box.tolist()

                    image = frame[int(y1) - 20:int(y2) + 20, int(x1) - 20:int(x2) + 20]
                    error_in_detect = False
                    try:
                        img = cv.cvtColor(image, cv.COLOR_BGR2RGB)
                    except Exception as e:
                        frame = cv.putText(frame, "Error", (int(x1), int(y1) - 50), fontFace=cv.FONT_HERSHEY_TRIPLEX,
                                           fontScale=1.0, color=(0, 255, 0), thickness=2)
                        frame = cv.putText(frame, f"0.0", (int(x1), int(y1) - 10),
                                           fontFace=cv.FONT_HERSHEY_TRIPLEX, fontScale=1.0, color=(0, 255, 0),
                                           thickness=2)
                        frame = cv.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        error_in_detect = True

                    # if cv.waitKey(1) & 0xFF == ord('c') or detect == True: #Detect = true for classify multiple face in an image
                    if mode == True or detect == True:  # Detect = true for classify multiple face in an image

                        if error_in_detect is False:
                            if detect is False:
                                names = []
                                confidences = []
                                detect = True

                            known_person = classify(img, error_in_detect, detect, names, confidences)
                            mode = False

                    elif idx == 0:
                        names = ["Ready"] * len(boxes)
                        confidences = [0.0] * len(boxes)

                    # print(f"idx: {idx}, len: {len(boxes)}")
                    # print("names len: " + str(len(names)))
                    frame = cv.putText(frame, names[idx], (int(x1), int(y1) - 50), fontFace=cv.FONT_HERSHEY_TRIPLEX,
                                       fontScale=1.0, color=(0, 255, 0), thickness=2)
                    frame = cv.putText(frame, f"{confidences[idx]}", (int(x1), int(y1) - 10),
                                       fontFace=cv.FONT_HERSHEY_TRIPLEX, fontScale=1.0, color=(0, 255, 0), thickness=2)
                    frame = cv.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    idx += 1

                # if detect is True:
                    # saveToFile(known_person, frame, boxes, names)
                    # break

            cv.imshow('Camera', frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    capture.release()
    cv.destroyAllWindows()
    # ser.close()

import pyRAPL

# pyRAPL.setup()
# meter = pyRAPL.Measurement('bar')
# meter.begin()
extract_Encoded_Dataset()
run()
# meter.end()