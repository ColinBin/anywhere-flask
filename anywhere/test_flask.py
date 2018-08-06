import json
import os
import tempfile

import pytest
from werkzeug.http import parse_cookie

from app import app
from constants import *
from db.database import *
from tools.random_generator import get_random_sha

user_signup_test_case = dict(user_id='Bob', password=get_random_sha(), username="bob", email="bob@gmail.com")
user_test_case = {k: v for (k, v) in user_signup_test_case.items() if k != 'password'}

new_post_test_case = dict(post_title="Test Post", post_content="this post is for testing purpose only",
                          location_description="default location", longitude=123.41, latitude=50, post_style=1,
                          has_cipher=0, post_cipher="", has_picture=0)


# check if all required fields are set in cookies
def cookie_fields(cookies, fields):
    s = len(fields)
    for cookie in cookies:
        c_key, c_value = list(parse_cookie(cookie).items())[0]
        if c_key in fields:
            s -= 1
    return s == 0


# get value of field in cookies
def get_cookie_field(cookies, field):
    for cookie in cookies:
        c_key, c_value = list(parse_cookie(cookie).items())[0]
        if c_key == field:
            return c_value
    assert False


# check if sub is a subset of sup
def sub_dict_match(sub, sup):
    for k, v in sub.items():
        if k not in sup or sup[k] != v:
            return False
    else:
        return True


# check if user's information matches
def entity_info_match(res, sub):
    res_json = get_json(res)
    return ~null_data(res_json) and sub_dict_match(sub, res_json['data'])


def get_json(res):
    return json.loads(res.data.decode('utf8').replace("'", '"'))


def status_success(res):
    return res['status'] == SUCCESS


def status_failure(res):
    return res['status'] == FAILURE


def null_data(res):
    return status_success(res) and 'data' in res and res['data'] is None


def data_val(res, d):
    return status_success(res) and ~null_data(res) and sub_dict_match(d, res['data'])


def errcode(res, error_code):
    return status_failure(res) and ~null_data(res) and 'err_code' in res['data'] and res['data'][
        'err_code'] == error_code


def signup_and_login(client):
    client.post('/signup',
                data=user_signup_test_case)
    res = client.post('/login',
                      data=dict(user_id=user_signup_test_case['user_id'], password=user_signup_test_case['password']))
    set_session_cookie(client, get_cookie_field(res.headers.getlist('Set-Cookie'), 'session'))


def set_session_cookie(client, val):
    client.set_cookie(key='session', value=val,
                      server_name=HOST_NAME)


def expire_session_cookie(client):
    client.set_cookie(key='session', value="",
                      server_name=HOST_NAME, expires="1900-1-1")


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        init_db()
    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def test_signup(client):
    res = client.post('/signup',
                      data=user_signup_test_case)
    assert null_data(get_json(res))
    res = client.post('/signup',
                      data=user_signup_test_case)
    assert errcode(get_json(res), USER_ALREADY_EXIST)


def test_login(client):
    client.post('/signup',
                data=user_signup_test_case)
    res = client.post('/login', data=dict(user_id=user_signup_test_case['user_id'],
                                          password=user_signup_test_case['password'] + "1"))
    assert errcode(get_json(res), PASSWORD_WRONG)
    res = client.post('/login',
                      data=dict(user_id=user_signup_test_case['user_id'], password=user_signup_test_case['password']))
    assert data_val(get_json(res), user_test_case) and cookie_fields(
        res.headers.getlist('Set-Cookie'), {'session'})
    res = client.post('/login', data=dict(user_id='Jack', password=user_signup_test_case['password']))
    assert errcode(get_json(res), USER_NOT_FOUND)


def test_get_basic_information(client):
    signup_and_login(client)
    res = client.post('/get_basic_information')
    assert entity_info_match(res, user_test_case)


def test_alter_basic_information(client):
    signup_and_login(client)
    new_email = "new_" + user_test_case['email']
    altered_info = dict(user_id=user_test_case['user_id'], username=user_test_case['username'], email=new_email,
                        has_altered_avatar='0')
    res = client.post('/alter_basic_information', data=altered_info)
    assert null_data(get_json(res))
    res = client.post('/get_basic_information')
    assert entity_info_match(res, {key: value for (key, value) in altered_info.items() if key != 'has_altered_avatar'})
    user_test_case['email'] = new_email


def test_alter_password(client):
    signup_and_login(client)
    new_pass = get_random_sha()
    res = client.post('/alter_password',
                      data={'original_password': user_signup_test_case['password'] + "1", 'new_password': new_pass})
    assert errcode(get_json(res), PASSWORD_WRONG)
    res = client.post('/alter_password',
                      data={'original_password': user_signup_test_case['password'], 'new_password': new_pass})
    assert null_data(get_json(res))

    old_pass = user_signup_test_case['password']
    user_signup_test_case['password'] = new_pass
    expire_session_cookie(client)

    res = client.post('/login', data=dict(user_id=user_signup_test_case['user_id'], password=old_pass))
    assert errcode(get_json(res), PASSWORD_WRONG)
    res = client.post('/login',
                      data=dict(user_id=user_signup_test_case['user_id'], password=user_signup_test_case['password']))
    assert data_val(get_json(res), user_test_case)


def test_get_location_description(client):
    signup_and_login(client)
    res = client.post('/get_location_description', data=dict(longitude=181.0, latitude=39.0))
    assert errcode(get_json(res), LOCATION_DESCRIPTION_SERVICE_UNAVAILABLE)
    res = client.post('/get_location_description', data=dict(longitude=116.0, latitude=39.0))
    assert status_success(get_json(res)) and ~null_data(get_json(res))


def test_post(client):
    signup_and_login(client)
    res = client.post('/create_post', data=new_post_test_case)
    assert null_data(get_json(res))

    res = client.post('/get_posts',
                      data=dict(longitude=new_post_test_case['longitude'], latitude=new_post_test_case['latitude']))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and len(get_json(res)['data']['posts']) == 1

    post_id = get_json(res)['data']['posts'][0]['post_id']

    res = client.post('/get_post_detail',
                      data=dict(post_id=post_id, has_cipher=new_post_test_case['has_cipher']))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and get_json(res)['data']['post'] is not None

    res = client.post('/get_comments',
                      data=dict(post_id=post_id))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and len(get_json(res)['data']['comments']) == 0

    res = client.post('/add_comment',
                      data=dict(post_id=post_id, comment_content="This is Test Comment."))
    assert status_success(get_json(res)) and ~null_data(get_json(res))

    res = client.post('/get_comments',
                      data=dict(post_id=post_id))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and len(get_json(res)['data']['comments']) == 1

    res = client.post('/like_post',
                      data=dict(post_id=post_id))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and get_json(res)['data']['like_post'] is True

    res = client.post('/like_post',
                      data=dict(post_id=post_id))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and get_json(res)['data']['like_post'] is False

    res = client.post('/dislike_post',
                      data=dict(post_id=post_id))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and get_json(res)['data']['dislike_post'] is True

    res = client.post('/dislike_post',
                      data=dict(post_id=post_id))
    assert status_success(get_json(res)) and ~null_data(get_json(res)) and get_json(res)['data'][
        'dislike_post'] is False
