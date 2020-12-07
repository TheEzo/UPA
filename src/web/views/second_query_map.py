import shapefile
import math
import copy
import random
import sys
import os

from flask import render_template
# from flask import current_app as app
from flask.views import MethodView
from flask import Flask, make_response
import numpy as np

import sys
sys.path.append("..")

from sql_dal.township_influence import township_influence_townships, township_influence_neighbours
from ..core.session import db_session
from datetime import date
from ..core.model import DataConsistency, Township, TownshipReproductionRateCache
from sqlalchemy import and_

class TownshipMap:
    def __init__(self, code, name, points):
        self.code = code
        self.name = name

        self.x_min = math.inf
        self.y_min = math.inf

        self.x_max = -math.inf
        self.y_max = -math.inf

        self.x_middle = 0
        self.y_middle = 0

        self.points = []
        self.neighbours_inf = dict()

        self.months = dict()

        for i in range(0, len(points), 50):
            x = round(points[i][0] / 300)
            y = round((points[i][1] * (-1)) / 500)

            if x < self.x_min:
                self.x_min = x

            if y < self.y_min:
                self.y_min = y

            if x > self.x_max:
                self.x_max = x

            if y > self.y_max:
                self.y_max = y

            self.x_middle = self.x_middle + x
            self.y_middle = self.y_middle + y

            self.points.append((x, y))

        self.x_middle = self.x_middle / len(self.points)
        self.y_middle = self.y_middle / len(self.points)

    def move(self, x_move, y_move):
        self.x_min = self.x_min + x_move
        self.y_min = self.y_min + y_move 
        
        self.x_max = self.x_max + x_move
        self.y_max = self.y_max + y_move 

        self.x_middle = self.x_middle + x_move
        self.y_middle = self.y_middle + y_move 

        for i, point in enumerate(self.points):
            self.points[i] = (point[0] + x_move, point[1] + y_move)

    def get_path(self):
        return " ".join(f"{point[0]},{point[1]}" for point in self.points)

def get_map(month_from='2020-01-01', month_to='2020-12-01'):
    if type(month_from) is str:
        month_from = date.fromisoformat(month_from)
    elif type(month_from) is not date:
        raise Exception('invalid date')

    if type(month_to) is str:
        month_to = date.fromisoformat(month_to)
    elif type(month_to) is not date:
        raise Exception('invalid date')

    with shapefile.Reader(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'SPH_OKRES'), encoding='windows-1250') as shp:
        townships = [TownshipMap(record[2], record[3], shape.points) for record, shape in zip(shp.records(), shp.shapes())]
        
        min_x = min(ts.x_min for ts in townships)
        min_y = min(ts.y_min for ts in townships)
        
        for ts in townships:
            ts.move((-min_x) + 20, (-min_y) + 20)

        max_x = max(ts.x_max for ts in townships)
        max_y = max(ts.y_max for ts in townships)
         
        def _get_defs(i):
            return """
            <defs>
                <marker 
            """ + f'id="arrow{i}"' + """ markerWidth="10" markerHeight="10" refX="0" refY="2" 
                    orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,2 L3,1 z" fill="#f00" />
                </marker>
            </defs>
            """

        townships = { ts.code : ts for ts in townships }

        def _val_to_color(val, step_size):
            colours = ['white', '#fff7ec', '#fee8c8', '#fdd49e', '#fdbb84',
                   '#fc8d59', '#ef6548', '#d7301f', '#b30000', '#7f0000']
            i = 1
            while i <= len(colours):
                if val < step_size * i:
                    return colours[i-1]
                i += 1
            return colours[len(colours) - 1]

        with db_session() as db:
            cached_ts = db.query(TownshipReproductionRateCache).filter(and_(TownshipReproductionRateCache.month >= month_from, TownshipReproductionRateCache.month <= month_to)).all()

        for cache_ts in cached_ts:
            townships[cache_ts.code].months[cache_ts.month.month] = cache_ts

        neighbours_infl = township_influence_neighbours()

        svg_townships = {i : [f'<svg id="map-{i}" width="{max_x + 20}" height="{max_y + 20}" style="display: none;">', _get_defs(i)] for i in range(month_from.month, month_to.month + 1)}

        for ts in townships.values():
            path = ts.get_path()
            
            for key, cached in ts.months.items():
                repr_rate_cached = cached.reproduction_rate

                svg_townships[key].append(f'<polygon class="okres" points="{path}" style="fill: {_val_to_color(repr_rate_cached, 0.16)};" onmousemove="showTooltip(evt, \'{ts.name}, {repr_rate_cached}\');" onmouseout="hideTooltip();"/>')
                svg_townships[key].append(f'<text x="{ts.x_middle}" y="{ts.y_middle}" text-anchor="middle" dy="0.2em"font-size="10">{ts.name}</text>')    

        def _get_infl_arrow(ts, nb, i):
            same = list(set(ts.points) & set(nb.points))

            if len(same) == 0:
                tx = (nb.x_middle - ts.x_middle) / 3
                ty = (nb.y_middle - ts.y_middle) / 3

                x1 = ts.x_middle
                y1 = ts.y_middle
                x2 = ts.x_middle + tx
                y2 = ts.y_middle + ty
            else:
                same.sort(key=lambda x: math.sqrt(x[0]**2 + x[1]**2))

                med = np.median(same, axis=0)

                tx = round((med[0] - ts.x_middle) / 1.25)
                ty = round((med[1] - ts.y_middle) / 1.25)

                x1 = ts.x_middle
                y1 = ts.y_middle
                x2 = ts.x_middle + tx
                y2 = ts.y_middle + ty

            return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="none" stroke-width="4" marker-end="url(#arrow{i})" />'

        for nb in neighbours_infl:
            ts1 = townships[nb[0]]
            ts2 = townships[nb[1]]

            t1_t2 = None
            t2_t1 = None

            for key, svg in svg_townships.items():
                ts1_cached = ts1.months[key]
                ts2_cached = ts2.months[key]
                
                if ts1_cached.reproduction_rate > ts2_cached.reproduction_rate:
                    if t1_t2 is None:
                        t1_t2 = _get_infl_arrow(ts1, ts2, key)

                    svg.append(t1_t2)
                elif ts1_cached.reproduction_rate < ts2_cached.reproduction_rate:
                    if t2_t1 is None:
                        t2_t1 = _get_infl_arrow(ts2, ts1, key)

                    svg.append(t2_t1)
        
        all_svg = []
        
        for svg in svg_townships.values():
            svg.append('</svg>')
            all_svg.extend(svg)

        return "\n".join(all_svg)