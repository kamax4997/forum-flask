from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
from datetime import datetime

import re   # "re"regular expression operations
import mysql.connector
# import pymysql
# import pymysql.cursors #makes data sent as python dictionaries

mysql = connectToMySQL('sql11422002')

# used for email validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__) 
bcrypt = Bcrypt(app)  
app.secret_key = "ThisIsSecret!"

# =====================================================
#                     INDEX ROUTE
# =====================================================
@app.route('/')
def index():
    mysql = connectToMySQL('sql11422002')

    # data to show "ALL topics", newest first
    # -------------------------------------------
    topic_query = "SELECT topics.id as id, topics.text as text, topics.created_at as created_at, topics.updated_at as updated_at, users.username as username FROM topics JOIN users ON topics.user_id = users.id ORDER BY topics.id DESC;"
  
    # use this to loop through on messages.html
    topics = mysql.query_db(topic_query)
    # print("topics", topics)
    return render_template('index.html', topics = topics)

# =======================================================
#                  REGISTER BUTTON ROUTE
# =======================================================
@app.route('/register', methods=['POST'])
def register():

    # name validation
    # --------------------------------------
    if len(request.form['username']) < 2:
        flash("User name must be at least 2 characters", 'username')
    
    # new-email validation
    # --------------------------------------
    if not EMAIL_REGEX.match(request.form['email']):
        flash("Invalid Email Address!", 'email')

    # checking if email already exists in db
    # --------------------------------------
    mysql = connectToMySQL('sql11422002')
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email']}
    matchingEmail = mysql.query_db(query, data)

    if matchingEmail:
        flash("Email already exists", 'email')
    
    # new-password validation
    # --------------------------------------
    if len(request.form['password']) < 8:
        flash("password must be at least 8 characters", 'password')
    
    # confirm-password validation
    # --------------------------------------
    if request.form['password'] != request.form['confirm-password']:
        flash("passwords don't match", 'confirm-password')
    
    # initiate any flash messages on index.html
    # --------------------------------------
    if '_flashes' in session.keys():
        return redirect("/")

    # ADD NEW USER TO DATABASE : hash password
    # --------------------------------------
    else:
        mysql = connectToMySQL('sql11422002')
        password_hash = bcrypt.generate_password_hash(request.form['password']) 

        query = "INSERT INTO users (username, email, password, created_at, updated_at) VALUES (%(username)s, %(email)s, %(password)s, NOW(), NOW());"
        data = {
             "username": request.form['username'],
             "email": request.form['email'],
             "password": password_hash,
        }
        new_user_id=mysql.query_db(query, data)

        # get user_id and store into session
        session['user_id'] = new_user_id
        session['user_name'] = request.form['username']
        print('SESSION:', session)
        flash("Welcome, you successfully registered!", 'success')

        return redirect('/')
    

# =======================================================
#                  LOGIN BUTTON ROUTE
# =======================================================
@app.route('/login', methods=['POST'])
def login():
    
    # check if email exists in database
    # --------------------------------------
    mysql = connectToMySQL('sql11422002')
    query = "SELECT id, username, password FROM users WHERE email = %(email)s;"
    data = { "email" : request.form['email'] }
    result = mysql.query_db(query, data)
    if result:
        temp = request.form.to_dict(flat = False)
        output = []
        for i in range(len(temp['email'])):
            di = {}
            for key in temp.keys():
                di[key] = temp[key][i]
            output.append(di)
        if bcrypt.check_password_hash(result[0][2], output[0]['password']):
            
            # if True: store some user data in session
            session['user_id'] = result[0][0]
            session['user_name'] = result[0][1]

            return redirect('/')
    
        # if username & password don't match
        # --------------------------------------
        else:
            flash("You could not be logged in", 'login')
            return redirect("/")


