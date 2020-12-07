import datetime
import sys
sys.path.append("..")

from . import import_data as sqlim
from sqlalchemy import func
from web.core.session import db_session
from web.core.model import Township, TownshipReproductionRateCache
from .township_influence import township_influence_townships

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

    year = datetime.date.today().year

    for month in range(1, 13):
        month_date = datetime.date(year, month, 1)
        townships_infl = township_influence_townships(month_date)

        rows = []

        for code, ts_infl in townships_infl.items():
            rows.append(TownshipReproductionRateCache(code=code, month=month_date, reproduction_rate=round(ts_infl.get_rep_number(), 1)))

        with db_session() as db:
            db.bulk_save_objects(rows)
            db.commit()

        progress_print(f'Spočteny reprodukční čísla pro {month}. měsíc.')