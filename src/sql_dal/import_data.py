from es_dal.elastic import Elastic
from elasticsearch import Elasticsearch, helpers, exceptions
from web.core.session import db_session
from web.core.model import Region, Township, Country, CovidCase, NeighbourTownship
from sqlalchemy import and_
import logging
import re
import copy
from datetime import date

logger = logging.getLogger('import_data')

def import_countries():
    es = Elastic()

    with db_session() as db:
        codes = set(i[0] for i in db.query(Country.code).all())

        resp = helpers.scan(
            es,
            index = 'states',
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
            index = 'regions',
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
            index = 'neighbours',
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

    gender_map = { 'M': 'm', 'Z': 'f' }

    with db_session() as db:
        resp = helpers.scan(
            es,
            index = 'infected',
            scroll = '3m',
            size = 1000
        )
        
        count = 0

        for doc in resp:
            case = doc['_source']
            
            sex = gender_map.get(case['pohlavi'], None)

            if sex is None:
                continue

            country = 'CZ' if case['nakaza_v_zahranici'] is None else case['nakaza_zeme_csu_kod']

            if case['okres_lau_kod'] == 'CZ099Y' or country is None or len(country) == 0:
                continue

            db.add(CovidCase(age=case['vek'], gender=sex, infected_date=case['datum'], township_code=case['okres_lau_kod'], country_code=country))

            count = count + 1

            if count == 5000:
                count = 0
                db.commit()

        db.commit()

def import_cases_recovered_death():
    es = Elastic()
    sex = {'M': 'm', 'Z': 'f'}

    def _init_data(nosql_index, ages_index, township_code, ages, remaining_rec):
        body = {
                "query": {
                    "bool": {
                        "filter": [
                            { "match":  { "okres_lau_kod": township_code }}
                        ]            
                    }
                },
                "sort": [
                    { "datum": { "order": "asc" }}
                ],
                '_source': ['pohlavi', 'vek', 'datum']
            }

        data = [i['_source'] for i in helpers.scan(
                es,
                index = nosql_index,
                scroll = '3m',
                size = 1000,
                query=body
            )]

        for i, rec in enumerate(data):
            rec['pohlavi'] = sex[rec['pohlavi']]      
            rec['datum'] = date.fromisoformat(rec['datum'])

            if len(remaining_rec) > 0:
                found = (rec['vek'], rec['pohlavi'])        
                if found in remaining_rec:
                    ages[found[0]][found[1]][ages_index] = i
                    remaining_rec.remove(found)

        return data

    def _find_next_match(index, to_search, case, check_date=False):
        if check_date is False:
            for i in range(index + 1, len(to_search)):
                rec = to_search[i]

                if rec['vek'] == case.age and rec['pohlavi'] == case.gender:
                    return i

            return None
        else:
            for i in range(index + 1, len(to_search)):
                rec = to_search[i]

                if rec['vek'] == case.age and rec['pohlavi'] == case.gender and rec['datum'] > case.infected_date:
                    return i

            return None


    with db_session() as db:
        townships = { i[0] : i[1] for i in db.query(Township.code, Township.name).all() }
        township_codes = [i for i in townships.keys()]

        for ts in township_codes:
            cases = db.query(CovidCase).filter(CovidCase.township_code == ts).order_by(CovidCase.infected_date).all()

            ages = { i : {'m': [None, None], 'f': [None, None]} for i in set(case.age for case in cases) }

            remaining_rec = set()
            
            for i in ages.keys():
                remaining_rec.add((i, 'm'))
                remaining_rec.add((i, 'f'))
            
            remaining_dead = copy.deepcopy(remaining_rec)

            recovered = _init_data('recovered', 0, ts, ages, remaining_rec)
            dead = _init_data('dead', 1, ts, ages, remaining_dead)

            not_found_set = remaining_rec & remaining_dead
            for not_found in not_found_set:
                ages[not_found[0]].pop(not_found[1])
            
            for case in cases:
                indexes = ages[case.age].get(case.gender)

                if indexes is None:
                    continue
                
                rec_index, dead_index = indexes

                recovered_date = None if rec_index is None else recovered[rec_index]['datum']
                dead_date = None if dead_index is None else dead[dead_index]['datum']

                if recovered_date is not None and recovered_date <= case.infected_date:
                    rec_index = _find_next_match(rec_index, recovered, case, True)
                    indexes[0] = rec_index
                    recovered_date = None if rec_index is None else recovered[rec_index]['datum']

                if dead_date is not None and dead_date <= case.infected_date:
                    dead_index = _find_next_match(dead_index, dead, case, True)
                    indexes[1] = dead_index
                    dead_date = None if dead_index is None else dead[dead_index]['datum']

                if recovered_date is not None and dead_date is not None:
                    if recovered_date <= dead_date:
                        case.recovered_date = recovered_date
                        indexes[0] = _find_next_match(rec_index, recovered, case)
                    else:
                        case.death_date = dead_date
                        indexes[1] = _find_next_match(dead_index, dead, case)
                else:
                    if recovered_date is not None:
                        case.recovered_date = recovered_date
                        indexes[0] = _find_next_match(rec_index, recovered, case)    
                    elif dead_date is not None:
                        case.death_date = dead_date
                        indexes[1] = _find_next_match(dead_index, dead, case)
                    
                    if indexes[0] is None and indexes[1] is None:
                        ages[case.age].pop(case.gender)
            db.commit()

            yield townships[ts]
            
            