# =======================================================
#                  TOPIC DETAIL PAGE
# =======================================================
@app.route('/topic', methods=['GET', 'POST'])
def topic():

    topic_id = request.args.get('id')
    topic_text = request.args.get('text')

    mysql = connectToMySQL('sql11422002')

    # data for all claims belong to selected topic
    claim_query = "SELECT claims.id, claims.post_type, claims.topic_id, claims.user_id, claims.parent_claim_id, claims.text, claims.created_at, claims.updated_at, users.username FROM claims JOIN users ON (claims.user_id = users.id AND claims.topic_id = %(topic_id)s) ORDER BY claims.id DESC;"
    claim_data = {
        "topic_id": topic_id
    }
    claims = mysql.query_db(claim_query, claim_data)
    output = []
    claim_keys = ['id', 'post_type', 'topic_id', 'user_id', 'parent_claim_id', 'text', 'created_at', 'updated_at', 'username']
    for claim in claims:
        di = {}
        for key in range(len(claim)):
            di[claim_keys[key]] = claim[key]
        output.append(di)

    # SEND ALL OF THIS DATA TO BE MANIPULATED ON HTML
    return render_template('topic.html', id = topic_id, text = topic_text, claims = output)


# =======================================================
#                  CLAIM DETAIL PAGE
# =======================================================
@app.route('/claim', methods=['GET', 'POST'])
def claim():

    topic_id = request.args.get('parent')
    claim_id = request.args.get('id')
    claim_text = request.args.get('text')

    mysql = connectToMySQL('sql11422002')

    # data for all claims belong to selected topic
    claim_query = "SELECT claims.id, claims.post_type, claims.topic_id, claims.user_id, claims.parent_claim_id, claims.text, claims.created_at, claims.updated_at, users.username FROM claims JOIN users ON (claims.user_id = users.id AND claims.parent_claim_id = %(claim_id)s) ORDER BY claims.id DESC;"
    claim_data = {
        "claim_id": claim_id
    }
    claims = mysql.query_db(claim_query, claim_data)
    output = []
    claim_keys = ['id', 'post_type', 'topic_id', 'user_id', 'parent_claim_id', 'text', 'created_at', 'updated_at', 'username']
    for claim in claims:
        di = {}
        for key in range(len(claim)):
            di[claim_keys[key]] = claim[key]
        output.append(di)
    
    mysql = connectToMySQL('sql11422002')

    thread_query = "SELECT threads.id, threads.post_type, threads.topic_id, threads.user_id, threads.claim_id, threads.parent_thread_id, threads.text, threads.created_at, threads.updated_at, users.username FROM threads JOIN users ON (threads.user_id = users.id AND threads.claim_id = %(claim_id)s) ORDER BY threads.id DESC;"
    thread_data = {
        "claim_id": claim_id
    }
    threads = mysql.query_db(thread_query, thread_data)
    output1 = []
    thread_keys = ['id', 'post_type', 'topic_id', 'user_id', 'claim_id', 'parent_thread_id', 'text', 'created_at', 'updated_at', 'username']
    for thread in threads:
        di1 = {}
        for key in range(len(thread)):
            di1[thread_keys[key]] = thread[key]

        mysql = connectToMySQL('sql11422002')

        thread_query1 = "SELECT threads.id, threads.post_type, threads.topic_id, threads.user_id, threads.claim_id, threads.parent_thread_id, threads.text, threads.created_at, threads.updated_at, users.username FROM threads JOIN users ON (threads.user_id = users.id AND threads.parent_thread_id = %(thread_id)s) ORDER BY threads.id DESC"
        thread_data1 = {
            "thread_id": di1['id']
        }
        threads1 = mysql.query_db(thread_query1, thread_data1)
        output2 = []
        for thread1 in threads1:
            di2 = {}
            for key1 in range(len(thread1)):
                di2[thread_keys[key1]] = thread1[key1]
            output2.append(di2)
        di1['children'] = output2
        output1.append(di1)

    # SEND ALL OF THIS DATA TO BE MANIPULATED ON HTML
    return render_template('claim.html', parent = topic_id, id = claim_id, text = claim_text, claims = output, threads = output1)

