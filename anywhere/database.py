# -*- coding: utf-8 -*-
__author__ = 'Colin'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('mysql+mysqlconnector://colin:colin1995@localhost:3306/anywhere')

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)

if __name__=="__main__":

    db_session = sessionmaker()
    db_session.configure(bind=engine)
    Base.metadata.create_all(engine)


