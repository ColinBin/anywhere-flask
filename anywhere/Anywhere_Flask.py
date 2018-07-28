# -*- coding: utf-8 -*-
__author__ = 'Colin'
from flask import Flask
from flask import request
import os,sys
import json
import hashlib
import flask
from database import db_session
from models import *
from get_location_description import LocationToDescriptionWithBaidu,LocationToDescriptionWithGoogle
from datetime import datetime
from calculate_distance import haversine

app = Flask(__name__)

LOGIN_SUCCESS=40
USER_NOT_FOUND=41
PASSWORD_WRONG=42

SIGN_UP_SUCCESS=50
USER_ALREADY_EXIST=51

ALTER_BASIC_INFO_SUCCESS=60
ALTER_PASSWORD_SUCCESS=70

GET_LOCATION_DESCRIPTION_SUCCESS=80
LOCATION_DESCRIPTION_SERVICE_UNAVAILABLE=81

CREATE_POST_SUCCESS=90

GET_POST_LIST_SUCCESS = 100

NO_POST_AROUND = 101

GET_POST_DETAIL_SUCCESS=110
POST_CIPHER_WRONG=111

GET_COMMENT_LIST_SUCCESS=120
NO_COMMENT_AVAILABLE=121

ADD_COMMENT_SUCCESS=130

LIKE_POST_SUCCESS=140
DE_LIKE_POST_SUCCESS=142

CONDEMN_POST_SUCCESS=150
DE_CONDEMN_POST_SUCCESS=152


@app.route('/login', methods=['POST'])
def login():
    result = dict()
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        findUser=db_session.query(User).filter(User.user_id==user_id).first()
        if findUser==None:
            result['permission']=USER_NOT_FOUND
        elif password!=get_md5(findUser.password):
            result['permission']=PASSWORD_WRONG
        else:
            result=findUser.as_dict()
            result['permission']=LOGIN_SUCCESS
        return json.dumps(result)


