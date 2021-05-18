#__組態設定________________________________________________________________________
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_pymongo import PyMongo
from bson.objectid import ObjectId  #支援BSON格式
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email


app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'   #暫時固定密鑰，之後要改放環境變數
app.config["MONGO_URI"] = "mongodb://localhost:27017/Lab_Equipment_Management"    #指定DB
mongo = PyMongo(app)

#指定collection
User = mongo.db.User
Record = mongo.db.Record
Lab_Equ = mongo.db.Lab_Equ

bootstrap = Bootstrap(app)  #支援前端排版
moment = Moment(app)    #時間本地化


#__表單類別________________________________________________________________________
class LogIn(FlaskForm):
    account = StringField('Account', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

class NewAccount(FlaskForm):    #之後可以加入重複輸入驗證；信箱格式認證；自訂格式驗證
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

#__路由___________________________________________________________________________
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registrate', methods=['GET', 'POST'])    #暫時性註冊表單URL
def Registrate():
    form = NewAccount()    #不能用名稱 "registrate"，原因未知
    if form.validate_on_submit():
        session['account'] = form.account.data
        session['password'] = form.password.data
        session['name'] = form.name.data
        session['email'] = form.email.data
        session['lab'] = form.lab.data
        session['telephone'] = form.telephone.data
        flash('data are saved to session!')     #瀏覽器暫存
        user = {'帳號':session.get('account'),'密碼':session.get('password'),
                '聯絡人姓名':session.get('name'),'聯絡人信箱':session.get('email'),
                '實驗室':session.get('lab'),'分機號碼':session.get('telephone')}    #封包物件
        User.insert_one(user)
        flash('data are saved to DB!')      #真正存入DB
        return redirect(url_for('index'))
    return render_template('registrate.html', form=form, account=session.get('account'), 
                            password=session.get('password'), name=session.get('name'), 
                            email=session.get('email'), lab=session.get('lab'), telephone=session.get('telephone'))

@app.route('/login', methods=['GET', 'POST'])    #暫時性登入表單URL
def login():
    form = LogIn()
    if form.validate_on_submit():
        session['account'] = form.account.data
        session['password'] = form.password.data
        user = mongo.db.User.find_one({'帳號':session.get('account'),'密碼':session.get('password')}) #不能使用find_one_or_404()
        if user:
            flash('welcome back!' + session.get('account'))
            return redirect(url_for('index'))
        else:
            flash('account or password error')
    return render_template('login.html', form=form, account=session.get('account'), password=session.get('password'))


####################################___test___####################################

@app.route('/userDB', methods=['GET', 'POST'])
def userDB():
    users = User.find()
    return render_template('userDB.html', context=users)


@app.route('/userDB/<id>',methods=['POST','GET'])
def userDB_update(id):
    filter = {'_id':ObjectId(id)}  
    user = User.find_one(filter)
    form = UpDateAccount()
    if form.validate_on_submit():
        session['account'] = form.account.data
        session['name'] = form.name.data
        session['email'] = form.email.data
        session['lab'] = form.lab.data
        session['telephone'] = form.telephone.data
        update = {'$set':{'帳號':session.get('account'), '聯絡人姓名':session.get('name'),
                '聯絡人信箱':session.get('email'),'實驗室':session.get('lab'),'分機號碼':session.get('telephone')}}
        User.update_one(filter,update)
        return redirect(url_for('userDB'))
    return render_template('userDBform.html', form=form, context=user, account=user['帳號'])  #嘗試使用 context 取代 session elements

####################################___test___####################################


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