# =====================================================
#                 CREATE A TOPIC
# =====================================================
@app.route('/create', methods=['POST'])
def create():
    user_id = session['user_id']

    mysql = connectToMySQL("sql11422002")
    query= "INSERT INTO topics (user_id, text, created_at, updated_at, views) VALUES (%(user_id)s, %(text)s, NOW(), NOW(), %(views)s);"

    temp = request.form.to_dict(flat = False)
    output = []
    for i in range(len(temp['create'])):
        di = {}
        for key in temp.keys():
            di[key] = temp[key][i]
        output.append(di)
    data = {
        'user_id': session['user_id'],
        'text': output[0]['create'],
        'views': 0,
        }
    mysql.query_db(query, data)

    return redirect('/')


# =====================================================
#                 CREATE A CLAIM
# =====================================================
@app.route('/create_claim', methods=['POST'])
def create_claim():

    mysql = connectToMySQL("sql11422002")
    query= ""
    data = {}
    if request.form['pagetype'] == '1':
        query = "INSERT INTO claims (post_type, user_id, text, parent_claim_id, created_at, updated_at) VALUES (%(post_type)s, %(user_id)s, %(text)s, %(parent_claim_id)s, NOW(), NOW());"
        data = {
            'post_type': request.form['posttype'],
            'user_id': session['user_id'],
            # 'topic_id': request.form['topicId'],
            'parent_claim_id': request.form['claimId'],
            'text': request.form['text'],
        }
        mysql.query_db(query, data)

        return redirect(url_for('claim', id = request.form['claimId'], text = request.form['claimText']))
    else:
        query = "INSERT INTO claims (post_type, topic_id, user_id, text, created_at, updated_at) VALUES (%(post_type)s, %(topic_id)s, %(user_id)s, %(text)s, NOW(), NOW());"
        data = {
            'post_type': request.form['posttype'],
            'user_id': session['user_id'],
            'topic_id': request.form['topicId'],
            # 'parent_claim_id': request.form['relation'],
            'text': request.form['text'],
        }
        mysql.query_db(query, data)

        return redirect(url_for('topic', id = request.form['topicId'], text = request.form['topicText']))

    

# =====================================================
#                 CREATE A THREAD
# =====================================================
@app.route('/create_thread', methods=['POST'])
def create_thread():
    user_id = session['user_id']

    mysql = connectToMySQL("sql11422002")
    query= ""
    data = {}
    if request.form['claimRelation'] == '0':
        query = "INSERT INTO threads (post_type, topic_id, user_id, claim_id,  text, created_at, updated_at) VALUES (%(post_type)s, %(topic_id)s, %(user_id)s, %(claim_id)s, %(text)s, NOW(), NOW());"
        data = {
            'post_type': request.form['posttype'],
            'user_id': session['user_id'],
            'topic_id': request.form['topicId'],
            'claim_id': request.form['claimId'],
            'text': request.form['text'],
        }
    else:
        query = "INSERT INTO threads (post_type, topic_id, user_id, text, parent_thread_id, created_at, updated_at) VALUES (%(post_type)s, %(topic_id)s, %(user_id)s, %(text)s, %(parent_thread_id)s, NOW(), NOW());"
        data = {
            'post_type': request.form['posttype'],
            'user_id': session['user_id'],
            'topic_id': request.form['topicId'],
            'parent_thread_id': request.form['threadRelation'] if request.form['threadRelation'] else None,
            'text': request.form['text'],
        }
    mysql.query_db(query, data)

    return redirect(url_for('claim', parent = request.form['topicId'], id = request.form['claimId'], text = request.form['claimText']))

# # =====================================================
# #                 DELETE A MESSAGE
# # =====================================================
# @app.route('/delete_message', methods=['POST'])
# def delete_message():

#     mysql = connectToMySQL("sql11422002")
#     query = "DELETE FROM messages WHERE (id = %(messagesId)s);"
#     data = {
#         'messagesId': request.form['messagesId']
#     }
#     mysql.query_db(query, data)

#     return redirect('/getData')


# ====================================================
#        LOG OUT: clear session
# ====================================================
@app.route('/logout', methods=['POST'])
def logout():
    return redirect('/clear_session')
# ----------------------------------------
@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect('/')


# =======================================================
#         START SERVER **********
# =======================================================
if __name__ == "__main__":
    app.run(debug=True)

