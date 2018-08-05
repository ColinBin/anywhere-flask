# -*- coding: utf-8 -*-
__author__ = 'Colin'
import os
import sys

import flask
from flask import Flask, request, session

from db.database import db_session, init_db
from db.models import *
from util.cal_dist import haversine
from util.get_location_description import location_to_description
from constants import *
from util.res_json_gen import *

app = Flask(__name__)
app.secret_key = "faffagavvqrq;van;.;vzvqpjoi94751[jz0v"


@app.before_request
def before_request():
    if 'user_id' not in session and request.endpoint != 'login':
        return gen_json_failure(OUTDATED_SESSION)


@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['user_id']
    password = request.form['password']
    user_found = db_session.query(User).filter(User.user_id == user_id).first()
    if user_found is None:
        app.logger.info("%s failed to login (%d)", user_id, USER_NOT_FOUND)
        return gen_json_failure(USER_NOT_FOUND)
    elif password != user_found.password:
        app.logger.info("%s failed to login (%d)", user_id, PASSWORD_WRONG)
        return gen_json_failure(PASSWORD_WRONG)
    else:
        app.logger.info("%s login successfully.", user_id)
        session["user_id"] = user_id
        return gen_json_success(user_found.as_dict())


@app.route('/signup', methods=['POST'])
def signup():
    user_id = request.form['user_id']
    password = request.form['password']
    username = request.form['username']
    email = request.form['email']
    user_found = db_session.query(User).filter(User.user_id == user_id).first()
    if user_found is not None:
        app.logger.info("User %s signup failed. (%d)", user_id, USER_ALREADY_EXIST)
        return gen_json_failure(USER_ALREADY_EXIST)
    else:
        new_user = User(user_id=user_id, password=password, email=email, username=username,
                        create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db_session.add(new_user)
        db_session.commit()
        app.logger.info("User %s signup successfully.", user_id)
        return gen_json_success(None)


@app.route('/get_avatar', methods=['POST'])
def get_avatar():
    user_id = request.form['user_id']
    avatar_path = sys.path[0] + '/avatar/' + user_id + '.png'
    if os.path.exists(avatar_path):
        app.logger.info("%s Avatar file sent.", avatar_path)
        return flask.send_file('avatar/' + user_id + '.png')
    else:
        return ""


@app.route('/alter_basic_information', methods=['POST'])
def alter_basic_information():
    user_id = request.form['user_id']
    user = db_session.query(User).filter(User.user_id == user_id).first()
    user.username = request.form['username']
    user.email = request.form['email']
    if request.form['has_altered_avatar'] == '1':
        avatar_file = request.files['avatar']
        avatar_file.save(sys.path[0] + '/avatar/' + user_id + '.png')
        user.has_avatar = 1
    db_session.commit()
    app.logger.info("User %s altered basic info.", user_id)
    return gen_json_success(None)


@app.route('/alter_password', methods=['POST'])
def alter_password():
    user_id = request.form['user_id']
    original_password = request.form['original_password']
    new_password = request.form['new_password']
    user_found = db_session.query(User).filter(User.user_id == user_id).first()
    if original_password == user_found.password:
        user_found.password = new_password
        db_session.commit()
        app.logger.info("User %s altered password successfully.", user_id)
        return gen_json_success(None)
    else:
        app.logger.info("User %s alter password failure. (%d)", user_id, PASSWORD_WRONG)
        return gen_json_failure(PASSWORD_WRONG)


@app.route('/get_location_description', methods=['POST'])
def get_location_description():
    longitude = request.form['longitude']
    latitude = request.form['latitude']
    location_description = location_to_description(longitude, latitude)
    if location_description is not None:
        data = dict()
        data['location_description'] = location_description
        app.logger.info("Getting location description successfully (%.2f, %.2f)", longitude, latitude)
        return gen_json_success(data)
    else:
        app.logger.info("Failed to get location description (%.2f, %.2f). (%d)", longitude, latitude, PASSWORD_WRONG)
        return gen_json_failure(LOCATION_DESCRIPTION_SERVICE_UNAVAILABLE)


@app.route('/create_post', methods=['POST'])
def create_post():
    user_id = request.form['user_id']
    user = db_session.query(User).filter(User.user_id == user_id).first()
    title = request.form['post_title']
    content = request.form['post_content']
    location_description = request.form['location_description']
    longitude = request.form['longitude']
    latitude = request.form['latitude']
    style = request.form['post_style']
    has_cipher = request.form['has_cipher']
    cipher = request.form['post_cipher']
    has_picture = request.form['has_picture']
    new_post = Post(title=title, content=content, location_description=location_description, longitude=longitude,
                    latitude=latitude, style=style, has_cipher=has_cipher, has_picture=has_picture, cipher=cipher,
                    create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    db_session.add(new_post)
    user.posts.append(new_post)
    db_session.commit()

    if has_picture == '1':
        post_picture = request.files['post_picture']
        post_picture.save(sys.path[0] + "/post_picture/" + str(new_post.post_id) + ".png")
    app.logger.info("User %s created post successfully.", user_id)
    return gen_json_success(None)


@app.route('/get_posts', methods=['POST'])
def get_posts():
    longitude = request.form['longitude']
    latitude = request.form['latitude']
    location_description = location_to_description(longitude, latitude)
    data = dict()
    if location_description is None:
        data['location_description'] = ''
    else:
        data['location_description'] = location_description
    posts = db_session.query(Post).all()
    data['posts'] = []
    for post in posts:
        if haversine(float(longitude), float(latitude), float(post.longitude), float(post.latitude)) < 500:
            data['posts'].append(post.as_dict_abstract())
    app.logger.info("Getting post around (%.2f, %.2f) successfully.", longitude, latitude)
    return gen_json_success(data)


@app.route('/get_post_detail', methods=['POST'])
def get_post_detail():
    post_id = request.form['post_id']
    user_id = request.form['user_id']
    post = db_session.query(Post).filter(Post.post_id == post_id).first()

    if request.form['has_cipher'] == "1" and post.cipher != request.form['cipher']:
        app.logger.info("User %s failed to get post detail. (%d)", user_id, POST_CIPHER_WRONG)
        return gen_json_failure(POST_CIPHER_WRONG)
    data = {"post": post.as_dict()}
    # 是否已点赞
    likes = post.post_likes
    for like in likes:
        if like.user_id == user_id:
            data['has_liked'] = 1
            break
    else:
        data['has_liked'] = 0
    # 是否已点踩
    dislikes = post.post_dislikes
    for dislike in dislikes:
        if dislike.user_id == user_id:
            data['has_disliked'] = 1
            break
    else:
        data['has_disliked'] = 0
    app.logger.info("User %s got post detail.", user_id)
    return gen_json_success(data)


@app.route('/get_post_picture', methods=['POST'])
def get_post_picture():
    post_id = request.form['post_id']
    post_picture_path = sys.path[0] + '/post_picture/' + str(post_id) + '.png'
    if os.path.exists(post_picture_path):
        app.logger.info("Post pic sent. %s", post_picture_path)
        return flask.send_file('post_picture/' + str(post_id) + '.png')
    else:
        return ""


@app.route('/get_comments', methods=['POST'])
def get_comments():
    post_id = request.form['post_id']
    post = db_session.query(Post).filter(Post.post_id == post_id).first()
    comments = post.post_comments
    comment_list = []
    for comment in comments:
        comment_list.append(comment.as_dict())
    data = {"comments": comment_list}
    return gen_json_success(data)


@app.route('/add_comment', methods=['POST'])
def add_comment():
    user_id = request.form['user_id']
    post_id = request.form['post_id']
    user = db_session.query(User).filter(User.user_id == user_id).first()
    post = db_session.query(Post).filter(Post.post_id == post_id).first()
    content = request.form['comment_content']
    new_comment = Comment(content=content, create_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    post.post_comments.append(new_comment)
    post.comment_number += 1
    user.user_comments.append(new_comment)
    db_session.add(new_comment)
    db_session.commit()
    data = {'comment': new_comment.as_dict()}
    return gen_json_success(data)


@app.route('/like_post', methods=['POST'])
def like_post():
    user_id = request.form['user_id']
    post_id = request.form['post_id']
    has_liked = request.form['has_liked']
    user = db_session.query(User).filter(User.user_id == user_id).first()
    post = db_session.query(Post).filter(Post.post_id == post_id).first()
    if has_liked == '1':
        new_like = Like()
        user.user_likes.append(new_like)
        post.post_likes.append(new_like)
        post.like_number += 1
        db_session.add(new_like)
        # remove old dislike
        old_dislike = db_session.query(Dislike).filter(
            Dislike.post_id == post_id and Dislike.user_id == user_id).first()
        if old_dislike is not None:
            db_session.delete(old_dislike)
            post.dislike_number -= 1
        db_session.commit()
        data = {"like_post": True}
    else:
        like = db_session.query(Like).filter(Like.post_id == post_id and Like.user_id == user_id).first()
        db_session.delete(like)
        post.like_number = post.like_number - 1
        db_session.commit()
        data = {"like_post": False}
    return gen_json_success(data)


@app.route('/dislike_post', methods=['POST'])
def dislike_post():
    user_id = request.form['user_id']
    post_id = request.form['post_id']
    new_disliked = request.form['new_disliked']
    user = db_session.query(User).filter(User.user_id == user_id).first()
    post = db_session.query(Post).filter(Post.post_id == post_id).first()

    if new_disliked == '1':
        new_dislike = Dislike()
        user.user_dislikes.append(new_dislike)
        post.post_dislikes.append(new_dislike)
        post.dislike_number += 1
        db_session.add(new_dislike)
        # remove old like
        old_like = db_session.query(Like).filter(Like.post_id == post_id and Like.user_id == user_id).first()
        if old_like is not None:
            db_session.delete(old_like)
            post.like_number -= 1
        db_session.commit()
        data = {"dislike_post": True}
    else:
        dislike = db_session.query(Dislike).filter(
            Dislike.post_id == post_id and Dislike.user_id == user_id).first()
        post.dislike_number -= 1
        db_session.delete(dislike)
        db_session.commit()
        data = {"dislike_post": False}
    return gen_json_success(data)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
