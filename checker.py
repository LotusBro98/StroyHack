#!/usr/bin/env python

import vk
import random
import cv2 as cv
import urllib
import numpy as np

#access_token = "0278078f487900898547ee42c429a0a6b4b8f075c9a65f7def3f7918922c37395f7547397a958cd51651d"
access_token = "fc25f343fc25f343fc25f343b8fc4c6bbaffc25fc25f343a0bace39cc11d6e7630c18d5"

ids = [
    "b_zzl",
    "alexpan98",
    "funky_style_dance_school",
    "id318959602",
    "sosha_i_am",
    "alexbogs",
    "rs_dyuldin",
    "zyuliya",
    "budiyanskaya"
]

fields = "sex, bdate, city, country, photo_max_orig, education, followers_count, personal, interests, music, movies, tv, books, games, about, quotes, career, relatives"

session = vk.Session(access_token=access_token)
vk_api = vk.API(session, v='5.92')

user_data = vk_api.users.get(user_ids=ids, fields=fields)

facecascade = cv.CascadeClassifier()
facecascade.load("./haarcascade_frontalface_default.xml")

net = cv.dnn.readNetFromCaffe("./deploy.prototxt", "./age_net.caffemodel")
age_list = ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)', '(25, 32)', '(38, 43)', '(48, 53)', '(60, 100)']

for user in user_data:
    user_id = user_data[0]['id']
    print(user)

    #vk_api.messages.send(user_id=user_id, random_id=random.randint(0,10000000), message="QWEQWEQWEQWEQWEQWE")

    subscriptions = vk_api.users.getSubscriptions(user_id=user_id)
    groups = subscriptions['groups']

    photo_url = user['photo_max_orig'] 
    req = urllib.urlopen(photo_url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv.imdecode(arr, -1)

    cv.imshow("Avatar", img)

    faces = facecascade.detectMultiScale(img) 

    i = 0
    for face_coord in faces:
        x1 = face_coord[1]
        y1 = face_coord[0]
        x2 = x1 + face_coord[2]
        y2 = y1 + face_coord[3]

        face = img[x1:x2, y1:y2]

        blob = cv.dnn.blobFromImage(face, 1, (227, 227))

        net.setInput(blob)
        ages = net.forward()
        age = age_list[ages[0].argmax()] 
        print(age)

        cv.imshow("Face " + str(i), face)
        i += 1

    cv.waitKey()
    
     
