from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('mysql+pymysql://root:root@127.0.0.1/upa')
session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=True,
                                      bind=engine))
session.configure(bind=engine)
Base = declarative_base(bind=engine)
Base.query = session.query_property()


# manual https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/
class Township(Base):
    __tablename__ = 'township'

    code = Column(String(10), primary_key=True)
    region = Column(String(10))


if __name__ == '__main__':
    Base.metadata.create_all()
