# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json


import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import VenueForm, ArtistForm, ShowForm, RegistrationForm, LoginForm
import collections
from flask_migrate import Migrate
import sys
from model import Venue,Artist,Show,db,app,bcrypt, User
from datetime import datetime
from flask_login import login_user,login_required,current_user,logout_user


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#





# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    locations = Venue.query.order_by(Venue.state, Venue.city).all()

    for location in locations:
        location_venues = Venue.query.filter_by(state=location.state).filter_by(city=location.city).all()
        venue = []
        for v in location_venues:
            venue.append({
                'id': v.id,
                'name': v.name,
                'num_upcoming_shows': len(
                    db.session.query(Show).filter(Show.venue_id == v.id).filter(Show.start_time > datetime.now()).all())
                    
            })

        data.append({
            'city': location.city,
            'state': location.state,
            'venues': venue
        })

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    search_results = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()

    data = []
    for result in search_results:
        data.append({
            'id': result.id,
            'name': result.name,
            'num_upcoming_shows':
                len(db.session.query(Show).filter(Show.venue_id == result.id).
                    filter(Show.start_time > datetime.now()).all())
        })

    response = {
        'count': len(search_results),
        'data': data,

    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)

    future = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
        Show.start_time <= datetime.now()).all()
    past = \
        db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
            Show.start_time > datetime.now()).all()

    upcoming_shows = []
    past_shows = []

    for show in past:
        past_shows.append({
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    for show in future:
        upcoming_shows.append({
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website_link': venue.website_link,
        'facebook_link': venue.facebook_link,
        'seeking_venue': venue.seeking_venue,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows),
    }

    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False
    try:
        venue = Venue()
        venue.name = request.form.get('name')
        venue.city = request.form.get('city')
        venue.state = request.form.get('state')
        venue.address = request.form.get('address')
        venue.phone = request.form.get('phone')
        venue.genres = request.form.getlist('genres')
        venue.facebook_link = request.form.get('facebook_link')

        db.session.add(venue)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()
        if error:
            flash('An error occurred: Venue ' + request.form['name'] + ' could not be listed')
        else:
            flash('Venue ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()
        if error:
            flash('An error occurred: Venue ' + request.form['name'] + ' could not be deleted')
        else:
            flash('Venue ' + request.form['name'] + ' was successfully deleted!')

    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = db.session.query(Artist).all()

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    search_results = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()

    data = []
    for result in search_results:
        data.append({
            'id': result.id,
            'name': result.name,
            'num_upcoming_shows': len(db.session.query(Show).
                                      filter(Show.artist_id == result.id).
                                      filter(Show.start_time > datetime.now()).all())
        })
    response = {
        'count': len(search_results),
        'data': data
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist = db.session.query(Artist).get(artist_id)

    artist_past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist.id).filter(
        Show.start_time < datetime.now()).all()
    artist_upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist.id).filter(
        Show.start_time >= datetime.now()).all()

    past_shows = []
    upcoming_shows = []

    for show in artist_past_shows:
        past_shows.append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    for show in artist_upcoming_shows:
        upcoming_shows.append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website_link,
        'facebook_link': artist.facebook_link,
        'seeking_talent': artist.seeking_talent,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': past_shows,
        'upcoming_shows': upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count': len(upcoming_shows)
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    # TODO: populate form with fields from artist with ID <artist_id>
    if artist:
        form.name.data = artist.name
        form.genres.data = artist.genres
        form.city.data = artist.city
        form.state.data = artist.state
        form.phone.data = artist.phone
        form.website_link.data = artist.website_link
        form.facebook_link.data = artist.facebook_link
        form.seeking_talent.data = artist.seeking_talent
        form.seeking_description.data = artist.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    error = False
    artist = Artist.query.get(artist_id)

    try:
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = request.form.getlist('genres')
        artist.website_link = request.form['website_link']
        artist.facebook_link = request.form['facebook_link']
        artist.image_link = request.form['image_link']
        artist.seeking_talent = True if 'seeking_talent' in request.form else False
        artist.steeking_description = request.form['seeking_description']
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()
        if error:
            flash('An Error occurred: Artist' + request.form['name'] + ' could not be updated')
        else:
            flash('Artist ' + request.form['name'] + ' was successfully updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    # Appropriately updating venue data from form
    if venue:
        form.name.data = venue.name
        form.genres.data = venue.genres
        form.address.data = venue.address
        form.city.data = venue.city
        form.state.data = venue.state
        form.phone.data = venue.phone
        form.website_link.data = venue.website_link
        form.facebook_link.data = venue.facebook_link
        form.seeking_venue.data = venue.seeking_venue
        form.seeking_description.data = venue.seeking_description

    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    error = False

    # Querying venue information based on venue_id
    venue = Venue.query.get(venue_id)

    try:
        venue.name = request.form['name']
        venue.genres = request.form.getlist('genres')
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.website_link = request.form['website_link']
        venue.facebook_link = request.form['facebook_link']
        venue.image_link = request.form['image_link']
        venue.seeking_venue= True if 'seeking_venue' in request.form['seeking_venue'] else False
        venue.seeking_description = request.form['seeking_description']
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()
        if error:
            flash('Error: Venue {} could not be updated.'.format(venue_id))
        else:
            flash('Venue {} was successfully updated.'.format(venue_id))
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

    error = False

    # Attempting to create artist entry with form information
    try:
            artist = Artist()
            artist.name = request.form.get('name')
            artist.city = request.form.get('city')
            artist.state = request.form.get('state')
            artist.phone = request.form.get('phone')
            artist.genres = request.form.getlist('genres')
            artist.website_link = request.form.get('website_link')
            artist.facebook_link = request.form.get('facebook_link')
            artist.image_link = request.form.get('image_link')
            artist.seeking_talent = request.form.get('seeking_talent')
            artist.seeking_description = request.form.get('seeking_description ')

            db.session.add(artist)
            db.session.commit()
        # Handling error scenarios with rollback
    except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        # CLosing session and showing appropriate message
    finally:
         db.session.close()
         if error:
             flash('Error: Artist {} could not be listed.'.format(request.form['name']))
         else:
             flash('Artist {} was successfully listed!'.format(request.form['name']))

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    all_shows = db.session.query(Show).join(Artist).join(Venue).all()

    # Creating an empty container to append show info to
    data = []

    # Looping through all shows to append show information appropriately
    for show in all_shows:
        data.append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'start_time': show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    error = False

    # Attempting to create show
    try:
        show = Show(
            artist_id = request.form['artist_id'],
            venue_id = request.form['venue_id'],
            start_time = request.form['start_time']
        )

        db.session.add(show)
        db.session.commit()
    # Handling error scenarios with rollback
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    # CLosing session and displaying appropriate information
    finally:
        db.session.close()
        if error:
            flash('An error occurred. Show could not be listed.')
        else:
            flash('Show was successfully listed.')

    # on successful db insert, flash success
    flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')



#  User information
#  ----------------------------------------------------------------
@app.route('/user/register', methods = ['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # creating instance of form
    form = RegistrationForm()
    if request.method == 'POST':
        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        users = User(name=request.form.get('name'), username=request.form.get('username'), email=request.form.get('email'), password=hashed_password)
        db.session.add(users)
        db.session.commit()
        flash(f'Your account has been created you can now login', 'success')
        return redirect(url_for('login_user'))
  
    return render_template('user/register.html', form=form)

@app.route('/user/login', methods = ['GET', 'POST'])
def login_user():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if request.method == "POST"  or request.method == "GET":
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
            login_user()
            next_page = request.args.get('next')
            #terinary conditional in python
            flash('Login successful!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('user/login.html', form=form)



@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
