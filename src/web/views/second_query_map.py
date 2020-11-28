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

colors = ("aliceblue", "antiquewhite", "aqua", "aquamarine", "azure", "beige", "bisque", "black", "blanchedalmond", "blue", "blueviolet", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen", "darkgrey", "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", "darkslategrey", "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray", "dimgrey", "dodgerblue", "firebrick", "floralwhite", "forestgreen", "fuchsia", "gainsboro", "ghostwhite", "gold", "goldenrod", "gray", "green", "greenyellow", "grey", "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender", "lavenderblush", "lawngreen", "lemonchiffon", "lightblue", "lightcoral", "lightcyan", "lightgoldenrodyellow", "lightgray", "lightgreen", "lightgrey", "lightpink", "lightsalmon", "lightseagreen", "lightskyblue", "lightslategray", "lightslategrey", "lightsteelblue", "lightyellow", "lime", "limegreen", "linen", "magenta", "maroon", "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen", "mediumturquoise", "mediumvioletred", "midnightblue", "mintcream", "mistyrose", "moccasin", "navajowhite", "navy", "oldlace", "olive", "olivedrab", "orange", "orangered", "orchid", "palegoldenrod", "palegreen", "paleturquoise", "palevioletred", "papayawhip", "peachpuff", "peru", "pink", "plum", "powderblue", "purple", "red", "rosybrown", "royalblue", "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell", "sienna", "silver", "skyblue", "slateblue", "slategray", "slategrey", "snow", "springgreen", "steelblue", "tan", "teal", "thistle", "tomato", "turquoise", "violet", "wheat", "white", "whitesmoke", "yellow", "yellowgreen")

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

        self.color = 'white'
        self.rep_nb = 0
        self.neighbours_inf = []

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

def get_map():
    with shapefile.Reader(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'SPH_OKRES'), encoding='windows-1250') as shp:
        townships = [TownshipMap(record[2], record[3], shape.points) for record, shape in zip(shp.records(), shp.shapes())]
        
        min_x = min(ts.x_min for ts in townships)
        min_y = min(ts.y_min for ts in townships)
        
        for ts in townships:
            ts.move((-min_x) + 20, (-min_y) + 20)

        max_x = max(ts.x_max for ts in townships)
        max_y = max(ts.y_max for ts in townships)
         
        lines = [f'<svg width="{max_x + 20}" height="{max_y + 20}">']   
        lines.append("""
         <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="2" 
                orient="auto" markerUnits="strokeWidth">
            <path d="M0,0 L0,2 L3,1 z" fill="#f00" />
            </marker>
        </defs>
        """)

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

        townships_infl = township_influence_townships()
        neighbours_infl = township_influence_neighbours()

        for code, ts_infl in townships_infl.items():
            ts = townships[code]
            
            ts.rep_nb = ts_infl.get_rep_number()
            ts.color = _val_to_color(ts.rep_nb, 0.16)

        for nb in neighbours_infl:
            ts1 = townships[nb[0]]
            ts2 = townships[nb[1]]

            if ts1.rep_nb >= ts2.rep_nb:
                ts1.neighbours_inf.append(ts2)
            else:
                ts2.neighbours_inf.append(ts1)

        arrows = []

        for ts in townships.values():
            lines.append(f'<polygon id="{ts.code}" class="okres off" points="{ts.get_path()}" style="fill: {ts.color};" onmousemove="showTooltip(evt, \'{ts.name}\');" onmouseout="hideTooltip();"/>')
            lines.append(f'<text x="{ts.x_middle}" y="{ts.y_middle}" text-anchor="middle" dy="0.2em"font-size="10">{ts.name}</text>')

            for nb in ts.neighbours_inf:
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

                    # mid_x = 0
                    # mid_y = 0

                    # for x, y in same:
                    #     mid_x = mid_x + x
                    #     mid_y = mid_y + y

                    # mid_x = mid_x / len(same)
                    # mid_y = mid_y / len(same)
                    tx = round((med[0] - ts.x_middle) / 1.25)
                    ty = round((med[1] - ts.y_middle) / 1.25)

                    x1 = ts.x_middle
                    y1 = ts.y_middle
                    x2 = ts.x_middle + tx
                    y2 = ts.y_middle + ty

                arrows.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="none" stroke-width="4" marker-end="url(#arrow)" />')

        lines.extend(arrows)
        lines.append('</svg>')
        return "\n".join(lines)