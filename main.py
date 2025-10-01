from flask import Flask, render_template, flash, request, redirect, url_for,get_flashed_messages,session,jsonify
import sqlite3,time,datetime,os,json,requests,re,math,secrets,pytz,logging
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import date,timedelta,timezone
from werkzeug.security import generate_password_hash,check_password_hash
from flask_limiter import Limiter
from flask_wtf.csrf import CSRFProtect
from apscheduler.schedulers.background import BackgroundScheduler
from logging.handlers import TimedRotatingFileHandler
import uuid

# 定义清理过期会话的函数
def clean_expired_sessions():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "DELETE FROM sessions WHERE expires_at <= CURRENT_TIMESTAMP"
    )
    con.commit()
    con.close()
    print(f"{datetime.datetime.now()} - 清理了过期的会话记录")

# 设置定时清理任务
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(clean_expired_sessions, 'interval', hours=1)  # 每小时清理一次
    scheduler.start()

#日期转绝对时间函数
def date_to_ctime(date_str):
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
    utc_plus_8 = datetime.timezone(datetime.timedelta(hours=8))
    date_obj_utc8 = date_obj.replace(tzinfo=utc_plus_8)
    return date_obj_utc8.timestamp()

#初始配置
start_scheduler()
app = Flask(__name__,static_folder='static', static_url_path='/static')
load_dotenv(dotenv_path='SecretKey.env')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
csrf = CSRFProtect(app)
DATABASE = 'instance/database.db'
CORS(app, resources={r"/getSongData": {"origins": "*"}})
def limit_key_func():
    return str(request.headers.get("X-Forwarded-For", '127.0.0.1'))
limiter = Limiter(app=app,key_func=limit_key_func)

#首页
@app.route('/')
def home():
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor()
    today = date.today()
    today_ctime = date_to_ctime(str(today))              
    showed_playlist = cur.execute("SELECT * FROM tb WHERE invisibility IS NULL AND datectime >= ? ORDER BY datectime LIMIT 0, 10", (today_ctime,)).fetchall()
    expired_playlist = cur.execute("SELECT * FROM tb WHERE (invisibility IS NULL OR invisibility == '过期') AND datectime < ? ORDER BY datectime DESC LIMIT 0, 5", (today_ctime,)).fetchall()
    #获取可点日期
    # 获取当前时间
    utc8 = pytz.timezone('Asia/Shanghai')  # 设置时区为上海时间，即 UTC+8
    current_time = datetime.datetime.now(utc8)
    # 获取今天早上 6:30 的时间
    morning_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
    # 如果当前时间已经过了早晨6:30，则更新为今天的6:30
    # 如果还没过6:30，则使用昨天的6:30
    if current_time >= morning_time:
        base_time = morning_time
    else:
        base_time = morning_time - timedelta(days=1)
    # 计算30天后的时间
    order_time = base_time + timedelta(days=30)
    # 格式化输出
    formatted_date = order_time.strftime("%Y-%m-%d")
    cur.close()
    con.close()
    with open('notice.md',encoding='utf-8') as f:
        notice_content = f.read()
        notice_content = re.sub(r'[*#_`~]', '', notice_content)
        notice_content = notice_content[:25]
        return render_template('add.html',expired=expired_playlist,showed=showed_playlist,date=formatted_date,notice=notice_content)

#管理页面
@app.route('/manage')
def manage():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    # 验证会话有效性
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    # 验证成功，获取歌单
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor()            
    today = date.today()
    today_ctime = date_to_ctime(str(today))    
    cur.execute("UPDATE tb SET invisibility = '过期' WHERE invisibility IS NULL AND datectime < ?", (today_ctime,))
    con.commit()
    showed_playlist = cur.execute("SELECT * FROM tb WHERE datectime >= ? ORDER BY datectime LIMIT 0,10", (today_ctime,)).fetchall()
    expired_playlist = cur.execute("SELECT * FROM tb WHERE datectime < ? ORDER BY datectime DESC LIMIT 0,5", (today_ctime,)).fetchall()
    cur.close()
    con.close() 
    return render_template('manage.html',showed=showed_playlist,expired=expired_playlist)

#公告修改页面
@app.route('/notice_update')
def notice_update():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    with open('notice.md',encoding='utf-8') as f:
            notice = f.read()
            return render_template('notice_update.html',notice=notice)
 
#公告修改提交   
@app.route('/notice_submit',methods=['POST'])
def notice_submit():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    with open('notice.md',mode='w',encoding='utf-8') as f:
        f.write(request.form['notice_write'])
        flash('提交成功！', 'success')
        return render_template('feedback.html')

