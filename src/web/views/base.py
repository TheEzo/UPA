
from flask import render_template, request
from flask.views import MethodView
from .second_query_map import get_map
from generate_graphs import generate


class Base(MethodView):
    def get(self):
        tmp = False
        if request.args:
            args = request.args
            generate(args['from'], args['to'], True)
            tmp = True
        return render_template('base.html', map_data=get_map(), tmp='tmp_' if tmp else '')


def configure(app):
    app.add_url_rule('/', view_func=Base.as_view('index'))
