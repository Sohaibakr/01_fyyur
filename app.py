#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask, 
    render_template, 
    request, 
    Response, 
    flash, 
    redirect, 
    url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime
from models import Venue, Artist, Show, db

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
moment = Moment(app)
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    locals = []
    venues = Venue.query.all()

    places = Venue.query.distinct(Venue.city, Venue.state).all()

    for place in places:
        locals.append({
            'city': place.city,
            'state': place.state,
            'venues': [{
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.datetime.now()])
            } for venue in venues if
                venue.city == place.city and venue.state == place.state]
        })
    return render_template('pages/venues.html', areas=locals)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()
    response = {
        "count": len(venues),
        "data": []
    }

    for venue in venues:
        response['data'].append({
            "id": venue.id,
            "name": venue.name,
        })

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)

    # get genres as a list
    genres = venue.genres.replace('{', '').replace('}', '').split(",")

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "upcoming_shows": [],
        "past_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0,
    }

    # get up coming shows only
    upcoming_shows_query = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue.id).filter(Show.start_time > datetime.datetime.now())
    past_shows_query = db.session.query(Show).join(Artist).filter(
        Show.venue_id == venue.id).filter(Show.start_time <= datetime.datetime.now())

    data["upcoming_shows_count"] = upcoming_shows_query.count()
    data["past_shows_count"] = past_shows_query.count()

    for show in upcoming_shows_query.all():
        data["upcoming_shows"].append({
            "artist_id": show.venue.id,
            "artist_name": show.venue.name,
            "artist_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    for show in past_shows_query.all():
        data["past_shows"].append({
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # insert form data as a new Venue record in the db, instead
    form = VenueForm(request.form)
    try:
        venue = Venue()
        form.populate_obj(venue)
        # insert venue
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except ValueError as e:
        # if error roll back
        db.session.rollback()
        # on unsuccessful db insert, flash an error instead.
        print(e)
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')

    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = Venue.query.get(venue_id)
    try:
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        flash('Venue with ID:' + venue_id + ' cannot be deleted')
    finally:
        flash('Venue with ID:' + venue_id + ' has been deleted')
        db.session.close()

    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()

    response = {
        "count": len(artists),
        "data": []
    }

    for artist in artists:
        response['data'].append({
            "id": artist.id,
            "name": artist.name,
        })

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)

    # get genres as a list
    genres = artist.genres.replace('{', '').replace('}', '').split(",")

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0,
    }

    # get up coming shows only
    upcoming_shows_query = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist.id).filter(Show.start_time > datetime.datetime.now())
    past_shows_query = db.session.query(Show).join(Venue).filter(
        Show.artist_id == artist.id).filter(Show.start_time <= datetime.datetime.now())

    data["upcoming_shows_count"] = upcoming_shows_query.count()
    data["past_shows_count"] = past_shows_query.count()
    for show in upcoming_shows_query.all():
        data["upcoming_shows"].append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    for show in past_shows_query.all():
        data["past_shows"].append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    artist = Artist.query.get(artist_id)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    try:
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.genres = request.form.getlist('genres')
        artist.phone = request.form['phone']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']

        db.session.commit()
    except:
        db.session.rollback()
        error = True
        flash('an error occurred, Artist ' +
              artist.id + ' cannot be updated')

    finally:
        db.session.close()

    if not error:
        flash('Artist ' + artist_id + ' has been successfully updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    try:
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.genres = request.form.getlist('genres')
        venue.phone = request.form['phone']
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        db.session.commit()
        flash('Venue ' + venue_id + ' has been successfully updated')
    except:
        db.session.rollback()
        flash('an error occurred, Venue ' + venue_id + ' cannot be updated')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # insert form data as a new Artist record in the db, instead
    form = ArtistForm(request.form)
    try:
        # create new artist object
        artist = Artist()
        form.populate_obj(artist)

        # insert artist
        db.session.add(artist)
        db.session.commit()

        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except ValueError as e:
        print(e)
        # if error roll back
        db.session.rollback()
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # insert form data as a new Show record in the db, instead
    error = False
    form = ShowForm(request.form)
    try:
        show = Show()
        form.populate_obj(show)

        # insert show
        db.session.add(show)
        db.session.commit()
    except:
        # if error roll back
        db.session.rollback()
        error = True
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    # on successful db insert, flash success
    if not error:
        flash('Show was successfully listed!')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
