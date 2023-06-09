from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)

from pymongo import MongoClient
import certifi

ca=certifi.where()

client = MongoClient("mongodb+srv://sparta:test@cluster0.vd0bjci.mongodb.net/", tlsCAFile=ca)
db = client.test3

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'threerow'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib

import requests

import re

#################################
##  DB 기본 저장값              ##
#################################
USER_DB = db.user
INFO_DB = 'info'
TIMER_DB = 'timer'
GUEST_DB = 'guest'
DUMMY_DB = db.dummy
QUESTION_DB = db.QuestionBook
QUESTION_REPLY_DB = db.QuestionBook.Reply

DB_ID = 'ID'
DB_PW = 'PW'
DB_NICK = 'NickName'

ACCESS_TOKEN = 'row_login'
REFERSH_TOKEN = 'rs_row_login'

#################################
##  테스트 모듈                 ##
#################################

TEST_ID = "asdfg"
TEST_NICK = "김준우"

#################################
##  기본 저장 함수              ##
#################################
def change_pw(id, pw):
    match PWcheck(pw):
        case "alpa":
            return 'pw_alpa'
        case "len":
            return 'pw_len'
    
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    USER_DB.update_one({"ID" : id},{'$set' : {'PW' : pw_hash}})
    return 'pass'

def Search_ID(id):
    result = USER_DB.find_one({'ID': id})
    if result is not None:
        return True
    else:
        return False
    
def Search_Nick(nick):
    result = USER_DB.find_one({'NickName': nick})
    if result is not None:
        return True
    else:
        return False

def create_account(id, nick):
    create_info(id,nick)
    create_timer(id,nick)

def create_info(id,nick):
    USER_DB[INFO_DB].insert_one({
        'NickName':nick,
        'Image_url':'null',
        'Image_delete_url': 'null',
        'Image_boolean' : True,
        'Hobby':'',
        'Hobby_boolean' : True,
        'TIL_url':'',
        'TIL_boolean': True
    })

def create_timer(id, nick):
    USER_DB[TIMER_DB].insert_one({
        'NickName':nick,
        'CheckInTime': 0,
        'CheckOutTime': 0,
        'LessTime':0,
        'Flag':False,
        'TimerOn':False
    })

def refresh_info(nick, i_url, id_url, i_b, H, H_b, T, T_b) :
    if i_url != "null":
        del_info_of_image(nick)
    USER_DB[INFO_DB].insert_one({
        'NickName':nick,
        'Image_url': i_url,
        'Image_delete_url': id_url,
        'Image_boolean' : i_b,
        'Hobby': H,
        'Hobby_boolean' : H_b,
        'TIL_url': T,
        'TIL_boolean': T_b
    })
def refresh_info_Image(nick, i_url):
    del_info_of_image(nick)
    USER_DB[INFO_DB].update_one

def del_info_of_image(nick) :
    test = USER_DB[INFO_DB].find_one({'NickName' : nick})
    print()
    DUMMY_DB['image'].insert_one({'Image_url' : test})
    USER_DB[INFO_DB].drop()

