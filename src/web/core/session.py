from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

@contextmanager
def db_session(db_url='mysql+pymysql://root:root@127.0.0.1/upa'):
    """ Creates a context with an open SQLAlchemy session.
    """
    connection = None
    db_session = None

    try:
        engine = create_engine(db_url)
        connection = engine.connect()
        db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
        yield db_session
    except:
        raise
    finally:
        if db_session is not None:
            db_session.close()

        if connection is not None:
            connection.close()
