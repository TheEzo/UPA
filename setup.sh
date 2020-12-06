#!/bin/bash

activate () {
  . ./.venv/bin/activate
}

virtualenv -p python3 .venv
activate
pip install -r requirements.txt
