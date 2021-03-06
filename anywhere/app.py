# -*- coding: utf-8 -*-
__author__ = 'Colin'
import os
import sys

import flask
from flask import Flask, request, session

from constants import *
from db.database import db_session, init_db
from db.models import *
from util.bound_calculator import get_bound
from util.distance_calculator import haversine
from util.location_description_fetcher import location_to_description
from util.res_json_generator import *

app = Flask(__name__)
app.secret_key = "faffagavvqrq;van;.;vzvqpjoi94751[jz0v"


@app.before_request
def before_request():
    if 'user_id' not in session and request.endpoint not in {'login', 'signup'}:
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


@app.route('/avatar', methods=['GET'])
def avatar():
    if request.method == "GET":
        user_id = session['user_id']
        avatar_path = sys.path[0] + '/avatar/' + user_id + '.png'
        if os.path.exists(avatar_path):
            app.logger.info("%s Avatar file sent.", avatar_path)
            return flask.send_file('avatar/' + user_id + '.png')
        else:
            return ""


@app.route('/basic_information', methods=['GET', 'PUT'])
def basic_information():
    if request.method == "PUT":
        return alter_basic_information()
    elif request.method == "GET":
        return get_basic_information()


def alter_basic_information():
    user_id = session['user_id']
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


def get_basic_information():
    user_id = session['user_id']
    user = db_session.query(User).filter(User.user_id == user_id).first()

    return gen_json_success(user.as_dict())


@app.route('/password', methods=['PUT'])
def password():
    if request.method == "PUT":
        user_id = session['user_id']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        user_found = db_session.query(User).filter(User.user_id == user_id).first()
        if old_password == user_found.password:
            user_found.password = new_password
            db_session.commit()
            app.logger.info("User %s altered password successfully.", user_id)
            return gen_json_success(None)
        else:
            app.logger.info("User %s alter password failure. (%d)", user_id, PASSWORD_WRONG)
            return gen_json_failure(PASSWORD_WRONG)


@app.route('/location_description', methods=['GET'])
def location_description():
    if request.method == "GET":
        longitude = request.args.get("longitude")
        latitude = request.args.get('latitude')
        resp_data = location_to_description(longitude, latitude)
        if resp_data is not None:
            if resp_data['status'] != 'OK':
                app.logger.info("Failed to get location description, API status %s.", resp_data['status'])
                return gen_json_failure(LOCATION_DESCRIPTION_SERVICE_UNAVAILABLE)
            data = dict()
            data['location_description'] = resp_data['results'][0]['formatted_address']
            app.logger.info("Getting location description successfully (%.2f, %.2f)", longitude, latitude)
            return gen_json_success(data)
        else:
            app.logger.info("Failed to get location description (%.2f, %.2f). (%d)", longitude, latitude,
                            LOCATION_DESCRIPTION_SERVICE_UNAVAILABLE)
            return gen_json_failure(LOCATION_DESCRIPTION_SERVICE_UNAVAILABLE)


@app.route('/posts', methods=['POST', 'GET'])
def posts():
    if request.method == "POST":
        return create_post()
    elif request.method == "GET":
        return get_posts()


def create_post():
    user_id = session['user_id']
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


def get_posts():
    longitude = request.args.get('longitude')
    latitude = request.args.get('latitude')
    bound = get_bound(float(latitude), float(longitude), 0.5)

    posts = db_session.query(Post).filter(
        Post.longitude.between(bound['lon_lower_bound'], bound['lon_upper_bound']) & Post.latitude.between(bound[
                                                                                                               'lat_lower_bound'],
                                                                                                           bound[
                                                                                                               'lat_upper_bound']))
    print(bound)
    data = dict()
    data['posts'] = []
    for post in posts:
        if haversine(float(longitude), float(latitude), float(post.longitude), float(post.latitude)) < 500:
            data['posts'].append(post.as_dict_abstract())
    app.logger.info("Getting post around (%.2f, %.2f) successfully.", longitude, latitude)
    return gen_json_success(data)


@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    if request.method == "GET":
        user_id = session['user_id']
        post = db_session.query(Post).filter(Post.post_id == post_id).first()

        if request.args.get('has_cipher') == "1" and post.cipher != request.args.get('cipher'):
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


@app.route('/post_picture', methods=['GET'])
def post_picture():
    if request.method == "GET":
        post_id = request.args.get('post_id')
        post_picture_path = sys.path[0] + '/post_picture/' + str(post_id) + '.png'
        if os.path.exists(post_picture_path):
            app.logger.info("Post pic sent. %s", post_picture_path)
            return flask.send_file('post_picture/' + str(post_id) + '.png')
        else:
            return ""


@app.route('/comments', methods=['POST', "GET"])
def comments():
    if request.method == "POST":
        return add_comment()
    elif request.method == "GET":
        return get_comments()


def get_comments():
    post_id = request.args.get('post_id')
    post = db_session.query(Post).filter(Post.post_id == post_id).first()
    comments = post.post_comments
    comment_list = []
    for comment in comments:
        comment_list.append(comment.as_dict())
    data = {"comments": comment_list}
    return gen_json_success(data)


def add_comment():
    user_id = session['user_id']
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


@app.route('/likes', methods=['PUT'])
def likes():
    if request.method == "PUT":
        user_id = session['user_id']
        post_id = request.form['post_id']
        user = db_session.query(User).filter(User.user_id == user_id).first()
        post = db_session.query(Post).filter(Post.post_id == post_id).first()
        like_found = db_session.query(Like).filter(Like.post_id == post_id and Like.user_id == user_id).first()
        if like_found is None:
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


@app.route('/dislikes', methods=['PUT'])
def dislikes():
    if request.method == "PUT":
        user_id = session['user_id']
        post_id = request.form['post_id']
        user = db_session.query(User).filter(User.user_id == user_id).first()
        post = db_session.query(Post).filter(Post.post_id == post_id).first()
        dislike_found = db_session.query(Dislike).filter(
            Dislike.post_id == post_id and Dislike.user_id == user_id).first()

        if dislike_found is None:
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
