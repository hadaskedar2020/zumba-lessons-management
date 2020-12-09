import datetime
import logging

from flask import Flask, render_template, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, MetaData

DATABASE = r"sqlite:///zumba.db"

app = Flask(__name__)

engine = create_engine(DATABASE)
# Base.prepare(engine, reflect=True)
metadata = MetaData()
metadata.reflect(engine, only=['genres', 'performers', 'songs', 'songs_performers'])
Base = automap_base(metadata=metadata)
Base.prepare()
Song = Base.classes.songs
Genre = Base.classes.genres
Performer = Base.classes.performers
Song_performers = Base.classes.songs_performers


def select_basic_data_from_table(table_name):
    session = Session(engine)
    Table = getattr(Base.classes, table_name)
    all_data = session.query(Table.name).order_by(Table.name).all()
    logging.critical(f"select_basic_data_from_table - {all_data}")
    session.close()
    return all_data


def insert_simple_data(table_name, object_name):
    session = Session(engine)
    Table = getattr(Base.classes, table_name)
    newrow = Table(name=object_name)
    try:
        session.add(newrow)
        session.commit()
        output_message = f"- {object_name} inserted successfully"
    except IntegrityError:
        session.rollback()
        output_message = f"- Error while trying to insert {object_name} - already exists."
    session.close()
    return output_message


def get_table_id_and_description(table_name, exclude_value=None):
    session = Session(engine)
    Table = getattr(Base.classes, table_name)
    if exclude_value is not None:
        all_data = session.query(Table.id, Table.name).filter(Table.id != exclude_value).all()
    else:
        all_data = session.query(Table.id, Table.name).all()
    session.close()
    return all_data


def select_songs_data_from_table():
    session = Session(engine)
    all_data = session.query(Song.id, Song.name, Song.length_seconds, Genre.name, Song.genre_id).order_by(
        Song.name).join('genres').all()
    session.close()
    return all_data


def select_one_songs_data(song_id):
    session = Session(engine)
    song_data = session.query(Song.id, Song.name, Song.length_seconds, Song.length_seconds, Genre.name, Song.genre_id,
                              Song.link).filter_by(id=song_id).join('genres').all()
    logging.critical(f"select_one_songs_data - {song_data}")
    song_performers = session.query(Song_performers.id, Song_performers.performer_id, Performer.name).filter_by(
        song_id=song_id).join('performers').all()
    logging.critical(f"song_performers - {song_performers}")
    session.close()
    return song_data, song_performers


def delete_song_by_id(song_id):
    session = Session(engine)
    obj = session.query(Song).filter_by(id=song_id).first()
    session.delete(obj)
    session.commit()
    session.close()
    return


def update_or_insert_song(mode, song_id, song_name, genre_id, length_seconds, link, add_performer):
    status = 0
    session = Session(engine)
    if mode == 'U':
        try:
            session.query(Song).filter_by(id=song_id).update(
                {"name": song_name, "genre_id": genre_id, "length_seconds": length_seconds, "link": link})
            session.commit()
        except IntegrityError:
            logging.critical(f"update_or_insert_song IntegrityError")
            session.rollback()
            status = 1
    if mode == 'I':
        song = Song(name=song_name, genre_id=genre_id, length_seconds=length_seconds, link=link)
        try:
            session.add(song)
            session.commit()
            session.refresh(song)
            song_id = song.id
        except IntegrityError:
            logging.critical(f"update_or_insert_song IntegrityError")
            session.rollback()
            status = 1
    if add_performer != 'None' and status == 0:
        song_performer = Song_performers(song_id=song_id, performer_id=add_performer)
        session.add(song_performer)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        status = 1
    session.close()
    return status


def search_songs_by_params(genre_id, performer_id):
    session = Session(engine)
    all_data = ""
    if genre_id != "None" and performer_id == "None":
        logging.critical(f"search by genre")
        all_data = session.query(Song.id, Song.name, Song.length_seconds, Genre.name, Song.genre_id).filter_by(genre_id=genre_id).join(Genre).order_by(Song.name).all()
        logging.critical(f"found_songs - {all_data}")
    if genre_id == "None" and performer_id != "None":
        logging.critical(f"search by performer")
        all_data = session.query(Song.id, Song.name, Song.length_seconds, Genre.name, Song.genre_id).join(Genre).join(Song_performers).filter_by(performer_id=performer_id).order_by(Song.name).all()
        logging.critical(f"found_songs - {all_data}")
    if genre_id != "None" and performer_id != "None":
        logging.critical(f"search by performer and genre")
        all_data = session.query(Song.id, Song.name, Song.length_seconds, Genre.name, Song.genre_id).filter_by(genre_id=genre_id).join(Genre).join(Song_performers).filter_by(performer_id=performer_id).order_by(Song.name).all()
        logging.critical(f"found_songs - {all_data}")
    session.close()
    return all_data


def convert_length_seconds_into_minutes(length_seconds):
    length_minutes = str(datetime.timedelta(seconds=float(length_seconds)))
    return length_minutes[-5:]


@app.route('/')
def management():
    return render_template(
        'management.html',
    )


