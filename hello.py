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
#之後可以加入重複輸入驗證；信箱/日期/數字格式認證；自訂格式驗證
class LogIn(FlaskForm):
    account = StringField('Account', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

class NewAccount(FlaskForm):
    account = StringField('Account', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    lab = StringField('Lab', validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired()])
    submit = SubmitField('Submit')

class UpDateUserDB(FlaskForm):    #密碼不可更改
    account = StringField('Account', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    lab = StringField('Lab', validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired()])
    submit = SubmitField('Submit')


class UpDateLab_EquDB(FlaskForm): 
    serial_number = StringField('Serial number', validators=[DataRequired()])
    school_number = StringField('School number', validators=[DataRequired()])
    attachment = StringField('Attachment', validators=[DataRequired()])
    property_name = StringField('Property name', validators=[DataRequired()])
    label = StringField('Label', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    increase_order_number = StringField('Increase order number', validators=[DataRequired()])
    acquired_date = StringField('Acquired date', validators=[DataRequired()])
    age_limit = StringField('Age limit', validators=[DataRequired()])
    administrator = StringField('Administrator', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    custody_group_remarks = StringField('Custody Group Remarks', validators=[DataRequired()])
    reimbursement = StringField('Reimbursement', validators=[DataRequired()])
    bar_code = StringField('Bar code', validators=[DataRequired()])
    status = StringField('Status', validators=[DataRequired()])
    submit = SubmitField('Submit')


class Rent(FlaskForm):
    date = StringField('歸還日期', validators=[DataRequired()])
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
    return render_template('login.html', form=form, account=session.get('account'))


#__監管者路由___________________________________________________________________________
#呈現資料庫資料
@app.route('/userDB')
def userDB():
    users = User.find()
    return render_template('userDB.html', context=users)


@app.route('/recordDB')
def recordDB():
    records = Record.find()
    return render_template('recordDB.html', context=records)


@app.route('/lab_equDB')
def lab_equDB():
    lab_equs = Lab_Equ.find()
    return render_template('lab_equDB.html', context=lab_equs)


#資料庫更新表單 (紀錄不可更改)
@app.route('/userDB_update/<id>',methods=['POST','GET'])
def userDB_update(id):
    filter = {'_id':ObjectId(id)}  
    user = User.find_one(filter)
    form = UpDateUserDB()
    if form.validate_on_submit():
        update = {'$set':{'帳號':form.account.data, '聯絡人姓名':form.name.data,
                '聯絡人信箱':form.email.data,'實驗室':form.lab.data,'分機號碼':form.telephone.data}}
        User.update_one(filter,update)
        return redirect(url_for('userDB'))
    return render_template('userDBform.html', form=form, context=user, account=user['帳號'])  #user['帳號']是為了後續可以在表單上添加默認答案


@app.route('/lab_equDB_update/<id>',methods=['POST','GET'])
def lab_equDB_update(id):
    filter = {'_id':ObjectId(id)}  
    lab_equ = Lab_Equ.find_one(filter)
    form = UpDateLab_EquDB()
    if form.validate_on_submit():
        update = {'$set':{'財物編號':form.serial_number.data, '校號':form.school_number.data, '附件':form.attachment.data,
                '財物名稱':form.property_name.data,'廠牌':form.label.data,'型式':form.type.data,
                '單價':form.price.data,'增加單號':form.increase_order_number.data,'取得日期':form.acquired_date.data,
                '年限':form.age_limit.data,'管理人':form.administrator.data,'存置地點':form.location.data,
                '保管組備註':form.custody_group_remarks.data,'報銷狀態':form.reimbursement.data,'財物條碼':form.bar_code.data,
                '狀態':form.status.data}}
        lab_equ.update_one(filter,update)
        return redirect(url_for('lab_equDB'))
    return render_template('lab_equDBform.html', form=form, context=lab_equ)


#刪除單筆資料 (功能路由，無匹配的靜態網頁)
@app.route('/userDB_delete/<id>')
def userDB_delete(id):
    filter = {'_id':ObjectId(id)}
    User.delete_one(filter)
    return redirect(url_for('userDB'))

@app.route('/recordDB_delete/<id>')
def recordDB_delete(id):
    filter = {'_id':ObjectId(id)}
    Record.delete_one(filter)
    return redirect(url_for('recordDB'))

@app.route('/lab_equDB_delete/<id>')
def lab_equDB_delete(id):
    filter = {'_id':ObjectId(id)}
    Lab_Equ.delete_one(filter)
    return redirect(url_for('lab_equDB'))





#__個人動態路由(測試中)___________________________________________________________________________
#以下試為了測試個人動態路由能成功運作，沒有保護資料的措施，資安性極低
@app.route('/<name>')
def personal_index(name):
    filter1 = {'狀態':"可供使用"}  
    equ1 = Lab_Equ.find(filter1)
    filter2 = {'狀態':"已出借"}  
    equ2 = Lab_Equ.find(filter2)
    form=Rent()
    return render_template('index.html', form=form, name=name, equ1=equ1, equ2=equ2)


@app.route('/record/<name>')    #查閱個人租借紀錄
def personal_record(name):
    filter1 = {'借用人':name, '歸還日期':{ "$gt": datetime.utcnow()}}  
    recent_record = Record.find(filter1)
    filter2 = {'借用人':name, '歸還日期':{ "$lt": datetime.utcnow()}}  
    passed_record = Record.find(filter2)
    return render_template('personalRecord.html', name=name, recent_record=recent_record,
                            passed_record=passed_record, current_time=datetime.utcnow())


@app.route('/personal_info/<name>')    #查閱個人資料&登出
def personal_info(name):
    filter = {'聯絡人姓名':name}
    user = User.find_one(filter)
    return render_template('personalInfo.html', name=name, context=user)


@app.route('/rent/<id>',methods=['POST','GET'])  #預約使用-功能路由 (id為Lab_Equ DB的id)
def rent(id):
    form=Rent()
    if form.validate_on_submit():
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



@app.route('/hand_in/<num>')  #預約使用-功能路由 (order為Record DB的財物編號)
def hand_in(num):
    #更改財產狀態
    filter1 = {'財物編號':num}
    equ=Lab_Equ.find_one(filter1)
    equ_update = {'$set':{'歸還日期':datetime.utcnow()}}
    Lab_Equ.update_one(filter1,equ_update)
    #更新租借紀錄(RECORD)
    filter2 = {'借用人':session.get('name')}
    record_update = {'$set':{'歸還日期':datetime.utcnow()}}
    Record.update_one(filter2,record_update)
    flash('sucessfully booked' + equ['財物名稱'])
    return redirect(url_for('personal_record', name=session.get('name')))


@app.route('/logout')   #登出-功能路由
def logout():
    session['name'] = None
    session['account'] = None
    return redirect(url_for('index'))

#__錯誤處理路由___________________________________________________________________________
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
