from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, Integer, REAL, SmallInteger
from sqlalchemy.orm import relationship, backref

from db.database import Base


class User(Base):
    __tablename__ = 'user'
    user_id = Column(String(20), primary_key=True, index=True)
    password = Column(String(20))
    username = Column(String(50))
    email = Column(String(40))
    has_avatar = Column(SmallInteger, default=0)
    create_time = Column(String(20), default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name is not 'password'}


class Post(Base):
    __tablename__ = 'post'
    post_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(20))
    content = Column(String(500))

    # location related information
    location_description = Column(String(70))

    longitude = Column(REAL)
    latitude = Column(REAL)

    style = Column(Integer)
    like_number = Column(Integer, default=0)
    dislike_number = Column(Integer, default=0)
    comment_number = Column(Integer, default=0)
    has_cipher = Column(SmallInteger, default=0)
    has_picture = Column(SmallInteger, default=0)
    cipher = Column(String(20), default='')
    create_time = Column(String(20), default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    user_id = Column(String(50), ForeignKey('user.user_id'))
    user = relationship(User, backref=backref('posts', uselist=True))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name is not 'cipher'}

    def as_dict_abstract(self):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns if
                c.name is not 'cipher' and c.name is not 'content'}
        temp['content'] = ''
        return temp


class Comment(Base):
    __tablename__ = "comment"
    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(50))
    create_time = Column(String(20), default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dislike_number = Column(Integer, default=0)

    post_id = Column(Integer, ForeignKey('post.post_id'))
    post = relationship(Post, backref=backref('post_comments', uselist=True))
    user_id = Column(String(50), ForeignKey('user.user_id'))
    user = relationship(User, backref=backref('user_comments', uselist=True))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Like(Base):
    __tablename__ = "like"
    like_id = Column(Integer, primary_key=True, autoincrement=True)

    post_id = Column(Integer, ForeignKey('post.post_id'))
    post = relationship(Post, backref=backref('post_likes', uselist=True))
    user_id = Column(String(50), ForeignKey('user.user_id'))
    user = relationship(User, backref=backref('user_likes', uselist=True))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Dislike(Base):
    __tablename__ = "dislike"
    dislike_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('post.post_id'))
    post = relationship(Post, backref=backref('post_dislikes', uselist=True))
    user_id = Column(String(50), ForeignKey('user.user_id'))
    user = relationship(User, backref=backref('user_dislikes', uselist=True))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
