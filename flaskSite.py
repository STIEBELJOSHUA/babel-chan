import os
import uuid
import hashlib
from flask import Flask, render_template, request, redirect, url_for, Markup, g
from werkzeug import secure_filename
import datetime, os, random
import sqlite3


DATABASE = 'databased.db'
UPLOAD_FOLDER = './static/images/posts'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
@app.route("/home")
def home():
	return render_template('index.html')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def create_post(request):
	query = ''' INSERT INTO posts(id, img, title, user, date, board, post_text) values(?,?,?,?,?,?,?) '''
	cur = get_db().cursor()
	cur.execute(query, request)
	get_db().commit()
	cur.close()


def create_reply(request):
	query = ''' INSERT INTO replies(id, img, user, date, post_text, reply_id) values(?,?,?,?,?,?) '''
	cur = get_db().cursor()
	cur.execute(query, request)
	get_db().commit()
	cur.close()

def randId():
	I_D=str(uuid.uuid4()).replace('-','')
	I_D = I_D[0:9]
	data = query_db('select * from posts where id = "{}"'.format(I_D))
	check = 0
	while check < 1:
		if len(data) == 0:
			check += 1
			return(I_D)
		

def randRepl():
	I_D=str(uuid.uuid4()).replace('-','')
	I_D = I_D[0:9]
	data = query_db('select * from replies where id = "{}"'.format(I_D))
	check = 0
	while check < 1:
		if len(data) == 0:
			check += 1
			return(I_D)
		



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def hashid(numb):
	while numb[0] == ' ':
		numb = numb[1:]
	while numb[0] == '!':
		numb = numb[1:]
	if numb[0] == '#':
		numb = numb[1:]
		h = hashlib.sha256(str(numb).encode('utf-8')).hexdigest()
		return('!'+h[0:9])
	else:
		return(numb)

app.jinja_env.globals.update(hashid=hashid)
@app.route("/board/<id>/<pagenum>")
@app.route("/board/<id>")
def board(id, pagenum=1):
	pagenum = int(pagenum)
	posts = query_db('select * from posts where board = "{}"'.format(id))
	if len(posts)%10 == 0:
		pages = len(posts)//10
	else:
		pages = len(posts)//10 + 1 
	if pagenum == 1:
		posts = posts[-10:]
	else:
		posts = posts[-10*(pagenum):-10*(pagenum-1)]
	posts = posts[::-1]
	return render_template('board.html', id = id, posts = posts, pagenum=pagenum, pages=pages)

@app.route("/thread/<postnum>")
def thread(postnum):
	exists = query_db('select * from posts where id = "{}"'.format(postnum))
	if len(exists) == 0:
		return redirect(url_for('home'))
	else:
		x=1
	posts = query_db('select * from posts where id = "{}"'.format(postnum))
	repl = query_db('select * from replies where reply_id = "{}"'.format(postnum))
	replids = []
	for repli in repl:
		replids.append(repli[0])
	return render_template('replies.html', id = postnum, repl = repl, posts = posts, replids = replids)

@app.route("/post/<id>", methods=['GET','POST'])
def post(id):
	#check if board is in list of real boards, if not, reroute to error page
	#or make secret boards a thing but at least make sure that the name of boards is less than a certian ammount
	if request.method =='POST':
		file = request.files['file']
		subject = request.form['subject']
		if request.form['ID']:
			USER_ID = request.form['ID']
			USER_ID = hashid(USER_ID)
		else:
			USER_ID = 'Anonymous'
		title = request.form['title']
		if file and allowed_file(file.filename):
			idhash = randId()
			filename = secure_filename(file.filename)
			filename = idhash + filename
			file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
			now = datetime.datetime.now()
			post = (idhash, filename, title, USER_ID, now.isoformat(), id, subject)
			create_post(post)
			return redirect(url_for('thread', postnum = idhash))
		else:
			return redirect(url_for('home'))

	return render_template('boardpost.html', id=id)


@app.route("/reply/<postnum>", methods=['GET','POST'])
def reply(postnum):
	exists = query_db('select * from posts where id = "{}"'.format(postnum))
	if len(exists) == 0:
		return redirect(url_for('home'))
	else:
		x=1
	if request.method =='POST':
		if request.files.get('file'):
			file = request.files['file']
		else:
			file = 'none'
		subject = request.form['subject']
		if request.form['ID']:
			USER_ID = request.form['ID']
			USER_ID = hashid(USER_ID)
		else:
			USER_ID = 'Anonymous'
		if file and file!= 'none' and allowed_file(file.filename):
			idhash = randRepl()
			filename = secure_filename(file.filename)
			filename = idhash + filename
			file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
			now = datetime.datetime.now()
			reply = (idhash, filename, USER_ID, now.isoformat(), subject, postnum)
			create_reply(reply)
			return redirect(url_for('thread', postnum=postnum))
		elif file == 'none':
			filename = 'none'
			now = datetime.datetime.now()
			idhash = randRepl()
			reply = (idhash, filename, USER_ID, now.isoformat(), subject, postnum)
			create_reply(reply)
			return redirect(url_for('thread', postnum=postnum))
		else:
			return redirect(url_for('home'))


	return render_template('replypost.html', postnum=postnum)
    

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', pic = pic), 404


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


if __name__ == '__main__':
    app.run()

