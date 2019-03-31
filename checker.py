#!/usr/bin/env python

import vk
import random
import cv2 as cv
import urllib
import numpy as np

import json

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

#group_id = "oldlentach"
group_id = "mnogomama_com"


fields = "sex, bdate, city, country, photo_max_orig, followers_count, personal, interests, career, relatives, screen_name"


MAX_SIZE = 500
PHOTO_COUNT = 5

USERS_COUNT = 50




session = vk.Session(access_token=access_token)
vk_api = vk.API(session, v='5.92')

ids = vk_api.groups.getMembers(group_id=group_id, count=USERS_COUNT)['items']
print(ids)

user_data = vk_api.users.get(user_ids=ids, fields=fields)

facecascade = cv.CascadeClassifier(cv.data.haarcascades + "haarcascade_frontalface_default.xml")
SCALE_FACTOR = 1.1
MIN_NEIGHBORS = 5

net = cv.dnn.readNetFromCaffe("./deploy.prototxt", "./age_net.caffemodel")
age_list = ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)', '(25, 32)', '(38, 43)', '(48, 53)', '(60, 100)']
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)




def check_family_photo(ages):
    children = 0
    adults = 0
    for age in ages:
        if age in ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)']:
            children += 1
        else:
            adults += 1
    if (children > 0) and (adults > 0):
        return True
    else:
        return False

def check_child_photo(ages):
    children = 0
    for age in ages:
        if age in ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)']:
            children += 1
    
    if (children > 0):
        return True
    else:
        return False

def check_adult_photo(ages):
    adults = 0
    for age in ages:
        if not age in ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)']:
            adults += 1
    
    if (adults > 0):
        return True
    else:
        return False



def check_user(user):
#    if (user['city']['id'] != 1): #Moscow
#        return False
    if len(user['family_photos']) >= 2:
        return True
    if 'relatives' in user and len(user['relatives']) > 2:
        return True
    if user['followers_count'] + user['friends_count'] > 5000:
        return True

    if len(user['child_photos']) >= 2 and len(user['adult_photos']) >= 2:
        return True

    return False





def shortPrint(user, interesting=False):
    if interesting:
        print("\033[92;1mInteresting user\033[0m: %s %s (%s)" % (user['first_name'], user['last_name'], user['link']))
    else:
        print("\033[92;1mProcessing user %d of %d\033[0m: %s %s (%s)" % (user_i, len(user_data), user['first_name'], user['last_name'], user['link']))
    


interesting_users = []

user_i = 0
for user in user_data:
    try:

        if ('screen_name' in user):
            user['link'] = "https://vk.com/" + user['screen_name']
        else:
            user['link'] = ""

        user_id = user['id']
        
        shortPrint(user)

        #vk_api.messages.send(user_id=user_id, random_id=random.randint(0,10000000), message="QWEQWEQWEQWEQWEQWE")

        subscriptions = vk_api.users.getSubscriptions(user_id=user_id)
        groups = subscriptions['groups']

        #photo_url = user['photo_max_orig'] 
        
        photos = vk_api.photos.get(owner_id=user_id, album_id='profile', count=PHOTO_COUNT, rev=1)
       
       
        photos['items'].insert(0, {'sizes':[{'url':user['photo_max_orig'], 'width':0, 'height':0}]})

        family_photos = []
        child_photos = []
        adult_photos = []
        for photo in photos['items']:

            photo_url = ""
            for photo_size in photo['sizes']:
                photo_url = photo_size['url']
                if (photo_size['width'] > MAX_SIZE or photo_size['height'] > MAX_SIZE):
                    break

            req = urllib.urlopen(photo_url)
            arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
            img = cv.imdecode(arr, -1)
            w = img.shape[1]
            h = img.shape[0]
            if h > w:
                img = cv.resize(img, (int(MAX_SIZE * w / h), MAX_SIZE))
            else:
                img = cv.resize(img, (MAX_SIZE, int(MAX_SIZE * h / w)))

            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            faces = facecascade.detectMultiScale(img, SCALE_FACTOR, MIN_NEIGHBORS, minSize=(10,10), maxSize=(200,200)) 

            i = 0
            photo_ages = []
            for (x, y, w, h) in faces:
                face = img[y:y+h, x:x+w]

                blob = cv.dnn.blobFromImage(face, 1, (227, 227), MODEL_MEAN_VALUES, swapRB=False)

                net.setInput(blob)
                ages_p = net.forward()
                age = age_list[ages_p[0].argmax()] 
                photo_ages.append(age)

                cv.circle(img, (x + w//2, y + h//2), w // 2, (0,255,0), 2)
                cv.putText(img, age, (x, y), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            if (check_family_photo(photo_ages)):
                family_photos.append(photo_url)

                cv.imshow("Family Photo", img)
                cv.waitKey(100)

            if (check_child_photo(photo_ages)):
                child_photos.append(photo_url)

            if (check_adult_photo(photo_ages)):
                adult_photos.append(photo_url)

        user['family_photos'] = family_photos
        user['child_photos'] = child_photos
        user['adult_photos'] = adult_photos
        user['groups'] = groups

        user['friends_count'] = vk_api.friends.get(user_id=user_id)['count']


        if (check_user(user)):
            interesting_users.append(user)
            print("Good user")

        if (len(family_photos) > 0):
            print("Family photos: (%d)" % len(family_photos))
            print(family_photos)
        
        #print(json.dumps(user, indent=2, sort_keys=False))

        user_i += 1

    except vk.exceptions.VkAPIError, cv.error:
        user_i += 1
        pass


print("\nInteresting users:\n")
for user in interesting_users:
    shortPrint(user, True)
