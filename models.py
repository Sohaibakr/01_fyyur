from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String())
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(
        db.String(), default="No seeking for talents")


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String())
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())


class Show(db.Model):
    __tablename__ = 'Shows'
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), primary_key=True)
    start_time = db.Column(db.DateTime, primary_key=True)

    # relations with venue and artists
    # if a venue or an artist is deleted delete all shows related to him
    venue = db.relationship(Venue, backref='shows', cascade="all,delete")
    artist = db.relationship(Artist, backref='shows', cascade="all,delete")