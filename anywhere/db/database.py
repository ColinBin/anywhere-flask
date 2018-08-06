# -*- coding: utf-8 -*-
__author__ = 'Colin'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config import *


engine = create_engine('mysql+mysqlconnector://' + DB_USER + ":" + DB_PASS + "@" + HOST_NAME + ":" + DB_PORT + "/" + DB_NAME)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import db.models
    Base.metadata.create_all(bind=engine)