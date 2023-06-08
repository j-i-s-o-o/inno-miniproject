from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

from pymongo import MongoClient  
client = MongoClient('mongodb+srv://sparta:test@cluster0.vwirvwe.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta

@app.route('/')
def home():
   return render_template('index.html')

# db.QuestionBook{
#     'WriteID': id
#     'WriteNick': nick
#     'book': num
#     'Text': text
#     'Respo': db.QuestionBook.['book']
# }

# db.QuestionBook.['book']{
#     'WriteID': id
#     'WriteNick': nick
#     'Text': text
# }

@app.route("/questionbook", methods=["POST"])
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
    return jsonify({'msg': '질문 등록 완료!'})

@app.route("/questionbook", methods=["GET"])
def questionbook_get():
    all_comments = list(db.cheer.find({},{'_id':False}))
    return jsonify({'result': all_comments})

@app.route("/questionbook/modify", methods=["POST"])
def questionbook_modify():
    num_receive = request.form['num_give']
    comment_receive = request.form['comment_give']

    db.cheer.update_one({'num':int(num_receive)},{'$set':{'comment':comment_receive}})

    return jsonify({'msg': '질문 수정 완료!'})

@app.route("/questionbook/delete", methods=["POST"])
def questionbook_delete():
    num_receive = request.form['num_give']

    db.cheer.delete_one({'num':int(num_receive)})

    return jsonify({'msg': '질문 삭제 완료!'})

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)
