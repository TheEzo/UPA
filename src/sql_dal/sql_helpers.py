import sys
sys.path.append("..")

from . import import_data as sqlim
from sqlalchemy import func
from web.core.session import db_session
from web.core.model import Township

def import_all(progress_print = print):
    sqlim.import_countries()
    progress_print(f'Země byly importovány do MySQL databáze.')

    sqlim.import_townships_and_regions()
    progress_print(f'Kraje a okresy byly importovány do MySQL databáze.')

    sqlim.import_township_neighbours()
    progress_print(f'Sousedící okresy byly importovány do MySQL databáze.')

    sqlim.import_covid_cases()
    progress_print(f'Záznamy infikovaných osob byly importovány do MySQL databáze.')

    with db_session() as db:
        township_count = db.query(func.count(Township.code)).first()[0]
    
    for township in sqlim.import_cases_recovered_death():
        township_count = township_count - 1
        progress_print(f'Infikovaným v kraji {township} byly přiřazeny datumy vyléčení/úmrtí. Zbývá {township_count} krajů.')