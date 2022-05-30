import tensorflow as tf
from flask import Flask, render_template, request, jsonify
import cv2
import pytesseract
import numpy as np
import matplotlib.pyplot as plt
# import pyrebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import os

app = Flask(__name__)

# pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

cred = credentials.Certificate("redmineKey.json")

model = tf.keras.models.load_model("C:\\Users\\ASUS\\PycharmProjects\\bangkit_capstone\\bounding_box_segmentation_5.h5")
# model.summary()

firebase = firebase_admin.initialize_app(cred,
                                         {'databaseURL': 'https://redmine-350506-default-rtdb.asia-southeast1.firebasedatabase.app/'}
                                         )

root = db.reference()

@app.route("/helloWorld")
def home():
    return "hello world"

@app.route("/getOcr", methods=['POST'])
def predict():
    imagefile = request.files['imagefile']
    uid = request.form.get('uid')
    # image_path = "C:\\Users\\ASUS\\PycharmProjects\\bangkit_capstone\\test.jpg"
    image_path = "C:\\Users\\ASUS\\PycharmProjects\\bangkit_capstone\\images\\"+imagefile.filename
    # image = imagefile.filename
    imagefile.save(image_path)

    img = cv2.imread(image_path, 0)
    ret, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY_INV)
    img = cv2.resize(img, (512, 512))
    img = np.expand_dims(img, axis=-1)
    img = img / 255

    img = np.expand_dims(img, axis=0)
    pred = model.predict(img)
    pred = np.squeeze(np.squeeze(pred, axis=0), axis=-1)
    # plt.imsave('C:\\Users\\ASUS\\PycharmProjects\\bangkit_capstone\\segmentation\\segmentation.png', pred)
    plt.imsave('segmentation.png', pred)

    img = cv2.imread('segmentation.png', 0)
    cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU, img)
    ori_img = cv2.imread(image_path)
    ori_img = cv2.cvtColor(ori_img, cv2.COLOR_BGR2RGB)
    ori_img = cv2.resize(ori_img, (512, 512))

    roi_img = []

    roi_number = 0
    contours, hier = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[0] + cv2.boundingRect(x)[1] * img.shape[1])
    for c in contours:
        # get the bounding rect
        x, y, w, h = cv2.boundingRect(c)
        if w > 40:
            # draw a white rectangle to visualize the bounding rect
            cv2.rectangle(ori_img, (x, y), (x + w, y + h), (36, 255, 12), 2)
            ROI = ori_img[y:y + h, x:x + w]
            roi_img.append(ROI)
            roi_number += 1

    if len(roi_img) > 1:
        nama = pytesseract.image_to_string(roi_img[0], lang='eng', config='--psm 7')
        jenis_kelamin = pytesseract.image_to_string(roi_img[1], lang='eng', config='--psm 7')
        verified = bool(True)

        response_json = {
            "name": nama,
            "gender": jenis_kelamin,
            "verified": verified
        }

        new_users = {
            "name": nama,
            "verified": verified
        }

        new_users_data = {
            "gender": jenis_kelamin,
            "verified": verified
        }

        db.reference("users").child(uid).update(new_users)
        db.reference("users_data").child(uid).update(new_users_data)

        return jsonify(response_json)

    # elif len(roi_img) == 1:
    #     text = pytesseract.image_to_string(roi_img[0], lang='eng', config='--psm 7')
    #     return "success"
    # else:
    #     return "success"
    # # return "Success"
#
# if __name__ == "__main__":
#     # app.run(host="localhost", debug=True)
#     app.run(debug=True, host="0.0.0.0")