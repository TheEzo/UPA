
import sys
sys.path.append("..")

from flask import render_template, request, redirect, url_for, send_from_directory, current_app as app, Response, g
from flask.views import MethodView
from .second_query_map import get_map
from generate_graphs import generate, generate_townships
import ssl

import json
import os

import pandas as pd
import numpy as np
import urllib
import io
from shutil import copy

import threading
from ..core.session import db_session
from ..core.model import DataConsistency, Township, TownshipReproductionRateCache
from es_dal.fill import fill_data
from pathlib import Path    

from sql_dal import import_data as sqlim
from sql_dal import sql_helpers as sqlhelp
from sqlalchemy import func
from business_logic.custom_query_graph import generate_custom_query

from business_logic.helpers import delete_all, get_filename_without_extension
from sql_dal.township_influence import township_influence_townships

from copy import deepcopy
import datetime

import calendar

ALLOWED_EXTENSIONS = set(['csv', 'json', 'min.json'])
ALLOWED_CODES = {
    'states': ['CHODNOTA', 'ZKRTEXT'],
    'regions': ['CHODNOTA1', 'TEXT1'],
    'neighbours': ['HODNOTA1', 'HODNOTA2'],
    'infected': ['datum', 'vek', 'pohlavi', 'kraj_nuts_kod', 'okres_lau_kod', 'nakaza_v_zahranici', 'nakaza_zeme_csu_kod'],
    'recovered': ['datum', 'vek', 'pohlavi', 'okres_lau_kod'],
    'dead': ['datum', 'vek', 'pohlavi', 'okres_lau_kod']}

folder_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'work')
data_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
context = ssl._create_unverified_context()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def find_file(code, dir_path):
    for fname in os.listdir(dir_path):
        path = os.path.join(dir_path, fname)
        if os.path.isfile(path) and fname.startswith(code):
            return path
            
    return None

def remove_tmp_file(code):
    path = find_file(code, folder_path)

    if path is not None:
        os.remove(path)


def check_json_file(js, code):
    if not 'data' in js:
        raise Exception('JSON neobsahuje klíč \'data\'.')

    if not type(js['data']) is list:
        raise Exception(
            'záznamy musí být uloženy v poli, jehož klíč je \'data\'.')

    if len(js['data']) == 0:
        raise Exception('JSON neobsahuje v poli \'data\' žádné záznamy.')

    headers = [k for k in js['data'][0].keys()]
    missing_columns = set(ALLOWED_CODES[code]) - set(headers)

    if len(missing_columns) > 0:
        raise Exception(f'záznamům chybí klíče {list(missing_columns)}')


def check_csv_file(df, code):
    headers = df.columns.tolist()

    if df.empty:
        raise Exception('soubor neobsahuje žádné záznamy.')

    missing_columns = set(ALLOWED_CODES[code]) - set(headers)

    if len(missing_columns) > 0:
        raise Exception(f'záznamům chybí klíče {list(missing_columns)}')

def _format_sse_message(msg):
    return f'data: {json.dumps(msg)} \n\n'

