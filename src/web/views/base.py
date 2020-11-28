
from flask import render_template
from flask.views import MethodView
from .second_query_map import get_map


class Base(MethodView):
    def get(self):
        return render_template('base.html')


class SecondQuery(MethodView):
    def get(self):
        return render_template("second_query.html", map_data=get_map())


def configure(app):
    app.add_url_rule('/', view_func=Base.as_view('index'))
    app.add_url_rule('/secondquery', view_func=SecondQuery.as_view('secondquery'))