@app.route('/manage_simple_table')
def manage_simple_table():
    table_name = request.args.get('selected_table')
    if table_name == 'genres' or table_name == 'performers':
        all_data = select_basic_data_from_table(table_name)
        return render_template(
            'simple_management.html',
            display_table_name=table_name[:-1].capitalize(),
            table_name=table_name,
            found_data=all_data
        )
    if table_name == 'songs':
        all_data = select_songs_data_from_table()
        return render_template(
            'songs_management.html',
            display_table_name=table_name[:-1].capitalize(),
            table_name=table_name,
            found_data=all_data
        )


@app.route('/remanage_table/<path:table_name>', methods=['POST'])
def remanage_table(table_name):
    if table_name == 'genres' or table_name == 'performers':
        object_name = request.form['new_object_name']
        output_message = insert_simple_data(table_name, object_name)
        all_data = select_basic_data_from_table(table_name)

        return render_template(
            'simple_management.html',
            display_table_name=table_name[:-1].capitalize(),
            table_name=table_name,
            found_data=all_data,
            display_message=output_message
        )


@app.route('/single_song_management/<int:song_id>')
@app.route('/single_song_management', methods=['GET', 'POST'])
def single_song_management(song_id=0):
    all_performes = get_table_id_and_description("performers")
    if song_id == 0:
        song_id = request.args.get('song_id', default=0)
        song_id = int(song_id)
    if song_id > 0:
        song_data, song_performers = select_one_songs_data(song_id)
        genres_data = get_table_id_and_description("genres", song_data[0][5])
        return render_template(
            'one_song_management.html',
            song_id=song_data[0][0],
            song_name=song_data[0][1],
            length_seconds=song_data[0][2],
            song_length=convert_length_seconds_into_minutes(song_data[0][2]),
            song_genre=song_data[0][4],
            genre_id=song_data[0][5],
            song_link=song_data[0][6],
            genres_data=genres_data,
            song_performers=song_performers,
            artists_data=all_performes
        )
    if song_id == 0:
        genres_data = get_table_id_and_description("genres", 0)
        return render_template(
            'one_song_management.html',
            song_id=None,
            genres_data=genres_data,
            artists_data=all_performes
        )


@app.route('/delete_song', methods=['POST'])
def delete_song():
    logging.critical(f"in delete_song")
    song_id = request.form['song_id']
    logging.critical(f"song_id = {song_id}")
    delete_song_by_id(song_id)
    logging.critical(f"after delete_song_by_id")
    all_data = select_songs_data_from_table()

    return render_template(
        'songs_management.html',
        display_table_name='Song',
        table_name='songs',
        found_data=all_data,
        display_message=" - Song was successfully deleted"
    )


@app.route('/update_song', methods=['POST'])
def update_song():
    song_id = request.form['song_id']
    logging.critical(f"song_id: {song_id}")
    song_name = request.form['song_name']
    genre_id = request.form['genre_id']
    link = request.form['link']
    length_seconds = request.form['length_seconds']
    add_performer = request.form['add_performer_0']
    logging.critical(f"add performer: {add_performer}")
    if song_id == 'None':
        mode = 'I'
    else:
        mode = 'U'
    logging.critical(f"Mode: {mode}")
    status = update_or_insert_song(mode, song_id, song_name, genre_id, length_seconds, link, add_performer)
    if status == 0:
        all_data = select_songs_data_from_table()
        return render_template(
            'songs_management.html',
            display_table_name='Song',
            table_name='songs',
            found_data=all_data,
            display_message=" - Song was successfully updated"
        )
    else:
        all_performes = get_table_id_and_description("performers")
        song_data, song_performers = select_one_songs_data(song_id)
        genres_data = get_table_id_and_description("genres", genre_id)
        logging.critical(f"link: {link}")
        return render_template(
            'one_song_management.html',
            song_id=song_id,
            song_name=song_name,
            length_seconds=length_seconds,
            song_length=convert_length_seconds_into_minutes(int(length_seconds)),
            # song_genre=song_genre,
            genre_id=genre_id,
            song_link=link,
            add_performer_0=add_performer,
            genres_data=genres_data,
            song_performers=song_performers,
            artists_data=all_performes,
            display_message=f" - {song_name} - already exists."
        )


@app.route('/song_searcher', methods=['GET'])
def song_searcher():
    logging.critical(f"in song_searcher")
    display_message = ""
    found_data = ""
    mode = request.args.get('mode')
    genre_id = request.args.get('genre_id')
    performer_id = request.args.get('performer_id')
    logging.critical(f"b4 data get, {genre_id}: genre_id")
    all_performes = get_table_id_and_description("performers")
    genres_data = get_table_id_and_description("genres")
    logging.critical(f"after data get")
    if mode == "Search" and performer_id == "None" and genre_id == "None":
       display_message = "- Choose at least 1 search criteria"
    else:
       found_data = search_songs_by_params(genre_id, performer_id)

    return render_template(
        'search_songs.html',
        genres_data=genres_data,
        artists_data=all_performes,
        display_message=display_message,
        found_data=found_data
    )
