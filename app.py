from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

from pymongo import MongoClient  
client = MongoClient('mongodb+srv://sparta:test@cluster0.vwirvwe.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta

@app.route('/')
def home():
   return render_template('index.html')

@app.route("/guestbook", methods=["POST"])
def guestbook_post():
    name_receive = request.form['name_give']
    comment_receive = request.form['comment_give']

    all_comments = list(db.cheer.find({}, {'_id': False}))
    count = len(all_comments) + 1
    doc = {
        'num':count, 
        'name':name_receive,
        'comment':comment_receive,
    }
    db.cheer.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})

@app.route("/guestbook", methods=["GET"])
def guestbook_get():
    all_comments = list(db.cheer.find({},{'_id':False}))
    return jsonify({'result': all_comments})

@app.route("/guestbook/delete", methods=["POST"])
def guestbook_delete():
    num_receive = request.form['num_give']

    db.cheer.delete_one({'num':int(num_receive)})

    return jsonify({'msg': '삭제 완료!'})

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)