def create_access_token(id):
    payload = {
            'ID': id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

#################################
##  HTML을 주는 부분            ##
#################################
@app.route('/')
def home():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = USER_DB.find_one({"ID": payload['ID']})
        if user_info is not None:
            return render_template('index.html')
    # 찾지 못하면
        else:
            return redirect(url_for("login", msg="로그인 정보가 일치하지 않습니다."))
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/logout')
def logout():
    render_template('logout.html')

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('rending.html', msg=msg)

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/mypage')
def mypage():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = USER_DB.find_one({"ID": payload['ID']})
        if user_info is not None:
            return render_template('info.html')
    # 찾지 못하면
        else:
            return redirect(url_for("login", msg="로그인 정보가 일치하지 않습니다."))
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/upload_homepage')
def upload_home():
    return render_template('upload.html')

#################################
##  로그인을 위한 API           ##
#################################

# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/register', methods=['POST'])
def api_register():
    print(request.headers)
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']

    if Search_ID(id_receive):
        return jsonify({'result': 'id_error'})
    match IDcheck(id_receive):
        case "alpa":
            return jsonify({'result': 'id_alpa'})
        case "len":
            return jsonify({'result': 'id_len'})
    if Search_Nick(nickname_receive):
        return jsonify({'result': 'nick_error'})
    match NICKcheck(nickname_receive):
        case "alpa":
            return jsonify({'result': 'nick_alpa'})
        case "len":
            return jsonify({'result': 'nick_len'})
    match PWcheck(pw_receive):
        case "alpa":
            return jsonify({'result': 'pw_alpa'})
        case "len":
            return jsonify({'result': 'pw_len'})
    
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    USER_DB.insert_one({'ID': id_receive, 'PW': pw_hash, 'NickName': nickname_receive})
    create_account(id_receive, nickname_receive)

    return jsonify({'result': 'success'})

##################
# 부가 체크 함수

# 아이디, 닉네임 중복
def IDcheck(id) :
    if len(re.findall(r'[^a-z0-9]+',id)) > 0 :
        return "alpa"
    elif len(id) < 5 :
        return "len"
    else :
        return "pass"
    
def NICKcheck(nick) :
    if len(re.findall(r'[^a-zA-Zㄱ-ㅎㅏ-ㅣ가-힣0-9]+',nick)) > 0 :
        return "alpa"
    elif korlen(nick) < 5 :
        return "len"
    else :
        return "pass"
    
def korlen(str):
    temp = re.findall(r'[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]+', str)
    temp_len = 0
    for item in temp:
        temp_len = temp_len + len(item)
    return len(str) + temp_len

# 비밀번호 여부
def PWcheck(pw):
    if len(re.findall(r'[^a-z0-9]+',pw)) > 0:
        return "alpa"
    if len(pw) < 8 :
        return "len"
    elif len(pw) > 12:
        return "len"
    else:
        return "pass"


# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = USER_DB.find_one({'ID': id_receive, 'PW': pw_hash})

    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'ID': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        # token을 줍니다.
        return jsonify({'result': 'success', 'token_name': ACCESS_TOKEN, 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

# [로그인 확인 API]
# 로그인된 유저만 call 할 수 있는 API입니다.
# 유효한 토큰을 줘야 올바른 결과를 얻어갈 수 있습니다.
# (그렇지 않으면 남의 장바구니라든가, 정보를 누구나 볼 수 있겠죠?)
@app.route('/api/login_check', methods=['GET'])
def api_login_check():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        return jsonify({'result': 'success', 'nickname': userinfo['NickName']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# [Token Text API]
# 로그인된 유저만 call 할 수 있는 API입니다.
# 유효한 토큰을 줘야 올바른 결과를 얻어갈 수 있습니다.
# (그렇지 않으면 남의 장바구니라든가, 정보를 누구나 볼 수 있겠죠?)
@app.route('/api/read_token_name', methods=['GET']) # CRACKED
def read_token_name():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        return jsonify({'result': 'success', 'NickName': userinfo['NickName']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# [유저 정보 확인 API]
# 로그인된 유저만 call 할 수 있는 API입니다.
# 유효한 토큰을 줘야 올바른 결과를 얻어갈 수 있습니다.
# (그렇지 않으면 남의 장바구니라든가, 정보를 누구나 볼 수 있겠죠?)
@app.route('/api/nick', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        return jsonify({'result': 'success', 'nickname': userinfo['NickName']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})



# [아이디 정보 확인 API]
# ID를 입력하면 있으면 success 없으면 fail 반환
@app.route('/api/id_check', methods=['POST'])
def api_id_check():
    id_receive = request.form['id_give']

    # user에 해당 id가 존재하는 지 확인
    result = Search_ID(id_receive)

    # 찾으면 true
    if result:
        return jsonify({'result': 'success'})
    # 찾지 못하면 false
    else:
        return jsonify({'result': 'fail'})
    
    
# [닉네임 정보 확인 API]
# ID를 입력하면 있으면 success 없으면 fail 반환
@app.route('/api/nick_check', methods=['POST'])
def api_nick_check():
    nickname_receive = request.form['nickname_give']

    # user에 해당 nick 존재하는 지 확인
    result = Search_Nick(nickname_receive)

    # 찾으면 true
    if result:
        # PW창 활성화
        return jsonify({'result': 'success'})
    # 찾지 못하면 false
    else:
        return jsonify({'result': 'fail'})
    
# [가입자 정보 확인 API]
# GET {result : success ? fail, member_list : USER_DB}
@app.route('/api/member', methods=['GET'])
def api_membercard():
    userlist = list(USER_DB.find({}, {'_id': False}))
    resultlist = []
    for e in userlist:
        resultlist.append({
            'ID' : e['ID'],
            'NickName': e['NickName']
        })
    return jsonify({'result': 'success', 'member_list': resultlist})

# [사용자 정보 확인 API]
# ID를 입력하면 있으면 success 없으면 fail 반환
@app.route('/api/userinfo', methods=['GET'])
def api_mypage():
    nickname_receive = request.args.get('user')

    userinfo = USER_DB[INFO_DB].find_one({'NickName':nickname_receive}, {'_id': False})
    if userinfo is not None:
        image = "null"
        hobby = "비공개"
        TIL_link = "비공개"
        if userinfo['Image_boolean']:
            image = userinfo['Image_url']
        if userinfo['Hobby_boolean']:
            hobby = userinfo['Hobby']
        if userinfo['TIL_boolean']:
            TIL_link = userinfo['TIL_url']
        doc = {
            'NickName': nickname_receive,
            'Image_url': image,
            'Hobby' : hobby,
            'TIL_url' : TIL_link
        }
        return jsonify({
            'result': 'success',
            'info_list' : doc
        })
    else:
        return jsonify({'result': 'fail', 'msg': '해당 사용자 정보가 없습니다.'})


#################################
##         mypage API          ##
#################################

# [마이페이지 정보 확인 API]
# [all]
@app.route('/api/mypage', methods=['GET'])
def api_mypage_admin():
    token_receive = request.cookies.get(ACCESS_TOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        user = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        userinfo = USER_DB[INFO_DB].find_one({'NickName' : user['NickName']}, {'_id': False})
        return jsonify({
            'result': 'success',
            'NickName': user['NickName'],
            'Image_url': userinfo['Image_url'],
            'Image_boolean': userinfo['Image_boolean'],
            'Hobby' : userinfo['Hobby'],
            'Hobby_boolean' : userinfo['Hobby_boolean'],
            'TIL_url' : userinfo['TIL_url'],
            'TIL_boolean' : userinfo['TIL_boolean']
            })
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# [all_change] #CRACKED
@app.route('/api/mypage', methods=['POST'])
def api_mypage_change():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        usernick = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})['NickName']
        pw_receive = request.form['pw_give']
        print(pw_receive)
        if pw_receive != "null":
            match change_pw(TEST_ID, pw_receive):
                case 'pw_alpa':
                    return jsonify({'result': 'fail', 'msg': 'pw_alpa'})
                case 'pw_len':
                    return jsonify({'result': 'fail', 'msg': 'pw_len'})
        try:
            Image_receive = request.files['Image']
            if Image_receive is not None:
                url_receive = upload_imageDB(Image_receive)
            else:
                url_receive = ["null","null"]
            urlb_receive = request.form['Image_boolean']
            Hobby_receive = request.form['Hobby']   
            Hobbyb_receive = request.form['Hobby_boolean']
            TIL_receive = request.form['TIL_url']
            TILb_receive = request.form['TIL_boolean']
            refresh_info(usernick,url_receive[0],url_receive[1],urlb_receive,Hobby_receive,Hobbyb_receive,TIL_receive,TILb_receive)
            return jsonify({'result': 'success'})
        except Exception as e:
            url_receive = ["null","null"]
            urlb_receive = request.form['Image_boolean']
            Hobby_receive = request.form['Hobby']
            Hobbyb_receive = request.form['Hobby_boolean']
            TIL_receive = request.form['TIL_url']
            TILb_receive = request.form['TIL_boolean']
            print(usernick,url_receive[0],url_receive[1],urlb_receive,Hobby_receive,Hobbyb_receive,TIL_receive,TILb_receive)
            refresh_info(usernick,url_receive[0],url_receive[1],urlb_receive,Hobby_receive,Hobbyb_receive,TIL_receive,TILb_receive)
            return jsonify({'result': 'fail'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# [image upload API]
# POST {Image} => USER_DB[INFO_DB]{user['NickName']} {Image_url, Image_delete_url} 
@app.route('/api/mypage/Image', methods=['POST'])
def api_mypage_change_Image():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        usernick = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})['NickName']
        Image_receive = request.files['Image']
        if Image_receive is not None:
            url_receive = upload_imageDB(Image_receive)
            USER_DB[INFO_DB].update_one({'NickName':usernick},{'$set':{'Image_url': url_receive[0], 'Image_delete_url': url_receive[1]}})
            return jsonify({'result': 'success'})
        else:
            return jsonify({'result': 'fail'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
# [Other upload API]
# POST {Image_boolean,Hobby,Hobby_boolean,TIL_url,TIL_boolean} => USER_DB[INFO_DB]{user['NickName']} {Image_url, Image_delete_url} 
@app.route('/api/mypage/Other', methods=['POST'])
def api_mypage_change_Other():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        usernick = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})['NickName']
        urlb_receive = request.form['Image_boolean']
        Hobby_receive = request.form['Hobby']
        Hobbyb_receive = request.form['Hobby_boolean']
        TIL_receive = request.form['TIL_url']
        TILb_receive = request.form['TIL_boolean']
        USER_DB[INFO_DB].update_one({'NickName':usernick},{'$set':{
            'Image_boolean': changefrom_str_bool(urlb_receive),
            'Hobby': Hobby_receive,
            'Hobby_boolean': changefrom_str_bool(Hobbyb_receive),
            'TIL_url': TIL_receive,
            'TIL_boolean': changefrom_str_bool(TILb_receive)
        }})
        return jsonify({'result': 'success'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

# [Password upload API]
# POST {pw_receive} => USER_DB{tokenID} {'PW'} 
@app.route('/api/mypage/password', methods=['POST'])
def api_mypage_change_password():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        pw_receive = request.form['pw_give']
        match PWcheck(pw_receive):
            case "alpa":
                return jsonify({'result': 'pw_alpa'})
            case "len":
                return jsonify({'result': 'pw_len'})
        pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
        USER_DB.update_one({'ID': payload['ID']}, {'$set':{'PW' : pw_hash}})
        return jsonify({'result': 'success'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
# [Password upload API]
# POST {pw_receive} => USER_DB{tokenID} {'NickName'} 
@app.route('/api/mypage/nick', methods=['POST'])
def api_mypage_change_nick():
    token_receive = request.cookies.get(ACCESS_TOKEN)
    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        
        nickname_receive = request.form['nickname_give']
        usernick = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})['NickName']

        if Search_Nick(nickname_receive):
            return jsonify({'result': 'nick_error'})
        match NICKcheck(nickname_receive):
            case "alpa":
                return jsonify({'result': 'nick_alpa'})
            case "len":
                return jsonify({'result': 'nick_len'})
        nick_data_change(usernick, nickname_receive)
        return jsonify({'result': 'success'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

##################
# mypage sub fuc

# [DB_nick_change] # HALF
def nick_data_change(oldnick, nick):
    USER_DB.update_one({'NickName':oldnick}, {'$set':{'NickName':nick}})
    USER_DB[INFO_DB].update_one({'NickName':oldnick}, {'$set':{'NickName':nick}})
    USER_DB[TIMER_DB].update_one({'NickName':oldnick}, {'$set':{'NickName':nick}})
    #guestupdate

# [upload_imageDB]
# return [ image_src, del_image_src ]
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

def changefrom_str_bool(str):
    return True if str == "true" else False



# # [마이페이지 정보 수정 API] ########################################################## [Debug]
# # [all]
# @app.route('/api/userinfo_change_Debug', methods=['POST'])
# def api_mypage_change_Debug():
#     usernick = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})['NickName']
#     pw_receive = request.form['pw_give']
#     print(pw_receive)
#     if pw_receive != "null":
#         match change_pw(TEST_ID, pw_receive):
#             case 'pw_alpa':
#                 return jsonify({'result': 'fail', 'msg': 'pw_alpa'})
#             case 'pw_len':
#                 return jsonify({'result': 'fail', 'msg': 'pw_len'})
#     try:
#         Image_receive = request.files['Image']
#         if Image_receive is not None:
#             url_receive = upload_imageDB(Image_receive)
#         else:
#             url_receive = ["null","null"]
#         urlb_receive = request.form['Image_boolean']
#         Hobby_receive = request.form['Hobby']
#         Hobbyb_receive = request.form['Hobby_boolean']
#         TIL_receive = request.form['TIL_url']
#         TILb_receive = request.form['TIL_boolean']
#         refresh_info(usernick,url_receive[0],url_receive[1],urlb_receive,Hobby_receive,Hobbyb_receive,TIL_receive,TILb_receive)
#         return jsonify({'result': 'success'})
#     except Exception as e:
#         url_receive = ["null","null"]
#         urlb_receive = request.form['Image_boolean']
#         Hobby_receive = request.form['Hobby']
#         Hobbyb_receive = request.form['Hobby_boolean']
#         TIL_receive = request.form['TIL_url']
#         TILb_receive = request.form['TIL_boolean']
#         print(usernick,url_receive[0],url_receive[1],urlb_receive,Hobby_receive,Hobbyb_receive,TIL_receive,TILb_receive)
#         refresh_info(usernick,url_receive[0],url_receive[1],urlb_receive,Hobby_receive,Hobbyb_receive,TIL_receive,TILb_receive)
#         return jsonify({'result': 'fail'})

# # [image upload API]
# # POST {Image} => USER_DB[INFO_DB]{user['NickName']} {Image_url, Image_delete_url} 
# @app.route('/api/userinfo_change/Image_Debug', methods=['POST'])
# def api_mypage_change_Image_Debug():
#     usernick = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})['NickName']
#     Image_receive = request.files['Image']
#     if Image_receive is not None:
#         url_receive = upload_imageDB(Image_receive)
#         USER_DB[INFO_DB].update_one({'NickName':usernick},{'$set':{'Image_url': Image_receive[0], 'Image_delete_url': Image_receive[1]}})
#         return jsonify({'result': 'success'})
#     else:
#         return jsonify({'result': 'fail'})
    
# # [Other upload API]
# # POST {Image_boolean,Hobby,Hobby_boolean,TIL_url,TIL_boolean} => USER_DB[INFO_DB]{user['NickName']} {Image_url, Image_delete_url} 
# @app.route('/api/userinfo_change/Other_Debug', methods=['POST'])
# def api_mypage_change_Other_Debug():
#     usernick = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})['NickName']
#     urlb_receive = request.form['Image_boolean']
#     Hobby_receive = request.form['Hobby']
#     Hobbyb_receive = request.form['Hobby_boolean']
#     TIL_receive = request.form['TIL_url']
#     TILb_receive = request.form['TIL_boolean']
#     USER_DB[INFO_DB].update_one({'NickName':usernick},{'$set':
#         {'Image_boolean': urlb_receive,
#           'Hobby': Hobby_receive,
#           'Hobby_boolean':Hobbyb_receive,
#           'TIL_url':TIL_receive,
#           'TIL_boolean':TILb_receive
#     }})
#     return jsonify({'result': 'success'})

#################################
##         Timer API           ##
#################################

# [read_timer]
@app.route('/api/time/read_timer', methods=['GET']) 
def api_timer_read_timer():

    usertimer = list(USER_DB[TIMER_DB].find({}, {'_id': False}))
    if len(usertimer) > 0:
        return jsonify({'result': 'success', 'Timer': usertimer})
    else:
        return jsonify({'result': 'fail'})
    
# [checkin]
# POST {'CheckInTime'} => USER_DB[TIMER_DB]{user['NickName']}['CheckInTime'] = CheckInTime
@app.route('/api/time/checkin', methods=['POST'])
def api_timer_checkin():
    token_receive = request.cookies.get(ACCESS_TOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.

        user = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        if user is None:
            return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
        time = request.form['CheckInTime']
        print(time)
        usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
        if usertimer is not None:
            print("checkin,post")
            USER_DB[TIMER_DB].update_one({'NickName': user['NickName']}, {'$set':{'CheckInTime':time, 'Flag':True}})
            return jsonify({'result': 'success'})
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

    
# [read_checkin_time]
# GET {'CheckInTime'} <= USER_DB[TIMER_DB]{user['NickName']}['CheckInTime']
@app.route('/api/time/checkin', methods=['GET'])
def api_timer_read_checkin_time():
    token_receive = request.cookies.get(ACCESS_TOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        user = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
        if usertimer is not None:
            return jsonify({'result': 'success', 'CheckInTime': usertimer['CheckInTime'], 'Flag' : usertimer['Flag']})
        else:
            usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
            return jsonify({'result': 'success', 'CheckInTime': usertimer['CheckInTime'], 'Flag' : usertimer['Flag']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
# [checkout]
# POST {'CheckOutTime'} => USER_DB[TIMER_DB]{user['NickName']}['CheckOutTime'] = CheckOutTime
@app.route('/api/time/checkout', methods=['POST'])
def api_timer_checkout():
    token_receive = request.cookies.get(ACCESS_TOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        user = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        if user is None:
            return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
        time = request.form['CheckOutTime']
        print(time)
        usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
        if usertimer is not None:
            setTime = int(usertimer['LessTime']) + int(time) - int(usertimer['CheckInTime'])
            print(setTime)
            print("checkout,post")
            USER_DB[TIMER_DB].update_one({'NickName': user['NickName']}, {'$set':{'CheckInTime':0, 'CheckOutTime':0, 'LessTime':setTime, 'Flag': False}})
            return jsonify({'result': 'success'})
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
# [read_checkout_time]
# GET {'CheckInTime'} <= USER_DB[TIMER_DB]{user['NickName']}['CheckInTime']
@app.route('/api/time/checkout', methods=['GET'])
def api_timer_read_checkout_time():
    token_receive = request.cookies.get(ACCESS_TOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        user = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
        if usertimer is not None:
            return jsonify({'result': 'success', 'CheckOutTime': usertimer['CheckOutTime'], 'Flag' : usertimer['Flag']})
        else:
            usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
            return jsonify({'result': 'success', 'CheckOutTime': usertimer['CheckOutTime'], 'Flag' : usertimer['Flag']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
@app.route('/api/time/lesstime', methods=['GET'])
def api_timer_read_lesstime():
    token_receive = request.cookies.get(ACCESS_TOKEN)

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        user = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
        usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
        if usertimer is not None:
            return jsonify({'result': 'success', 'LessTime': usertimer['LessTime'], 'Flag' : usertimer['Flag']})
        else:
            usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
            return jsonify({'result': 'success', 'LessTime': usertimer['LessTime'], 'Flag' : usertimer['Flag']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
# db.user.['NickName'].timer{
#     'NickName':nick,
#     'CheckInTime': 0,
#     'CheckOutTime': 0,
#     'LessTime':0,
#     'Flag':false,
#     'TimerOn':false
# }

# [타이머 API Debug] ################################################################## [Debug]
# [read_timer]
# GET {list Timer} <= USER_DB[TIMER_DB]{[user['NickName']]}
# @app.route('/api/time/read_timer_debug', methods=['GET']) 
# def api_timer_read_timer_Debug():

#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     usertimer = list(USER_DB[TIMER_DB].find({'NickName':user['NickName']}, {'_id': False}))
#     print(len(usertimer))
#     if len(usertimer) > 0:
#         return jsonify({'result': 'success', 'Timer': usertimer})
#     else:
#         return jsonify({'result': 'fail'})
    
# # [checkin]
# # POST {'CheckInTime'} => USER_DB[TIMER_DB]{[user['NickName']]}['CheckInTime'] = CheckInTime
# @app.route('/api/time/checkin_debug', methods=['POST'])
# def api_timer_checkin_Debug():

#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     if user is None:
#         return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
#     time = request.form['CheckInTime']
#     usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#     if usertimer is not None:
#         USER_DB[TIMER_DB].update_one({'NickName': user['NickName']}, {'$set':{'CheckInTime':time}})
#         return jsonify({'result': 'success'})
#     return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})

# # [checkout]
# # POST {'CheckOutTime'} => USER_DB[TIMER_DB]{[user['NickName']]}['CheckOutTime'] = CheckOutTime
# @app.route('/api/time/checkout_debug', methods=['POST'])
# def api_timer_checkout_Debug():

#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     if user is None:
#         return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
#     time = request.form['CheckOutTime']
#     usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#     if usertimer is not None:
#         USER_DB[TIMER_DB].update_one({'NickName': user['NickName']}, {'$set':{'CheckOutTime':time}})
#         return jsonify({'result': 'success'})
#     return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})

# # [read_checkin_time]
# # GET {'CheckInTime'} <= USER_DB[TIMER_DB]{[user['NickName']]}['CheckInTime']
# @app.route('/api/time/checkin_debug', methods=['GET'])
# def api_timer_read_checkin_time_Debug():

#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#     if usertimer is not None:
#         return jsonify({'result': 'success', 'CheckInTime': usertimer['CheckInTime'], 'Flag' : usertimer['Flag']})
#     else:
#         usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#         return jsonify({'result': 'success', 'CheckInTime': usertimer['CheckInTime']})
    
# # [read_checkout_time]
# # POST {'CheckInTime'} => USER_DB[TIMER_DB]{[user['NickName']]}['CheckInTime'] = CheckInTime
# @app.route('/api/time/checkout_debug', methods=['GET'])
# def api_timer_read_checkout_time_Debug():

#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#     if usertimer is not None:
#         return jsonify({'result': 'success', 'CheckOutTime': usertimer['CheckOutTime'], 'Flag' : usertimer['Flag']})
#     else:
#         usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#         return jsonify({'result': 'success', 'CheckOutTime': usertimer['CheckOutTime'], 'Flag' : usertimer['Flag']})

# @app.route('/api/time/pause', methods=['POST'])
# def api_timer_pause_Debug():

#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     if user is None:
#         return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
#     time = request.form['PauseTime']
#     usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#     if usertimer is not None:
#         if usertimer['TimerOn']:
#             USER_DB[TIMER_DB].update_one({'NickName': user['NickName']}, {'$set':{'LessTime': time, 'PauseTime':0, 'TimerOn' : False}})
#             return jsonify({'result': 'success'})
#         else :
#             USER_DB[TIMER_DB].update_one({'NickName': user['NickName']}, {'$set':{'PauseTime': time, 'TimerOn' : True}})
#             return jsonify({'result': 'success'})
#     return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})

# @app.route('/api/time/pause', methods=['GET'])
# def api_timer_read_pause_time_Debug():

#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#     if usertimer is not None:
#         return jsonify({'result': 'success', 'PauseTime': usertimer['PauseTime'], 'LessTime': usertimer['LessTime'], 'TimerOn' : usertimer['TimerOn']})
#     else:
#         usertimer = USER_DB[TIMER_DB].find_one({'NickName':user['NickName']}, {'_id': False})
#         return jsonify({'result': 'success', 'PauseTime': usertimer['PauseTime'], 'LessTime': usertimer['LessTime'], 'TimerOn' : usertimer['TimerOn']})
    
# db.QuestionBook{
#     'WriteID': id
#     'WriteNick': nick
#     'book': num
#     'Text': text
#     'Respo': db.QuestionBook.['book']
# }

# [질문방 API] ########################################################## [Debug]
# [Question add]

# @app.route('/api/Question_Debug/add', methods=['POST'])
# def api_Question_add_Debug():
#     user = USER_DB.find_one({'ID': TEST_ID}, {'_id': 0})
#     all_comments = list(QUESTION_DB.find({}, {'_id': False}))
    
#     comment_receive = request.form['comment_give']
#     print(comment_receive)

#     count = len(all_comments) + 1
#     doc = {
#         'WriteID': TEST_ID,
#         'WriteNick': user[DB_NICK],
#         'book':count, 
#         'Text':comment_receive
#     }
#     QUESTION_DB.insert_one(doc)
#     return jsonify({'result': 'success'})

# # [Question Load]
# @app.route('/api/Question_Debug/Load', methods=['GET'])
# def api_Question_Load_Debug():
#     all_comments = list(QUESTION_DB.find({}, {'_id': False}))
    
#     return jsonify({'result': 'success', 'comment': all_comments, 'getID' : TEST_ID})

# # [Question Remove]
# @app.route('/api/Question_Debug/Remove', methods=['POST'])
# def api_Question_Remove_Debug():
#     num = request.form['num_give']
#     commentL = QUESTION_DB.find_one({'book':int(num)})
#     if commentL['WriteID'] == TEST_ID:
#         QUESTION_DB.delete_one({'book':int(num)})
#         DB_sort()
#         return jsonify({'result': 'success'})
#     else:
#         return jsonify({'result': 'fail', 'msg' : "non-correct ID"})


##################
# Question Sub fuc

def DB_sort():
    all_comments = list(QUESTION_DB.find({}, {'_id': False}))
    if len(all_comments) > 0:
        num = 1
        QUESTION_DB.drop()
        for c in all_comments:
            QUESTION_DB.insert_one({
            'WriteID': c['WriteID'],
            'WriteNick': c['WriteNick'],
            'book':num, 
            'Text':c['Text']
            }) 
            num = num + 1

# 추가 서버 명령어

# [Test Command]
#
# @app.route('/test/LoadinfoDB', methods=['GET'])
# def testdebug_database_info():
#     nickname_receive = request.args.get('user')
#     print(nickname_receive)
#     temp = list(USER_DB[INFO_DB].find({'NickName' : nickname_receive}, {'_id': False}))
#     return jsonify({'result': temp })

# @app.route('/test/test2', methods=['GET'])
# def testdebug_test2():
#     test = USER_DB['asdf'][INFO_DB].find_one()['Image_delete_url']
#     return jsonify({'result': test})

# @app.route('/test/test3', methods=['POST'])
# def testdebug_test3():
#     nickname_receive = request.form['nickname_give']
#     userinfo = USER_DB[INFO_DB].find_one({'NickName' : nickname_receive}, {'_id': False})
#     print(userinfo)
#     return jsonify({'result': "success"})

# @app.route('/gettoken', methods=['GET'])
# def testdebug_getToken():
#     id_receive = request.args.get('user')
#     payload = {
#             'ID': id_receive,
#         }
#     token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
#     return jsonify({'result': 'success', 'token_name': ACCESS_TOKEN, 'token': token});


# @app.route('/testtoken', methods=['GET'])
# def testdebug_testToken():
#     token_receive = request.cookies.get(ACCESS_TOKEN)
#     payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#     userinfo = USER_DB.find_one({'ID': payload['ID']}, {'_id': 0})
#     return jsonify({'result': userinfo})




# [이미지 업로드]
# 
# @app.route("/upload", methods=['POST'])
# def upload():
#     img = request.files['image']
#     params = {
#         'key': '14ec9aa021692985d8f4ea5ca92c172b',
#     }

#     files = {
#         'image': img,
#     }
#     res = requests.post("https://api.imgbb.com/1/upload", params=params, files=files)
#     print(res.status_code)
#     print(res.json())
#     json_object = res.json()
#     print(json_object["data"]["url"])
#     print(json_object["data"]["delete_url"])

#     token_receive = request.cookies.get(ACCESS_TOKEN)
#     payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#     USER_DB.admin.update_one({'ID': payload['ID']}, {'$set':{'Image_url': json_object["data"]["url"]}})

#     return render_template('upload.html')

# 받아오는 법
# <form action="/upload" method="post" id="uploadForm" enctype="multipart/form-data">
#         <label>이미지 첨부</label>
#         <input type="file" name="image" class="form-control" placeholder="">
#         <input type="submit" class="btn btn-primary btn_location" value="Submit">
#     </form>

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)