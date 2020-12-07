import logging
import os
import re
from graphviz import Digraph
from sqlalchemy import func, and_
from datetime import date, timedelta
from web.core.session import db_session
from web.core.model import Region, Township, Country, CovidCase, NeighbourTownship
import calendar


logger = logging.getLogger('import_data')


class TSInfluence:
    def __init__(self, code, name):
        self.code = code
        self.name = name
        self.cases1 = 0
        self.cases2 = 0

    def get_rep_number(self):
        return 0 if self.cases1 == 0 else self.cases2/self.cases1


def township_influence(month_date='2020-01-01'):
    townships = township_influence_townships(month_date)
    neighbours = township_influence_neighbours()
    township_influence_graph(townships, neighbours)
    return
    for code, ts in townships.items():
        logger.info("{0} rep.num.: {1}".format(code, ts.get_rep_number()))


def township_influence_graph(townships, neighbours, directory=os.path.join(os.path.dirname(__file__), '..', '..', 'work')):
    def _val_to_color(val, step_size):
        colours = ['white', '#fff7ec', '#fee8c8', '#fdd49e', '#fdbb84',
                   '#fc8d59', '#ef6548', '#d7301f', '#b30000', '#7f0000']
        i = 1
        while i <= len(colours):
            if val < step_size * i:
                return colours[i-1]
            i += 1
        return colours[len(colours) - 1]

    f = Digraph('Townships influence graph', filename='township_influence.gv', directory=directory, format="pdf")
    # f.attr(rankdir='LR', size='8,5')

    for code, ts in townships.items():
        f.attr('node', style='filled', color=_val_to_color(ts.get_rep_number(), 0.16))
        f.node(code)

    # f.attr('node', shape='circle')
    for nb in neighbours:  # higher to lower direction
        if townships[nb[0]].get_rep_number() >= townships[nb[1]].get_rep_number():
            f.edge(nb[0], nb[1])
        else:
            f.edge(nb[1], nb[0])
    
    f.render()
    # f.view()


def township_influence_townships(month_date='2020-01-01'):
    if type(month_date) is str:
        month_date = date.fromisoformat(month_date)
    elif type(month_date) is not date:
        raise Exception('invalid date')

    last_day = calendar.monthrange(month_date.year, month_date.month)

    if month_date.month == date.today().month:  # v ramci mesice
        day1 = date.today() + timedelta(days=-12)
        day2 = date.today() + timedelta(days=-6)

        day3 = date.today() + timedelta(days=-7)
        day4 = date.today() + timedelta(days=-1)
    else:
        day1 = date(month_date.year, month_date.month, 1)
        day2 = date(month_date.year, month_date.month, 15)

        day3 = day2
        day4 = date(month_date.year, month_date.month, last_day[1])

    townships = {}
    with db_session() as db:
        for ts in db.query(Township.code, Township.name).all():
            townships[ts.code] = TSInfluence(ts.code, ts.name)
        logger.info("Townships count: {0}".format(len(townships)))
        
        cases_1 = db.query(CovidCase.township_code, func.count(CovidCase.id).label('count')).filter(and_(CovidCase.infected_date >= day1, CovidCase.infected_date <= day2)).group_by(CovidCase.township_code)
        logger.info(cases_1)
        for c1 in cases_1:
            townships[c1.township_code].cases1 = c1.count

        cases_2 = db.query(CovidCase.township_code, func.count(CovidCase.id).label('count')).filter(and_(CovidCase.infected_date > day3, CovidCase.infected_date <= day4)).group_by(CovidCase.township_code)
        logger.info(cases_2)
        for c1 in cases_2:
            townships[c1.township_code].cases2 = c1.count

    return townships

def township_influence_neighbours():
    neighbours = []
    with db_session() as db:
        for tn in db.query(NeighbourTownship.code1, NeighbourTownship.code2).all():
            neighbours.append([tn.code1, tn.code2])
    return neighbours


class TownshipsAveragesCount(object):
    
    def __init__(self, ts):
        self.ts = ts
        self.avg_neighbours = 0
        self.avg_all = 0

    def __str__(self):
        return "{0}: neighbours {1}, all {2}".format(self.ts, self.avg_neighbours, self.avg_all)


def township_influence_averages(townships, neighbours):
    """Count average neigbour difference and average difference between all"""
    assert len(townships) > 1
    ret = []
    all_rep_nums_count = 0
    for code, ts in townships.items():
        print(ts.cases1)
        print(ts.cases2)
        tac = TownshipsAveragesCount(ts)
        all_sum = 0
        for code2, ts2 in townships.items():
            all_sum += abs(ts.get_rep_number() - ts2.get_rep_number())
        tac.avg_all = (all_sum)/(len(townships) - 1)
        nb_cnt = 0
        nb_sum = 0
        for nb in neighbours:
            # print("compare {0} {1} {1}".format(code, nb[0], nb[1]))
            if code == nb[0] or code == nb[1]:
                nb_sum += abs(townships[nb[0]].get_rep_number() - townships[nb[1]].get_rep_number())
                nb_cnt += 1
        logger.debug("nb cnt {0}".format(nb_cnt))
        if nb_cnt > 0:
            tac.avg_neighbours = nb_sum / nb_cnt
            ret.append(tac)
        else:
            logger.error("township without neighbours")
    logger.info("Total results: {0}".format(len(ret)))
    return ret
