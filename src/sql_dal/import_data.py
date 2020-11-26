from es_dal.elastic import Elastic
from elasticsearch import Elasticsearch, helpers, exceptions
from web.core.session import db_session
from web.core.model import Region, Township, Country, CovidCase, NeighbourTownship
from sqlalchemy import and_
import logging
import re


logger = logging.getLogger('import_data')

def import_countries():
    es = Elastic()

    with db_session() as db:
        codes = set(i[0] for i in db.query(Country.code).all())

        resp = helpers.scan(
            es,
            index = 'staty',
            scroll = '3m',
            size = 10,
            query={'_source': ['CHODNOTA', 'ZKRTEXT']}
        )
        
        for doc in resp:
            code = doc['_source']['CHODNOTA']
            name = doc['_source']['ZKRTEXT']

            if code is None or len(code) == 0 \
                or name is None or len(name) == 0 \
                or code in codes:
                continue

            codes.add(code)
            db.add(Country(code=code, name=name))

        db.commit()

def import_townships_and_regions():
    es = Elastic()

    with db_session() as db:
        region_codes = set(i[0] for i in db.query(Region.code).all())
        township_codes = set(i[0] for i in db.query(Township.code).all())

        resp = helpers.scan(
            es,
            index = 'kraje_a_okresy',
            scroll = '3m',
            size = 10,
            query={'_source': ['CHODNOTA1', 'TEXT1', 'CHODNOTA2', 'TEXT2']}
        )
        
        for doc in resp:
            reg_code = re.search(r'CZ0\d\d', doc['_source']['CHODNOTA1'])
            reg_name = doc['_source']['TEXT1']
            
            if reg_code is None or reg_name is None or len(reg_name) == 0:
                continue
            
            reg_code = reg_code.group()

            if reg_code not in region_codes:
                region_codes.add(reg_code)
                db.add(Region(code=reg_code, name=reg_name))

            ts_code = re.search(r'CZ0\d\d[\d|A-Z]', doc['_source']['CHODNOTA2'])
            ts_name = doc['_source']['TEXT2']

            if ts_code is None or ts_name is None or len(ts_name) == 0:
                continue

            ts_code = ts_code.group()

            if ts_code not in township_codes:
                township_codes.add(ts_code)
                db.add(Township(code=ts_code, name=ts_name, region_code=reg_code))

        db.commit()
    
def import_township_neighbours():
    es = Elastic()

    with db_session() as db:
        resp = helpers.scan(
            es,
            index = 'sousedni_okresy',
            scroll = '3m',
            size = 10,
            query={'_source': ['HODNOTA1', 'HODNOTA2']}
        )

        townships = db.query(Township.code, Township.name)

        for doc in resp:
            name_1 = doc['_source']['HODNOTA1']
            name_2 = doc['_source']['HODNOTA2']

            if name_1 is None or len(name_1) == 0 or name_2 is None or len(name_2) == 0:
                logger.error("Invalid data in 'sousedni_okresy'")
                continue
            
            ts_1 = townships.filter(Township.name == name_1)
            ts_2 = townships.filter(Township.name == name_2)

            if ts_1.first() is None or ts_2.first() is None:
                logger.error("Invalid data in 'sousedni_okresy', not existing township")
                continue

            db.add(NeighbourTownship(code1=ts_1.first().code, code2=ts_2.first().code))
        
        db.commit()

def import_covid_cases():
    es = Elastic()

    # if 'CZ099Y' not in township_codes: # mimo uzemi cr

    with db_session() as db:
        resp = helpers.scan(
            es,
            index = 'osoby',
            scroll = '3m',
            size = 1000
        )
        
        for doc in resp:
            case = doc['_source']
            
            sex = 'm' if case['pohlavi'] == 'M' else 'f'
            country = 'CZ' if case['nakaza_v_zahranici'] is None else case['nakaza_zeme_csu_kod']

            if case['okres_lau_kod'] == 'CZ099Y' or country is None:
                continue

            db.add(CovidCase(age=case['vek'], gender=sex, infected_date=case['datum'], township_code=case['okres_lau_kod'], country_code=country))

        db.commit()

def import_cases_recovered_death():
    es = Elastic()

    sex = {'m': 'M', 'f': 'Z'}

    with db_session() as db:
        for age, gender, township_code in db.query(CovidCase.age, CovidCase.gender, CovidCase.township_code).group_by(CovidCase.age, CovidCase.gender, CovidCase.township_code):
            body = {
                "query": {
                    "bool": {
                        "filter": [
                            { "match":  { "okres_lau_kod": township_code }},
                            { "match":  { "pohlavi": sex[gender] }},
                            { "match":  { "vek": age }},
                        ]            
                    }
                },
                "sort": [
                    { "datum": { "order": "asc" }}
                ],
                '_source': ['datum']
            }

            recovered_dead = [(i['_source']['datum'], True) for i in helpers.scan(
                es,
                index = 'vyleceni',
                scroll = '3m',
                size = 1000,
                query=body
            )]

            recovered_dead.extend((i['_source']['datum'], False) for i in helpers.scan(
                es,
                index = 'umrti',
                scroll = '3m',
                size = 1000,
                query=body
            ))

            recovered_dead.sort(key=lambda x: x[0])

            cases = db.query(CovidCase) \
                .filter(and_(CovidCase.age == age, CovidCase.gender == gender, CovidCase.township_code == township_code)) \
                .order_by(CovidCase.infected_date)

            for case, final_date in zip(cases, recovered_dead):
                if final_date[1] is True:    
                    case.recovered_date = final_date[0]
                else:
                    case.death_date = final_date[0]

            db.commit()
            
            

