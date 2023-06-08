from flask import Flask, render_template, jsonify, session, redirect, url_for, request
import datetime, requests
app = Flask(__name__)

from pymongo import MongoClient
import certifi
ca=certifi.where()

client = MongoClient("mongodb+srv://sparta:test@cluster0.vd0bjci.mongodb.net/", tlsCAFile=ca)
# db = client.team3
db = client.test2

#################################
##  DB 기본 저장값              ##
#################################
USER_DB = db.user
INFO_DB = 'info'
DUMMY_DB = db.dummy
DB_ID = 'ID'
TEST_ID = "asdf"

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'threerow'

@app.route('/')
def home():
   return render_template("index.html")

@app.route('/rending')
def rending():
   return render_template("rending.html")

@app.route('/signup')
def signup():
   return render_template("signup.html")

@app.route('/info')
def info():
   return render_template("info.html")
# @app.route('/test_admin')
# def test_admin():
#    payload = {
#       'ID': TEST_ID,
#       'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
#    }
#    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
   
#    return jsonify({'result': 'success', 'token': token})

# [마이페이지 정보 확인 API]
# ID를 입력하면 있으면 success 없으면 fail 반환
@app.route('/api/userinfo_admin', methods=['GET'])
def api_mypage_admin():
    #token_receive = request.cookies.get('logintoken')

    #try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
       # payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
        userinfo = USER_DB[user['NickName']][INFO_DB].find_one()
        return jsonify({
            'result': 'success',
            'nickname': user['NickName'],
            'Image_url': userinfo['Image_url'],
            'Image_boolean': userinfo['Image_boolean'],
            'Hobby' : userinfo['Hobby'],
            'Hobby_boolean' : userinfo['Hobby_boolean'],
            'TIL_url' : userinfo['TIL_url'],
            'TIL_boolean' : userinfo['TIL_boolean']
            })
    #except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    #except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# [이미지 업로드]
# 
@app.route("/upload", methods=['POST'])
def upload():
    img = request.files['image']
    params = {
        'key': '14ec9aa021692985d8f4ea5ca92c172b',
    }

    files = {
        'image': img,
    }
    res = requests.post("https://api.imgbb.com/1/upload", params=params, files=files)
    print(res.status_code)
    print(res.json())
    json_object = res.json()
    print(json_object["data"]["url"])
    print(json_object["data"]["delete_url"])

    #token_receive = request.cookies.get('logintoken')
    #payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    db.user.admin.update_one({'ID': TEST_ID}, {'$set':{'Image_url': json_object["data"]["url"]}})

    return jsonify({'result' : "success"})

# 받아오는 법
# <form action="/upload" method="post" id="uploadForm" enctype="multipart/form-data">
#         <label>이미지 첨부</label>
#         <input type="file" name="image" class="form-control" placeholder="">
#         <input type="submit" class="btn btn-primary btn_location" value="Submit">
#     </form>

def refresh_info(nick, i_url, id_url, i_b, H, H_b, T, T_b) :
    del_info_of_image(nick)
    USER_DB[nick][INFO_DB].insert_one({
        'Image_url': i_url,
        'Image_delete_url': i_url,
        'Image_boolean' : i_b,
        'Hobby': H,
        'Hobby_boolean' : H_b,
        'TIL_url': T,
        'TIL_boolean': T_b
    })

def del_info_of_image(nick) :
    test = USER_DB['asdf'][INFO_DB].find_one()['Image_delete_url']
    DUMMY_DB['image'].insert_one({'Image_url' : test})
    USER_DB[nick][INFO_DB].drop()


# pw_give
# Image_url
# Image_boolean : true
# Hobby
# Hobby_boolean :
# TIL_url
# TIL_boolean :
    
# [마이페이지 정보 수정 API]
# token 있으면 DB삭제 후 재 생성 success : fail 반환
@app.route('/api/userinfo_change', methods=['POST'])
def api_mypage_change():
    # token_receive = request.cookies.get('logintoken')
    # try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        # payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # userinfo = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
    usernick = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})['NickName']
    pw_receive = request.form['pw_give']
    # Image_receive = request.files['Image']
    # print(Image_receive)
    # url_receive = upload_imageDB(Image_receive)
    url_receive = ["null", "null"]
    urlb_receive = request.form['Image_boolean']
    Hobby_receive = request.form['Hobby']
    Hobbyb_receive = request.form['Hobby_boolean']
    TIL_receive = request.form['TIL_url']
    TILb_receive = request.form['TIL_boolean']
    urlb_receive = True if urlb_receive == "on" else False
    Hobbyb_receive = True if Hobbyb_receive == "on" else False
    TILb_receive = True if TILb_receive == "on" else False
    refresh_info(usernick,url_receive[0],url_receive[1],urlb_receive,Hobby_receive,Hobbyb_receive,TIL_receive,TILb_receive)
    return jsonify({'result': 'success'})
    # except jwt.ExpiredSignatureError:
    #     # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
    #     return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    # except jwt.exceptions.DecodeError:
    #     return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

##################
# 부가 체크 함수

# [이미지 서버에 올리기]
def upload_imageDB(img):
    params = {
        'key': '14ec9aa021692985d8f4ea5ca92c172b',
    }
    files = {
        'image': img,
    }
    res = requests.post("https://api.imgbb.com/1/upload", params=params, files=files)
    json_object = res.json()
    print(json_object["data"]["url"])
    print(json_object["data"]["delete_url"])
    image_url_arr = [json_object["data"]["url"],json_object["data"]["delete_url"]]
    return image_url_arr


if __name__ == '__main__':  
   app.run('0.0.0.0',port=5000,debug=True)