def download_file(url, code):
    if not code or code not in ALLOWED_CODES:
        yield _format_sse_message({'success': False, 'error': 'Položka nebyla rozpoznána. Obnovte stránku.'})
        return
        
    if type(url) is str:
        try:
            status_code = urllib.request.urlopen(
                url, context=context).getcode()
            if status_code != 200:
                yield _format_sse_message({'success': False, 'error': f'Nepodařilo se stáhnout soubor: chybový návratový kód: {status_code}'})
                return

        except urllib.error.URLError as e:
            yield _format_sse_message({'success': False, 'error': f'Nepodařilo se stáhnout soubor: {str(e.reason)}'})
            return

        remove_tmp_file(code)

        tmp_file_name = os.path.join(folder_path, code)
        with urllib.request.urlopen(url, context=context) as response, open(tmp_file_name, 'wb') as tmp_file:
            length = response.getheader('content-length')
            block_size = 1000000  # default value
            if length:
                length = int(length)
                block_size = max(4096, length // 20)
            buffer_all = io.BytesIO()
            size = 0
            while True:
                buffer_now = response.read(block_size)
                if not buffer_now:
                    break
                buffer_all.write(buffer_now)
                size += len(buffer_now)
                if length:
                    percent = int((size / length)*100)
                    yield _format_sse_message({'success': True, 'progress': percent})
                    
            tmp_file.write(buffer_all.getvalue())
        try:
            parsed_file = pd.read_csv(tmp_file_name, nrows=1) #index_col=0,
            is_csv = True
        except:
            is_csv = False
        if is_csv is False:
            try:
                with open(tmp_file_name) as f:
                    parsed_file = json.load(f)
            except:
                os.remove(tmp_file_name)
                yield _format_sse_message({'success': False, 'error': f'Nepodařilo se rozpoznat formát souboru. Povolené jsou pouze .csv/.json soubory.'})
                return
        try:
            if is_csv:
                check_csv_file(parsed_file, code)
            else:
                check_json_file(parsed_file, code)
        except Exception as e:
            os.remove(tmp_file_name)
            yield _format_sse_message({'success': False, 'error': f'Soubor není validní: {e}'})
            return

        extension = '.csv' if is_csv else '.json'
        os.rename(tmp_file_name, tmp_file_name + extension)
        
        yield _format_sse_message({'success': True})
        return
    else:
        yield _format_sse_message({'success': False, 'error': 'URL chybí nebo není validní.'})
        return
       

importing_thread = None
importing_thread_error = None

def _format_import_msg(msg):
    return "{0}".format(datetime.datetime.now().strftime("%H:%M:%S")) + f': {msg}'


class ImportingThread(threading.Thread):
    def __init__(self):
        self.messages = [_format_import_msg('Import byl spuštěn')]
        super().__init__()

    def run(self):
        global importing_thread_error
        
        try:
            req_files = set(i for i in ALLOWED_CODES.keys())
            files_paths = []

            for _, _, files in os.walk(folder_path):
                for name in files:
                    name_no_ext = get_filename_without_extension(name)

                    if name_no_ext in req_files:
                        files_paths.append(os.path.join(folder_path, name))
                        req_files.remove(name_no_ext)

                        if len(req_files) == 0:
                            break
                break

            if len(req_files) > 0:
                raise Exception(f'Chybí soubory {str(list(req_files))}')
            
            for path in files_paths:
                fill_data(path)
                self.messages.append(_format_import_msg(f'Soubor {Path(path).name} byl nahrán do NoSQL databáze.'))
            
            def _print(msg):
                self.messages.append(_format_import_msg(msg))

            sqlhelp.import_all(progress_print=_print)

            generate()
            generate_custom_query()
            generate_townships()
                
            with db_session() as db:
                imp_row = db.query(DataConsistency).filter(DataConsistency.code == 'import').one()
                db.add(DataConsistency(code='valid'))
                db.delete(imp_row)
                db.commit()
            
        except Exception as e:
            print(str(e))
            importing_thread_error = str(e)
            delete_all()

        global importing_thread
        importing_thread = None

class StartImport(MethodView):
    def get(self):
        global importing_thread
        global importing_thread_error

        req_files = set(i for i in ALLOWED_CODES.keys())

        for _, _, files in os.walk(folder_path):
            for name in files:
                name_no_ext = get_filename_without_extension(name)

                if name_no_ext in req_files:
                    req_files.remove(name_no_ext)

                    if len(req_files) == 0:
                        break
            break
        
        if len(req_files) > 0:
            return {'success': False, 'error': f'Chybí soubory pro {str(list(req_files))}'}
        
        row = DataConsistency(code='import')

        try:
            with db_session() as db:
                db.add(row)
                db.commit()
        except:
            return {'success': False, 'error': f'Již běží jiný import.'}

        try:
            importing_thread = ImportingThread()
            importing_thread_error = None
            importing_thread.start()
        except Exception as e:
            with db_session() as db:
                db.delete(row)
                db.commit()

            importing_thread = None
            return {'success': False, 'error': f'Nepodařilo se spustit vlákno: {str(e)}'}

        return {'success': True}

class DownloadUrl(MethodView):
    def post(self):
        url = request.json['url']
        code = request.json['code']

        return Response(download_file(url, code), mimetype='application/json') #text/event-stream

class Upload(MethodView):
    def post(self):
        file = request.files['file']
        code = request.form['code']

        if not code or code not in ALLOWED_CODES:
            return {'success': False, 'error': 'Položka nebyla rozpoznána. Obnovte stránku.'}

        if file:
            if not allowed_file(file.filename):
                return {'success': False, 'error': 'Soubor má nepodporovaný formát. Povolené jsou pouze csv/json soubory.'}

            else:
                remove_tmp_file(code)
                ext = os.path.splitext(file.filename)[1]

                uploaded_file_path = os.path.join(folder_path, code + ext)
                file.save(uploaded_file_path)

                try:
                    if (ext == '.csv'):
                        df = pd.read_csv(uploaded_file_path, nrows=1)
                        check_csv_file(df, code)
                    else:
                        with open(uploaded_file_path) as f:
                            js = json.load(f)

                        check_json_file(js, code)
                except Exception as e:
                    os.remove(uploaded_file_path)
                    return {'success': False, 'error': f'Soubor není validní: {e}'}

                return {'success': True}
        else:
            return {'success': False, 'error': 'Žádný soubor k nahrání.'}

def copy_data_file(code):
    remove_tmp_file(code)

    orig_file = find_file(code, data_path)

    if orig_file is None:
        raise Exception(f'Výchozí soubor {code} nebyl nalezen.')

    copy(orig_file, folder_path)

class CopyFromData(MethodView):
    def post(self):
        code = request.form['code']

        if not code or code not in ALLOWED_CODES:
            return {'success': False, 'error': 'Položka nebyla rozpoznána. Obnovte stránku.'}
        
        try:
            copy_data_file(code)
        except Exception as e:
            return {'success': False, 'error': str(e)}

        return {'success': True}
        
class Base(MethodView):
    def get(self):
        influence_map = None
        tmp = False
        months=(1, 12)

        if request.args:
            args = request.args
            tmp = True

            from_date = datetime.date.fromisoformat(args['from'])
            to_date = datetime.date.fromisoformat(args['to'])
           
            months = (from_date.month, to_date.month)

            generate(args['from'], args['to'], tmp)
            generate_custom_query(args['from'], args['to'], tmp)
            influence_map = get_map(from_date, to_date)
            
        return render_template('base.html', map_data=influence_map if influence_map else get_map(), months=months, tmp=tmp)


registered_routes = {'/', '/erase', '/status', '/dataloader', '/upload', '/download', '/copy', '/start'}
loader_permitted_routes = {'/dataloader', '/upload', '/download', '/copy', '/start'}

def before_request():
    global registered_routes

    if not request.path in registered_routes:
        return

    if request.path == '/status' and request.method == 'POST':
        return

    with db_session() as db:
        is_importing = db.query(DataConsistency).filter(DataConsistency.code == 'import').first()
        is_valid = db.query(DataConsistency).filter(DataConsistency.code == 'valid').first()
    
    if is_importing is not None:
        if request.path == '/status':
            return
        else:
            return redirect('/status')

    if is_valid is not None:
        if request.path != '/' and request.path != '/erase':
            return redirect('/')
        else:
            return

    global loader_permitted_routes

    if request.path not in loader_permitted_routes:
        return redirect('/dataloader') 

class DataLoader(MethodView):
    def get(self):
        return render_template('data_loader.html')

class ImportStatus(MethodView):
    def get(self):
        return render_template('import_in_process.html')

    def post(self):
        global importing_thread
        global importing_thread_error

        thread = importing_thread
        error = importing_thread_error

        if thread is not None:
            return {'success': True, 'msg': thread.messages[-10:]}
        elif error is not None:
            return {'success': False, 'msg': error}
        else:
            return Response(None, 302)

class EraseData(MethodView):
    def get(self):
        try:
            delete_all()
        except:
            pass

        return redirect('/dataloader')


def configure(app):
    app.add_url_rule('/', view_func=Base.as_view('index'))
    app.add_url_rule('/erase', view_func=EraseData.as_view('erase'))

    app.add_url_rule('/status', view_func=ImportStatus.as_view('import_status'))

    app.add_url_rule('/dataloader', view_func=DataLoader.as_view('data_loader'))
    app.add_url_rule('/upload', view_func=Upload.as_view('file_upload'))
    app.add_url_rule('/download', view_func=DownloadUrl.as_view('file_download'))
    app.add_url_rule('/copy', view_func=CopyFromData.as_view('copy_from_data'))
    app.add_url_rule('/start', view_func=StartImport.as_view('import_start'))
    
    app.before_request(before_request)