@app.route('/notice')
def notice():
    with open('notice.md',encoding='utf-8') as f:
        notice = f.read()
        return render_template('notice.html',notice=notice)


#点歌提交任务
@app.route('/submit', methods=['POST'])
def submit():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_address = ip_address.split(',')[0]  
    with sqlite3.connect(DATABASE) as con:  
        cur = con.cursor()    
        date_select = request.form['date']           
        cur.execute("SELECT * FROM tb WHERE date=? AND invisibility is NULL", (str(date_select),))
        results = cur.fetchall()
        cur.close()
    from datetime import date
    today = date.today()
     # 获取当前时间
    utc8 = pytz.timezone('Asia/Shanghai') 
    current_time = datetime.datetime.now(utc8)
    # 获取最远可点日期
    morning_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
    if current_time >= morning_time:
        base_time = morning_time
    else:
        base_time = morning_time - timedelta(days=1)
    order_time = base_time + timedelta(days=30)
    order_time_timestamp = order_time.timestamp()
    if date_to_ctime(str(date_select)) < date_to_ctime(str(today)):
        flash('提交失败：不能提交过去的日期！','danger')
        return render_template('feedback.html')
    if date_to_ctime(str(date_select)) > order_time_timestamp:
        flash('提交失败：日期超出30天限制！', 'danger')
        return render_template('feedback.html')
    if date_to_ctime(str(date_select)) == float(date_to_ctime(str(today))):
        flash('提交失败：无法提交当天，请至少提前一天点歌！', 'danger')
        return render_template('feedback.html')
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()  
        if cur.execute("SELECT * FROM tb WHERE name=? AND artist=? AND date=?",(request.form['name'],request.form['artist'],request.form['date'])).fetchall() != []:
            flash('提交失败：当日已有此歌曲！', 'danger')
            cur.close()
            con.close()
            return render_template('feedback.html')
        if request.form.get('birthday') == "on" and len(results)>=2:
            name = request.form['name']
            target = request.form['target']
            artist = request.form['artist']
            client = request.form['client']
            date = request.form['date']
            note = request.form['note']
            birthday = "on"
            ctime = time.time()
            datectime = date_to_ctime(request.form['date'])
            code = str(uuid.uuid4()) 
            try:
                with sqlite3.connect(DATABASE) as con:     
                    cur = con.cursor()   
                    cur.execute("SELECT id FROM tb WHERE date = ? AND birthday is NULL AND invisibility is NULL ORDER BY ctime DESC LIMIT 1", (date,))
                    id = cur.fetchall()
                    if id!=[]:
                        cur.execute("UPDATE tb SET invisibility = '隐藏' WHERE id = ?", (id[0][0],))
                    cur.execute("INSERT INTO tb (date,name,artist,target,client,note,ctime,datectime,birthday,ip,code) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(date,name,artist,target,client,note,ctime,datectime,birthday,ip_address,code) )                    #添加数据，执行单条的sql语句
                    con.commit()
            except Exception as e:
                con.rollback()
                flash('提交失败：{}'.format(str(e)), 'danger')
                return render_template('feedback.html')
            else:
                flash('提交成功！您的识别码为'+code+'，为方便后续修改，请牢记！', 'success')
                return render_template('feedback.html')
            finally:
                cur.close() 
                con.close()
        elif(len(results)>=2):
            flash('提交失败：当日歌曲已满', 'danger')
            return render_template('feedback.html')
        else:
            name = request.form['name']
            target = request.form['target']
            artist = request.form['artist']
            client = request.form['client']
            date = request.form['date']
            note = request.form['note']
            birthday = request.form.get('birthday')
            ctime = time.time()
            datectime = date_to_ctime(request.form['date'])
            code = str(uuid.uuid4()) 
            try:
                with sqlite3.connect(DATABASE) as con:     
                    cur = con.cursor()               
                    cur.execute("INSERT INTO tb (date,name,artist,target,client,note,ctime,datectime,birthday,ip,code) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(date,name,artist,target,client,note,ctime,datectime,birthday,ip_address,code) )                    #添加数据，执行单条的sql语句
                    con.commit()
            except Exception as e:
                con.rollback()
                flash('提交失败：{}'.format(str(e)), 'danger')
                return render_template('feedback.html')
            else:
                flash('提交成功！您的识别码为'+code+'，为方便后续修改，请牢记！', 'success')
                return render_template('feedback.html')
            finally:
                cur.close() 
                con.close()

#管理员删除点歌任务
@app.route('/delete', methods=['POST'])
def delete():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        try:
            id = request.form['id']                
            cur.execute("DELETE FROM tb WHERE id = ?", (id,))
            con.commit()
        except Exception as e:
            con.rollback()
            flash('删除失败：{}'.format(str(e)), 'danger')
            return render_template('feedback.html')
        else:
            flash('删除成功！', 'success')
            return render_template('feedback.html')
        finally:
            cur.close()  

#用户删除点歌任务
@app.route('/user_delete', methods=['POST'])
def user_delete():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        try:
            id = request.form['id']                
            cur.execute("DELETE FROM tb WHERE id = ?", (id,))
            con.commit()
        except Exception as e:
            con.rollback()
            flash('删除失败：{}'.format(str(e)), 'danger')
            return render_template('feedback_tohome.html')
        else:
            flash('删除成功！', 'success')
            return render_template('feedback_tohome.html')
        finally:
            cur.close() 

#登录页面
@app.route('/login')
def login():
    return render_template("login.html")

# 登录处理函数
@app.route('/login_submit', methods=['GET','POST'])
@limiter.limit("5 per minute")  
def login_submit():
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor() 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        result = con.execute("SELECT password FROM users WHERE username = ?", (username,))
        if result.fetchone() is None:
            flash('提交失败：用户名或密码错误！', 'danger')
            cur.close()
            con.close() 
            return render_template('feedback.html')
        else:
            result = con.execute("SELECT password FROM users WHERE username = ?", (username,))
            hashed_password = result.fetchone()[0]
            if check_password_hash(hashed_password, password):
                session_id = secrets.token_hex(16)  
                session_token = secrets.token_hex(32)  
                # 设置过期时间为 30 天
                expires_at = (datetime.datetime.now(timezone.utc) + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')  
                user_agent = request.headers.get('User-Agent', 'Unknown')
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                ip_address = ip_address.split(',')[0]  
                cur.execute("INSERT INTO sessions (session_id, username, session_token, expires_at, user_agent, ip_address) VALUES (?, ?, ?, ?, ?, ?)",(session_id, username, session_token, expires_at, user_agent, ip_address))
                con.commit()
                session['session_id'] = session_id
                session['session_token'] = session_token
                session['username'] = username
                cur.close()
                con.close() 
                return redirect(url_for('manage'))
            else:
                flash('提交失败：用户名或密码错误！', 'danger')
                cur.close()
                con.close() 
                return render_template('feedback.html')
    else:
        return render_template('login.html')

# 退出登录处理函数
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session_id = session.get('session_id')
    username = session.get('username')
    if session_id and username:
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        cur.execute("DELETE FROM sessions WHERE session_id = ? AND username = ?", (session_id, username))
        con.commit()
        con.close()
    session.clear()
    return redirect(url_for('login'))

#修改点歌页面
@app.route('/edit', methods=['POST'])
def edit():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    id = request.form['id']
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor() 
    results = cur.execute("SELECT * FROM tb WHERE id = ?", (id,))
    return render_template('edit.html',db=results)

#点歌详情界面
@app.route('/detail', methods=['POST'])
def detail():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    id = request.form['id']
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor() 
    results = cur.execute("SELECT * FROM tb WHERE id = ?", (id,))
    return render_template('detail.html',db=results)

#用户修改页面
@app.route('/user_edit', methods=['POST'])
def user_edit():
    code = request.form['code']
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor() 
    results = cur.execute("SELECT * FROM tb WHERE code = ?", (code,)).fetchall()
    if results != []:
        return render_template('user_edit.html',db=results)
    else:
        flash('识别码不存在！请检查后重试！','danger')
        return render_template('feedback_tohome.html')

#管理员修改任务
@app.route('/update', methods=['POST'])
def update():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    id = request.form['id']
    name = request.form['name']
    target = request.form['target']
    artist = request.form['artist']
    client = request.form['client']
    date = request.form['date']
    datectime = date_to_ctime(date)
    note = request.form['note']
    birthday=request.form.get('birthday')
    con= sqlite3.connect(DATABASE)       
    cur = con.cursor()               
    cur.execute("UPDATE tb SET name=?,target=?,artist=?,client=?,date=?,note=?,datectime=?,birthday=? WHERE id =?",(name,target,artist,client,date,note,datectime,birthday,id))
    con.commit()
    cur.close()
    con.close()
    return redirect(url_for('manage'))

#用户修改任务
@app.route('/user_update', methods=['POST'])
def user_update():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_address = ip_address.split(',')[0]  
    with sqlite3.connect(DATABASE) as con:  
        cur = con.cursor()    
        date_select = request.form['date']           
        cur.execute("SELECT * FROM tb WHERE date=? AND invisibility is NULL", (str(date_select),))
        results = cur.fetchall()
        cur.close()
    from datetime import date
    today = date.today()
    utc8 = pytz.timezone('Asia/Shanghai')  
    current_time = datetime.datetime.now(utc8)
    # 获取最远可点日期
    morning_time = current_time.replace(hour=6, minute=30, second=0, microsecond=0)
    if current_time >= morning_time:
        base_time = morning_time
    else:
        base_time = morning_time - timedelta(days=1)
    order_time = base_time + timedelta(days=30)
    order_time_timestamp = order_time.timestamp()
    if date_to_ctime(str(date_select)) < date_to_ctime(str(today)):
        flash('提交失败：不能提交过去的日期！','danger')
        return render_template('feedback_tohome.html')
    if date_to_ctime(str(date_select)) > order_time_timestamp:
        flash('提交失败：日期超出30天限制！', 'danger')
        return render_template('feedback_tohome.html')
    if date_to_ctime(str(date_select)) == float(date_to_ctime(str(today))):
        flash('提交失败：无法提交当天，请至少提前一天点歌！', 'danger')
        return render_template('feedback_tohome.html')
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor()  
    new_date = request.form['date']
    ori_date = request.form['ori_date']
    if ori_date == new_date:
        try:    
            with sqlite3.connect(DATABASE) as con:     
                cur = con.cursor()
                id = request.form['id']
                name = request.form['name']
                target = request.form['target']
                artist = request.form['artist']
                client = request.form['client']
                date = request.form['date']
                note = request.form['note']
                birthday = request.form.get('birthday')
                datectime = date_to_ctime(request.form['date'])               
                cur.execute("UPDATE tb SET name=?,target=?,artist=?,client=?,date=?,note=?,datectime=?,birthday=?,ip=? WHERE id =?",(name,target,artist,client,date,note,datectime,birthday,ip_address,id))
                con.commit()
        except Exception as e:
            con.rollback()
            flash('提交失败：{}'.format(str(e)), 'danger')
            return render_template('feedback_tohome.html')
        else:
            flash('提交成功！', 'success')
            return render_template('feedback_tohome.html')
        finally:
            con.close() 
    elif request.form.get('birthday') == "on" and len(results)>=2 and ori_date != new_date:
        try:
            id = request.form['id']
            name = request.form['name']
            target = request.form['target']
            artist = request.form['artist']
            client = request.form['client']
            date = request.form['date']
            note = request.form['note']
            birthday = "on"
            datectime = date_to_ctime(request.form['date'])
            with sqlite3.connect(DATABASE) as con:     
                cur = con.cursor()   
                cur.execute("SELECT id FROM tb WHERE date = ? AND birthday IS NULL AND invisibility IS NULL ORDER BY ctime DESC LIMIT 1", (date,))
                set_id = cur.fetchall()
                if set_id!=[]:
                    cur.execute("UPDATE tb SET invisibility = '隐藏' WHERE id = ?", (set_id[0][0],))
                cur.execute("UPDATE tb SET name=?,target=?,artist=?,client=?,date=?,note=?,datectime=?,birthday=?,ip=? WHERE id =?",(name,target,artist,client,date,note,datectime,birthday,ip_address,id))
                con.commit()
        except Exception as e:
            con.rollback()
            flash('提交失败：{}'.format(str(e)), 'danger')
            return render_template('feedback_tohome.html')
        else:
            flash('提交成功！', 'success')
            return render_template('feedback_tohome.html')
        finally:
            con.close() 
    elif(len(results)>=2):
        flash('提交失败：当日歌曲已满', 'danger')
        return render_template('feedback_tohome.html')
    else:
        try:    
            with sqlite3.connect(DATABASE) as con:     
                cur = con.cursor()
                id = request.form['id']
                name = request.form['name']
                target = request.form['target']
                artist = request.form['artist']
                client = request.form['client']
                date = request.form['date']
                note = request.form['note']
                birthday = request.form.get('birthday')
                datectime = date_to_ctime(request.form['date'])   
                cur.execute("UPDATE tb SET name=?,target=?,artist=?,client=?,date=?,note=?,datectime=?,birthday=?,ip=? WHERE id =?",(name,target,artist,client,date,note,datectime,birthday,ip_address,id))
                con.commit()
        except Exception as e:
            con.rollback()
            flash('提交失败：{}'.format(str(e)), 'danger')
            return render_template('feedback_tohome.html')
        else:
            flash('提交成功！', 'success')
            return render_template('feedback_tohome.html')
        finally:
            con.close() 

#管理员添加歌曲页面
@app.route('/admin_add')
def admin_add():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    # 验证会话有效性
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    return render_template('admin_add.html')


#管理员添加歌曲任务
@app.route('/admin_add_submit', methods=['POST'])
def admin_add_submit():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    from datetime import date
    name = request.form['name']
    target = request.form['target']
    artist = request.form['artist']
    client = request.form['client']
    date = request.form['date']
    note = request.form['note']
    birthday = request.form.get('birthday')
    ctime = time.time()
    datectime = date_to_ctime(request.form['date'])
    try:    
        with sqlite3.connect(DATABASE) as con:     
            cur = con.cursor()               
            cur.execute("INSERT INTO tb (date,name,artist,target,client,note,ctime,datectime,birthday) VALUES (?,?,?,?,?,?,?,?,?)",(date,name,artist,target,client,note,ctime,datectime,birthday) )
            con.commit()
    except Exception as e:
            con.rollback()
            flash('提交失败：{}'.format(str(e)), 'danger')
            return render_template('feedback.html')
    else:
            flash('提交成功！', 'success')
            return render_template('feedback.html')
    finally:
            con.close() 

#管理员修改点歌是否显示（显示/隐藏切换）
@app.route('/alter', methods=['POST'])
def alter():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    # 验证会话有效性
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    id = request.form['id']
    con= sqlite3.connect(DATABASE)    
    cur = con.cursor() 
    invisibility=cur.execute("SELECT invisibility FROM tb WHERE id=?", (id,)).fetchall()
    if invisibility[0][0] == "隐藏":
        cur.execute("UPDATE tb SET invisibility=NULL WHERE id=?",(id,))
    else:
        cur.execute("UPDATE tb SET invisibility='隐藏' WHERE id=?",(id,))
    con.commit()
    cur.close()
    con.close()
    return redirect(url_for('manage'))

#用户修改显示歌曲数_历史
@app.route('/edit_fetch_history', methods=['POST'])
def edit_fetch_history():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    today = date.today()
    today_ctime = date_to_ctime(str(today))
    day = request.form['num']
    expired_playlist = cur.execute("SELECT date, name, artist, birthday FROM tb WHERE (invisibility IS NULL OR invisibility = '过期') AND datectime < ? ORDER BY datectime DESC LIMIT 0, ?", 
    (today_ctime, day)
).fetchall()

    cur.close()
    con.close()
    return jsonify(expired=expired_playlist)

#用户修改显示歌曲数_当前
@app.route('/edit_fetch_current', methods=['POST'])
def edit_fetch_current():
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    today = date.today()
    today_ctime = date_to_ctime(str(today))
    day = request.form['num']
    showed_playlist = cur.execute("SELECT date, name, artist, birthday FROM tb WHERE invisibility IS NULL AND datectime >= ? ORDER BY datectime LIMIT 0, ?", (today_ctime, day)
).fetchall()

    cur.close()
    con.close()
    return jsonify(showed=showed_playlist)

#管理员修改显示歌曲数_历史
@app.route('/edit_fetch_history_manage', methods=['POST'])
def edit_fetch_history_manage():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    # 验证会话有效性
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    today = date.today()
    today_ctime = date_to_ctime(str(today))
    day = request.form['num']
    expired_playlist = cur.execute("SELECT * FROM tb WHERE datectime < ? ORDER BY datectime DESC LIMIT 0, ?", (today_ctime, day)).fetchall()
    cur.close()
    con.close()
    return jsonify(expired=expired_playlist)

#管理员修改显示歌曲数_当前
@app.route('/edit_fetch_current_manage', methods=['POST'])
def edit_fetch_current_manage():
    session_id = session.get('session_id')
    session_token = session.get('session_token')
    username = session.get('username')
    if not session_id or not session_token or not username:
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute(
        "SELECT 1 FROM sessions WHERE session_id = ? AND session_token = ? AND username = ? AND expires_at > CURRENT_TIMESTAMP",
        (session_id, session_token, username)
    )
    valid_session = cur.fetchone()
    con.close()
    if not valid_session:
        session.clear()
        return redirect(url_for('login'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    today = date.today()
    today_ctime = date_to_ctime(str(today))
    day = request.form['num']
    showed_playlist = cur.execute("SELECT * FROM tb WHERE datectime >= ? ORDER BY datectime LIMIT 0, ?", (today_ctime, day)).fetchall()
    cur.close()
    con.close()
    return jsonify(showed=showed_playlist)

#----------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True,host='0.0.0.0',port=2788)

