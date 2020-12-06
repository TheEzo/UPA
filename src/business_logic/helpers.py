import sys
sys.path.append("..")

from es_dal.elastic import Elastic
from web.core import model
import shutil
import os

def delete_all():
  model.Base.metadata.drop_all()
  model.Base.metadata.create_all()

  es = Elastic()
  es.indices.delete('*')

  work_folder = os.path.join(os.path.dirname(__file__), '..', 'work')
  shutil.rmtree(work_folder, ignore_errors=True)

  if not os.path.exists(work_folder):
      os.makedirs(work_folder)

def get_filename_without_extension(file_path):
    file_basename = os.path.basename(file_path)
    filename_without_extension = file_basename.split('.')[0]
    return filename_without_extension