from flask import Flask, send_from_directory, request, render_template, redirect, render_template_string, session, url_for, flash
import pymysql
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import os

app = Flask(__name__)
    
app.secret_key = 'dm38z1mo9se7'
UPLOAD_FOLDER = "upload"
ALLOWED_EXTENSIONS = {'txt','jpg','png'};
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = pymysql.connect(host='localhost',
                     user='root',
                     password='123456',
                     database='curd',
                     charset='utf8mb4',
                     cursorclass=pymysql.cursors.DictCursor)

cursor = db.cursor()

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'testacnt1195@gmail.com'
app.config['MAIL_PASSWORD'] = 'btaf icoy txjd ufmj'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route('/')
def main_index():
    sql = "SELECT * FROM board"
    cursor.execute(sql)
    boards = cursor.fetchall()
    return render_template('index.html', boards=boards)

@app.route('/index')
def index():
    sql = "SELECT * FROM board"
    cursor.execute(sql)
    boards = cursor.fetchall()
    return render_template('index.html', boards=boards)

@app.route('/sub_index')
def sub_index():
    sql = "SELECT * FROM board"
    cursor.execute(sql)
    boards = cursor.fetchall()
    return render_template('sub_index.html', boards=boards)

@app.route('/login', methods=['GET', 'POST'])
def login():
     return render_template('login.html')

@app.route('/login_prd', methods=['GET', 'POST'])
def login_prd():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with db.cursor() as cursor:
            sql = "SELECT * FROM user WHERE username = %s AND password = %s;"
            cursor.execute(sql, (username, password))
            result = cursor.fetchone()
            if result:
                session['username'] = username
                sql = "SELECT * FROM board"
                cursor.execute(sql)
                boards = cursor.fetchall()
                return render_template('sub_index.html', boards=boards)
            else:
                alert = "<script>alert('사용자 이름 또는 비밀번호가 잘못되었습니다.'); window.history.back();</script>"
                return render_template_string(alert)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return '업로드 파일이 없습니다.'
        file = request.files['file']
        if file.filename == '':
            return '선택된 파일이 없습니다.'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return '파일이 성공적으로 업로드 되었습니다.'
        else:
            return '허용되지 않는 파일 확장자입니다.'
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  
    sql = "SELECT * FROM board"
    cursor.execute(sql)
    boards = cursor.fetchall()
    return render_template('index.html', boards=boards)

@app.route('/register', methods=['GET', 'POST'])
def register():
     return render_template('register.html')

@app.route('/register_prd', methods=['GET', 'POST'])
def register_prd():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            with db.cursor() as cursor:
                sql = "INSERT INTO user (username, email, password) VALUES (%s, %s, %s)"
                cursor.execute(sql, (username, email, password))
            db.commit()
            return '회원가입이 완료되었습니다.'
        except Exception as e:
            return '오류가 발생했습니다: ' + str(e)
    else:
        return render_template('register.html')
    
@app.route('/view_post/<int:board_id>')
def view(board_id):

    with db.cursor() as cursor:
        sql = "SELECT * FROM board WHERE id = %s"
        cursor.execute(sql, (board_id,))
        board = cursor.fetchone()

    if board['secret_key']:
        return redirect(url_for('enter_secret_key', board_id=board_id))
    else:
        return render_template('view_post.html', board=board)

@app.route('/enter_secret_key/<int:board_id>', methods=['GET', 'POST'])
def enter_secret_key(board_id):
    with db.cursor() as cursor:
        sql = "SELECT SECRET_KEY FROM board WHERE id = %s"
        cursor.execute(sql, (board_id,))
        s_key = cursor.fetchone()

    if s_key is None:
        return '게시글 정보를 찾을 수 없습니다.', 404
    
    if request.method == 'POST':
        input_secret_key = request.form.get('secret_key')

        if input_secret_key == s_key['secret_key']:
            flash("비밀번호가 일치합니다! 🎉")
            return redirect(url_for('view_post', board_id=board_id))
        else:
            flash("비밀번호가 일치하지 않습니다. 😢")
    
    return render_template('enter_secret_key.html', board_id=board_id)

@app.route('/create_post', methods=['POST'])
def create_post():
    title = request.form['title']
    author = session['username']
    content = request.form['content']
    time = datetime.now()
    if 'secret' in request.form:
        secret_key = request.form['password'] if 'password' in request.form else 'default_password'
    else:
        secret_key = 'off' 

    sql = "INSERT INTO board (title, author, content, time, secret_key) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (title, author, content, time, secret_key))
    db.commit()

    return redirect("/sub_index")

@app.route('/edit_post/<int:post_id>')
def edit_post(post_id):
    sql = "SELECT * FROM board WHERE id=%s"
    cursor.execute(sql, (post_id,))
    post = cursor.fetchone()

    if post:
        return render_template('edit.html', post=post)
    return redirect(url_for('index'))

@app.route('/update_post/<int:post_id>', methods=['POST'])
def update_post(post_id):
    title = request.form['title']
    author = request.form['author']
    content = request.form['content']

    sql = "UPDATE board SET title=%s, author=%s, content=%s WHERE id=%s"
    cursor.execute(sql, (title, author, content, post_id))
    db.commit()

    return redirect(url_for('index'))

@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    sql = "DELETE FROM board WHERE id=%s"
    cursor.execute(sql, (post_id,))
    db.commit()

    return redirect('/index')

@app.route('/search', methods=['POST'])
def search():
    search_term = request.form['search_term']

    sql = "SELECT * FROM board WHERE title LIKE %s OR content LIKE %s"
    cursor.execute(sql, (f"%{search_term}%", f"%{search_term}%"))
    boards = cursor.fetchall()

    return render_template('index.html', boards=boards)

@app.route('/recover_account', methods=['POST'])
def recover_account():
    try:
        email = request.form['recovery_email']
    except KeyError:
        return '복구 이메일 필드가 누락되었습니다.', 400
    
    with db.cursor() as cursor:
        sql = "SELECT username, password FROM user WHERE email = %s"
        cursor.execute(sql, (email,))
        user_info = cursor.fetchone()
    
    if user_info:
        msg = Message('계정 정보 복구',
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"안녕하세요, {user_info['username']}님! 귀하의 사용자 이름은 {user_info['username']}이고 비밀번호는 {user_info['password']} 입니다."
        mail.send(msg)
        
        return '복구 이메일이 전송되었습니다.'
    else:
        return '해당 이메일로 등록된 계정을 찾을 수 없습니다.'


if __name__ == '__main__':
    app.run(debug=True)
