import html
import logging
import sqlite3

from bs4 import BeautifulSoup
from flask import Flask, render_template, request
import requests
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine


DATABASE = r"C:\HADAS\Dropbox\קורס פייתון\sqlite_db\zumba.db"

app = Flask(__name__)


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn


def select_all_data_from_table(table_name):
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    cur.execute(f"SELECT name FROM {table_name} ORDER BY name;")
    all_data = cur.fetchall()
    conn.close()
    return all_data


def insert_simple_data(table_name, object_name):
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    cur.execute(f"INSERT INTO {table_name} (id, name) VALUES ((SELECT MAX(ID) + 1 FROM {table_name}), '{object_name}')")
    conn.commit()
    conn.close()
    return


Base = automap_base()
engine = create_engine("sqlite:///zumba.db")
Base.prepare(engine, reflect=True)
session = Session(engine)
#session.add(Genre(genre="miracle", song=Song(name="miracle2")))
#session.commit()

# collection-based relationships are by default named
# "<classname>_collection"
# print (u1.address_collection)
#u1 = session.query(Song).first()

# Song = Base.classes.songs
# Genre = Base.classes.genres
# Performer = Base.classes.performers

@app.route('/')
def management():
#    Song = Base.classes.songs
#    logging.critical(session.query(Song).first().name)
#    return f'<h1>{session.query(Song).first()}</h1>'
    return render_template(
        'management.html',
    )


@app.route('/manage_simple_table')
def manage_simple_table():
    table_name = request.args.get('selected_table')
    if table_name == 'genres' or table_name == 'performers':
        all_data = select_all_data_from_table(table_name)

        return render_template(
            'simple_management.html',
            display_table_name=table_name[:-1].capitalize(),
            table_name=table_name,
            found_data=all_data
        )


@app.route('/remanage_table/<path:table_name>', methods=['POST'])
def remanage_table(table_name):
    if table_name == 'genres' or table_name == 'performers':
        object_name = request.form['new_object_name']
        insert_simple_data(table_name, object_name)
        all_data = select_all_data_from_table(table_name)

        return render_template(
            'simple_management.html',
            display_table_name=table_name[:-1].capitalize(),
            table_name=table_name,
            found_data=all_data
        )

