from sqlalchemy import Column, String, create_engine, Integer, Date, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
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

class Country(Base):
    __tablename__ = 'country'

    code = Column(String(10), primary_key=True) # csu code
    name = Column(String(50), nullable=False)

    covidcases = relationship('CovidCase', back_populates='country')

class Region(Base):
    __tablename__ = 'region'

    code = Column(String(10), primary_key=True) # nuts code
    name = Column(String(50), nullable=False)

    townships = relationship('Township', back_populates='region')

class Township(Base):
    __tablename__ = 'township'

    code = Column(String(10), primary_key=True) # lau code
    name = Column(String(50), nullable=False)

    region_code = Column(String(10), ForeignKey(Region.code))
    region = relationship(Region, back_populates="townships")

    covidcases = relationship('CovidCase', back_populates='township')

class NeighbourTownship(Base):
    __tablename__ = 'neighbour_township'

    code1 = Column(String(10), ForeignKey(Township.code), primary_key = True)
    code2 = Column(String(10), ForeignKey(Township.code), primary_key = True)

class CovidCase(Base):
    __tablename__ = 'covidcase'

    id = Column(Integer, primary_key=True)

    age = Column(Integer, nullable=False, index=True)
    gender = Column(String(1), CheckConstraint("gender in ('m', 'f')"), nullable=False)
    
    township_code = Column(String(10), ForeignKey(Township.code), nullable=False)
    township = relationship(Township, back_populates="covidcases")

    country_code = Column(String(10), ForeignKey(Country.code), nullable=False)
    country = relationship(Country, back_populates="covidcases")
    
    infected_date = Column(Date, nullable=False, index=True)
    recovered_date = Column(Date, nullable=True)
    death_date = Column(Date, nullable=True)

if __name__ == '__main__':
    Base.metadata.create_all()