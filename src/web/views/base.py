
from flask import render_template
from flask.views import MethodView


class Base(MethodView):
    def get(self):
        return render_template('base.html')


def configure(app):
    app.add_url_rule('/', view_func=Base.as_view('index'))
