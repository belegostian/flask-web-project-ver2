#__組態設定________________________________________________________________________
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask.globals import current_app
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_pymongo import PyMongo
from bson.objectid import ObjectId  #支援BSON格式
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField
from wtforms.validators import DataRequired, Email


app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'   #暫時固定密鑰，之後要改放環境變數

app.config["MONGO_URI"] = "mongodb://localhost:27017/Lab_Equipment_Management"    #指定DB
mongo = PyMongo(app)
#指定collection
User = mongo.db.User
Record = mongo.db.Record
Lab_Equ = mongo.db.Lab_Equipments

bootstrap = Bootstrap(app)  #支援前端排版
moment = Moment(app)    #時間本地化


#__表單類別________________________________________________________________________
class LogIn(FlaskForm):
    account = StringField('Account', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

class NewAccount(FlaskForm):    #之後可以加入重複輸入驗證；信箱/日期格式認證；自訂格式驗證
    account = StringField('Account', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    lab = StringField('Lab', validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired()])
    submit = SubmitField('Submit')

class UpDateAccount(FlaskForm):
    account = StringField('Account', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    lab = StringField('Lab', validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired()])
    submit = SubmitField('Submit')


class Rent(FlaskForm):
    date = StringField('歸還日期 (Ex.date-Month-year)', validators=[DataRequired()])
    submit = SubmitField('Submit')


#__普通路由___________________________________________________________________________
@app.route('/')
def index():
    filter1 = {'狀態':"可供使用"}  
    equ1 = Lab_Equ.find(filter1)
    filter2 = {'狀態':"已出借"}  
    equ2 = Lab_Equ.find(filter2)
    return render_template('index.html', equ1=equ1, equ2=equ2)


@app.route('/registrate', methods=['GET', 'POST'])    #註冊表單
def registrate():
    form = NewAccount()    #不能用名稱 "registrate()"，原因未知
    if form.validate_on_submit():
        session['account'] = form.account.data  #暫存記憶體
        #封包物件
        user = {'帳號':session.get('account'),'密碼':form.password.data,
                '聯絡人姓名':form.name.data,'聯絡人信箱':form.email.data,
                '實驗室':form.lab.data,'分機號碼':form.telephone.data}    
        User.insert_one(user)
        return redirect(url_for('index'))
    return render_template('registrate.html', form=form, account=session.get('account'))

@app.route('/login', methods=['GET', 'POST'])    #登入表單，登入後session儲存其帳戶與名稱
def login():
    form = LogIn()
    if form.validate_on_submit():
        session['account'] = form.account.data
        user = mongo.db.User.find_one({'帳號':session.get('account'),'密碼':form.password.data})
        if user:
            filter = {'帳號':session.get('account')}  
            user = User.find_one(filter)
            session['name'] = user['聯絡人姓名']
            flash('welcome back!' + user['聯絡人姓名'])
            return redirect(url_for('personal_index', name=user['聯絡人姓名']))
        else:
            flash('account or password error')
    return render_template('login.html', form=form, account=session.get('account'), password=session.get('password'))


#__監管者路由___________________________________________________________________________
@app.route('/userDB', methods=['GET', 'POST'])
def userDB():
    users = User.find()
    return render_template('userDB.html', context=users)


@app.route('/userDB_update/<id>',methods=['POST','GET'])
def userDB_update(id):
    filter = {'_id':ObjectId(id)}  
    user = User.find_one(filter)
    form = UpDateAccount()
    if form.validate_on_submit():
        update = {'$set':{'帳號':session.get('account'), '聯絡人姓名':form.name.data,
                '聯絡人信箱':form.email.data,'實驗室':form.lab.data,'分機號碼':form.telephone.data}}
        User.update_one(filter,update)
        return redirect(url_for('userDB'))
    return render_template('userDBform.html', form=form, context=user, account=user['帳號'])  #user['帳號']是為了後續可以在表單上添加默認答案


@app.route('/userDB_delete/<id>',methods=['POST','GET'])  #功能路由，無匹配的靜態網頁
def userDB_delete(id):
    filter = {'_id':ObjectId(id)}
    User.delete_one(filter)
    return redirect(url_for('userDB'))


@app.route('/rent/<id>',methods=['POST','GET'])  #功能路由，無匹配的靜態網頁(id為Lab_Equ DB的id)
def rent(id):
    form=Rent()
    if form.validate_on_submit():    #wtf quick form 不支援 date picker
        #更改財產狀態
        filter = {'_id':ObjectId(id)}
        equ=Lab_Equ.find_one(filter)
        equ_update = {'$set':{'狀態':"已出借"}}
        Lab_Equ.update_one(filter,equ_update)
        #產生租借紀錄(RECORD)
        date_obj = datetime.strptime(form.date.data, '%Y-%m-%d')    #詳細時間為當日0:00
        record = {'狀態':"租借中", '借用人':session.get('name'), '財物編號':equ['財物編號'], '財物名稱':equ['財物名稱']
                , '廠牌':equ['廠牌'], '型式':equ['型式'], '財物條碼':equ['財物條碼'], '租借日期':datetime.utcnow(), '歸還日期':date_obj}
        Record.insert_one(record)
        flash('sucessfully booked' + equ['財物名稱'])
    return redirect(url_for('personal_index', name=session.get('name')))


#__測試中路由___________________________________________________________________________
@app.route('/<name>')  #只是用以測試登入狀態，毫無資安可言
def personal_index(name):
    filter1 = {'狀態':"可供使用"}  
    equ1 = Lab_Equ.find(filter1)
    filter2 = {'狀態':"已出借"}  
    equ2 = Lab_Equ.find(filter2)
    form=Rent()
    return render_template('index.html', form=form, name=name, equ1=equ1, equ2=equ2)


@app.route('/record/<name>', methods=['GET', 'POST'])
def personal_record(name):
    filter1 = {'借用人':name, '歸還日期':{ "$gt": datetime.utcnow()}}  
    recent_record = Record.find(filter1)
    filter2 = {'借用人':name, '歸還日期':{ "$lt": datetime.utcnow()}}  
    passed_record = Record.find(filter2)
    return render_template('personalRecord.html', name=name, recent_record=recent_record,
                            passed_record=passed_record, current_time=datetime.utcnow())


#__錯誤處理路由___________________________________________________________________________
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