@app.route('/sign_up',methods=['POST'])
def sign_up():
    result=dict()
    if request.method=='POST':
        user_id=request.form['user_id']
        password=request.form['password']
        username=request.form['username']
        email=request.form['email']
        findUser=db_session.query(User).filter(User.user_id==user_id).first()
        if findUser!=None:
            result['permission']=USER_ALREADY_EXIST
            print("User: "+user_id+" sign up failed")
        else:
            result['permission']=SIGN_UP_SUCCESS
            newUser=User(user_id=user_id,password=password,email=email,username=username,create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            db_session.add(newUser)
            db_session.commit()
            print("User: "+user_id+" sign up success")
        return json.dumps(result)

@app.route('/get_avatar',methods=['POST'])
def get_avatar():
    if request.method=='POST':
        user_id=request.form['user_id']
        avatar_path=sys.path[0]+'/avatar/'+user_id+'.png'
        if(os.path.exists(avatar_path)):
            return flask.send_file('avatar/'+user_id+'.png')
        else:
            return ""

@app.route('/alter_basic_information',methods=['POST'])
def alter_basic_information():
    if request.method=='POST':
        user_id=request.form['user_id']
        user=db_session.query(User).filter(User.user_id==user_id).first()
        user.username=request.form['username']
        user.email=request.form['email']
        if request.form['has_altered_avatar']=='1':
            avatar_file=request.files['avatar']
            avatar_file.save(sys.path[0]+'/avatar/'+user_id+'.png')
            user.has_avatar=1
        db_session.commit()
        result=dict()
        result['permission']=ALTER_BASIC_INFO_SUCCESS
        return json.dumps(result)

@app.route('/alter_password',methods=['POST'])
def alter_password():
    result=dict()
    if request.method=="POST":
        user_id=request.form['user_id']
        original_password=request.form['original_password']
        new_password=request.form['new_password']
        findUser=db_session.query(User).filter(User.user_id==user_id).first()
        if original_password==get_md5(findUser.password):
            findUser.password=new_password
            result['permission']=ALTER_PASSWORD_SUCCESS
            db_session.commit()
        else:
            result['permission']=PASSWORD_WRONG
        return json.dumps(result)

@app.route('/get_location_description',methods=['POST'])
def get_location_description():
    if request.method=='POST':
        longitude=request.form['longitude']
        latitude=request.form['latitude']
        language=request.form['language']
        result=dict()
        location_description=None
        if language=='zh':
            location_description=LocationToDescriptionWithBaidu(longitude,latitude)
        elif language=='en':
            location_description=LocationToDescriptionWithGoogle(longitude,latitude)
        if location_description is not None:
            result['permission']=GET_LOCATION_DESCRIPTION_SUCCESS
            result['location_description']=location_description
        else:
            print("OK")
            result['permission']=LOCATION_DESCRIPTION_SERVICE_UNAVAILABLE
        return json.dumps(result)

@app.route('/create_post',methods=['POST'])
def create_post():
    if request.method=='POST':
        user_id=request.form['user_id']
        user=db_session.query(User).filter(User.user_id==user_id).first()
        title=request.form['post_title']
        content=request.form['post_content']
        location_description=request.form['location_description']
        longitude=request.form['longitude']
        latitude=request.form['latitude']
        style=request.form['post_style']
        has_cipher=request.form['has_cipher']
        cipher=request.form['post_cipher']
        has_picture=request.form['has_picture']
        newPost=Post(title=title,content=content,location_description=location_description,longitude=longitude,latitude=latitude,style=style,has_cipher=has_cipher,has_picture=has_picture,cipher=cipher,create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db_session.add(newPost)
        user.posts.append(newPost)
        db_session.commit()

        if has_picture=='1':
            post_picture=request.files['post_picture']
            post_picture.save(sys.path[0]+"/post_picture/"+str(newPost.post_id)+".png")
        result = dict()
        result['permission']=CREATE_POST_SUCCESS
        return json.dumps(result)
@app.route('/get_posts',methods=['POST'])
def get_posts():
    if request.method=='POST':
        result={}
        longitude=request.form['longitude']
        latitude=request.form['latitude']
        language=request.form['language']
        location_description=None
        if language=='zh':
            location_description=LocationToDescriptionWithBaidu(longitude,latitude)
        elif language=='en':
            location_description=LocationToDescriptionWithGoogle(longitude,latitude)
        if location_description is None:
            result['location_description']=''
        else:
            result['location_description']=location_description

        posts=db_session.query(Post).all()
        if(len(posts)>0):
            post_list = []
            for post in posts:
                if haversine(float(longitude),float(latitude),float(post.longitude),float(post.latitude))<500:
                    post_list.append(post.as_dict_abstract())
            result['posts']=post_list
            result['permission']=GET_POST_LIST_SUCCESS
        else:
            result['permission']=NO_POST_AROUND
        return json.dumps(result)

@app.route('/get_post_detail',methods=['POST'])
def get_post_detail():
    if request.method=='POST':
        post_id=request.form['post_id']
        user_id=request.form['user_id']
        post = db_session.query(Post).filter(Post.post_id == post_id).first()
        result={}
        if request.form['has_cipher']=="1":
            cipher = request.form['cipher']
            if post.cipher == cipher:
                result['permission'] = GET_POST_DETAIL_SUCCESS
                result['post'] = post.as_dict()
            else:
                result['permission'] = POST_CIPHER_WRONG
        else:
            result['post']=post.as_dict()
            result['permission']=GET_POST_DETAIL_SUCCESS
        #是否已点赞
        likes=post.post_likes
        for like in likes:
            if like.user_id==user_id:
                result['has_liked']=1
                break
        else:
            result['has_liked']=0
        #是否已点踩
        condemns=post.post_condemns
        for condemn in condemns:
            if condemn.user_id==user_id:
                result['has_condemned']=1
                break
        else:
            result['has_condemned']=0
        return json.dumps(result)

@app.route('/get_post_picture',methods=['POST'])
def get_post_picture():
    if request.method=="POST":
        post_id=request.form['post_id']
        post_picture_path=sys.path[0]+'/post_picture/'+str(post_id)+'.png'
        if os.path.exists(post_picture_path):
            return flask.send_file('post_picture/'+str(post_id)+'.png')
        else:
            return ""

@app.route('/get_comments',methods=['POST'])
def get_comments():
    if request.method=='POST':
        post_id=request.form['post_id']
        post=db_session.query(Post).filter(Post.post_id==post_id).first()
        comments=post.post_comments
        result={}
        if len(comments)>0:
            comment_list=[]
            for comment in comments:
                comment_list.append(comment.as_dict())
            result['comments']=comment_list
            result['permission']=GET_COMMENT_LIST_SUCCESS
        else:
            result['permission']=NO_COMMENT_AVAILABLE
        return json.dumps(result)

@app.route('/add_comment',methods=['POST'])
def add_comment():
    if request.method=='POST':
        user_id=request.form['user_id']
        post_id=request.form['post_id']
        user=db_session.query(User).filter(User.user_id==user_id).first()
        post=db_session.query(Post).filter(Post.post_id==post_id).first()
        content=request.form['comment_content']
        newComment=Comment(content=content,create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        post.post_comments.append(newComment)
        post.comment_number=post.comment_number+1
        user.user_comments.append(newComment)
        db_session.add(newComment)
        db_session.commit()
        result={}
        result['comment']=newComment.as_dict()
        result['permission']=ADD_COMMENT_SUCCESS
        return json.dumps(result)

@app.route('/like_post_or_not',methods=['POST'])
def like_post_or_not():
    if request.method=='POST':
        user_id=request.form['user_id']
        post_id=request.form['post_id']
        has_liked=request.form['has_liked']
        user=db_session.query(User).filter(User.user_id==user_id).first()
        post=db_session.query(Post).filter(Post.post_id==post_id).first()
        if has_liked=='1':
            newLike = Like()
            user.user_likes.append(newLike)
            post.post_likes.append(newLike)
            post.like_number = post.like_number + 1
            db_session.add(newLike)
            # remove old condemn
            oldCondemn=db_session.query(Condemn).filter(Condemn.post_id==post_id and Condemn.user_id==user_id).first()
            if oldCondemn is not None:
                db_session.delete(oldCondemn)
                post.condemn_number-=1
            db_session.commit()
            result = {}
            result['permission'] = LIKE_POST_SUCCESS
        else:
            like=db_session.query(Like).filter(Like.post_id==post_id and Like.user_id==user_id).first()
            db_session.delete(like)
            post.like_number=post.like_number-1
            db_session.commit()
            result={}
            result['permission']=DE_LIKE_POST_SUCCESS
        return json.dumps(result)


@app.route('/condemn_post_or_not',methods=['POST'])
def condemn_post_or_not():
    if request.method == 'POST':
        user_id = request.form['user_id']
        post_id = request.form['post_id']
        has_condemned=request.form['has_condemned']
        user=db_session.query(User).filter(User.user_id==user_id).first()
        post=db_session.query(Post).filter(Post.post_id==post_id).first()
        
        if has_condemned=='1':
            newCondemn = Condemn()
            user.user_condemns.append(newCondemn)
            post.post_condemns.append(newCondemn)
            post.condemn_number = post.condemn_number + 1
            db_session.add(newCondemn)
            # remove old like
            oldLike=db_session.query(Like).filter(Like.post_id==post_id and Like.user_id==user_id).first()
            if oldLike is not None:
                db_session.delete(oldLike)
                post.like_number-=1
            db_session.commit()
            result = {}
            result['permission'] = CONDEMN_POST_SUCCESS
        else:
            condemn=db_session.query(Condemn).filter(Condemn.post_id==post_id and Condemn.user_id==user_id).first()
            post.condemn_number=post.condemn_number-1
            db_session.delete(condemn)
            db_session.commit()
            result={}
            result['permission']=DE_CONDEMN_POST_SUCCESS
        return json.dumps(result)

def get_md5(raw_string):
    m=hashlib.md5()
    m.update(raw_string.encode('utf-8'))
    return m.hexdigest()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
