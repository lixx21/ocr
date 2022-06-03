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
import smtplib
import ssl
import math
import random
from email.message import EmailMessage

app = Flask(__name__)

# pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

cred = credentials.Certificate("/home/m7364j2910/ocr-api/redmineKey.json")

model = tf.keras.models.load_model("/home/m7364j2910/ocr-api/bounding_box_segmentation_5.h5")
# model.summary()

firebase = firebase_admin.initialize_app(cred,
                                         {'databaseURL': 'https://redmine-350506-default-rtdb.asia-southeast1.firebasedatabase.app/'}
                                         )

root = db.reference()

@app.route("/ml-api/helloWorld")
def home():
    return "hello world"

@app.route("/ml-api/getOcr", methods=['POST'])
def predict():
    imagefile = request.files['imagefile']
    uid = request.form.get('uid')
    # image_path = "C:\\Users\\ASUS\\PycharmProjects\\bangkit_capstone\\test.jpg"
    image_path = "/home/m7364j2910/ocr-api/images/"+imagefile.filename
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
        name = pytesseract.image_to_string(roi_img[0], lang='eng', config='--psm 7')
        jenis_kelamin = pytesseract.image_to_string(roi_img[1], lang='eng', config='--psm 7')
        verified = bool(True)

        wrong_name = ["\n", "\f"]

        for i in range (len(wrong_name)) :
            if wrong_name[i] in name:
            new_name = name.strip(wrong_name[i])
        new_name = new_name.strip("\n")
        new_name = new_name.title()

        for i in range (len(wrong_name)) :
            if wrong_name[i] in jenis_kelamin:
            new_jenis_kelamin = jenis_kelamin.strip(wrong_name[i])
        new_jenis_kelamin = new_jenis_kelamin.strip("\n")

        if new_jenis_kelamin == "PEREMPUAN":
            new_jenis_kelamin = "female"
        elif new_jenis_kelamin == "LAKI-LAKI":
            new_jenis_kelamin = "male"
        else:
            new_jenis_kelamin = new_jenis_kelamin


        response_json = {
            "name": new_name,
            "gender": new_jenis_kelamin,
            "verified": verified
        }

        new_users = {
            "name": new_name,
            "verified": verified
        }

        new_users_data = {
            "gender": new_jenis_kelamin,
            "verified": verified
        }

        db.reference("users").child(uid).update(new_users)
        db.reference("users_data").child(uid).update(new_users_data)

        return jsonify(response_json)
      
@app.route('/ml-api/sendOtp', methods=['POST'])
def sendEmail():
    user_email = request.form.get("email")
    for string in user_email:
        if "." == string:
            db_email = user_email.replace(string, "")

    digits = "0123456789"
    otp = ""

    for i in range(6):
        otp += digits[math.floor(random.random() * 10)]

    subject = "REDMINE"
    call_otp = otp
    body = "Hello Redminers, \n\nAvoid scams! Do not give the OTP code to anyone. Redmine OTP code: {}.".format(
        call_otp)
    email_sender = "nararyanirankara@gmail.com"
    email_receiver = user_email
    password = "ognbgktfhkfcunra"

    message = EmailMessage()
    message["From"] = email_sender
    message["To"] = email_receiver
    message["Subject"] = subject

    html = f"""
    <html>
      <body>
        <h1>{subject}</h1>
        <p>{body}</p>
      </body>
    </html>
    """
    message.add_alternative(html, subtype="html")

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(email_sender, password)
        server.sendmail(email_sender, email_receiver, message.as_string())

        data = {"otpCode": call_otp}
        db.reference("otp_codes").child(db_email).set(data)

    email_response = {
        "otpCode": call_otp,
        "email": user_email,
        "databaseEmail": db_email

    }

    return jsonify(email_response)

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
