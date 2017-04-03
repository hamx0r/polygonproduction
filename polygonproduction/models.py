
"""Get data feed from Picasa Web Album and show them on our
own web app.  Requires:
1) gdata-py 1.2.4
2) django 1.0+
"""

from gdata.photos.service import PhotosService
import gdata.urlfetch
import gdata.service
gdata.service.http_request_handler = gdata.urlfetch
#from google.appengine.ext import ndb
from google.appengine.api import memcache
from django.conf import settings
from django.db.models import permalink
import time, logging


# Thumbnail size.
SMALL_THUMB, MID_THUMB, LARGE_THUMB = 0, 1, 2


class StopWatch(object):
    """Use this to measure the wallclock time for
    profiling.  Use it like this:
    sw = StopWatch()
    sw.start()
    ... do something...
    sw.stop()
    print sw.sec_elasped
    """
    def __init__(self):
        self.sec_elapsed = 0
        self._start      = 0

    def start(self):
        self._start = time.clock()

    def stop(self):
        self.sec_elapsed = time.clock() - self._start


class Cache(object):
    """Wrapping AppEngine's memcache API.
    """
    CACHE_TIME = settings.PP_CACHE_TIME

    @staticmethod
    def get(key):
        """Return an item from cache.
        What happen if item is not in cache?"""
        data = memcache.get(key)
        return data

    @classmethod
    def set(cls, key, val):
        """Cache an item for the CACHE_TIME period."""
        memcache.add(key, val, cls.CACHE_TIME)

    @staticmethod
    def clear_all():
        """Clear all memcache data.  Return True if success,
        False if any error.  In that case, try again."""
        logging.info("Clearing all memcache data.")
        return memcache.flush_all()


class PicasaFeed(object):
    """The Picasa API."""
    @staticmethod
    def get_albums():
        data = []
        album_entries = PhotosService().GetUserFeed(user=settings.PP_USERID).entry

        for entry in album_entries:
            if entry.name.text in settings.PP_IGNORED_ALBUMS: continue
            thumb = entry.media.thumbnail[SMALL_THUMB]

            album                 = Album()
            album.id              = entry.GetAlbumId()
            album.name            = entry.name.text
            album.title           = entry.title.text
            album.numphotos       = entry.numphotos.text
            album.updated         = entry.updated.text
            album.cover_url       = thumb.url
            album.cover_width     = int(thumb.width)
            album.cover_height    = int(thumb.height)
            album.photos_feed_uri = entry.GetPhotosUri()

            data.append((album.name, album))
        return data

    @staticmethod
    def get_photos(album_name, photos_feed_uri):
        data = []
        photo_entries = PhotosService().GetFeed(photos_feed_uri).entry

        for i, entry in enumerate(photo_entries):
            thumb = entry.media.thumbnail[MID_THUMB]
            sized_url = entry.content.src.rsplit("/", 1)
            sized_url.insert(-1, "s640")

            photo              = Photo()
            photo.id           = entry.gphoto_id.text
            photo.pos          = i + 1
            photo.caption      = entry.summary.text or ''
            photo.url          = "/".join(sized_url)
            photo.size         = int(entry.size.text)
            photo.width        = int(entry.width.text)
            photo.height       = int(entry.height.text)
            photo.thumb_url    = thumb.url
            photo.thumb_width  = int(thumb.width)
            photo.thumb_height = int(thumb.height)
            photo.album_name   = album_name

            data.append((photo.id, photo))
        return data


class AlbumList(object):
    """A list of albums."""
    def __init__(self):
        """Return a list of tuples (album_name, album_obj)."""
        data = Cache.get("albums")
        if data is None:
            logging.info('Memcache miss on "albums"')
            sw = StopWatch()
            sw.start()
            data = PicasaFeed.get_albums()
            sw.stop()
            logging.info("Called and parsed Picasa user albums feed in %s sec"
                         % sw.sec_elapsed)
            Cache.set("albums", data)
        self._data = data

    def get(self, album_name=None):
        """Return an album object.
        album_name -- a string represents the album id.
        """
        return self._data if album_name is None else dict(self._data)[album_name]


class PhotoList(object):
    """A list of photos."""
    def __init__(self, album):
        """Return a list of tuples (photo_id, photo_obj)."""
        data = Cache.get("photos:%s" % album.name)
        if data is None:
            logging.info('Memcache miss on "photos:%s"' % album.name)
            sw = StopWatch()
            sw.start()
            data = PicasaFeed.get_photos(album.name, album.photos_feed_uri)
            sw.stop()
            logging.info("Called and parsed Picasa photos feed in %s sec"
                         % sw.sec_elapsed)
            Cache.set("photos:%s" % album.name, data)
        self._data = data

    def get(self, photo_id=None):
        """Return a photo object.
        photo_id -- a string represents the photo id
        """
        return self._data if photo_id is None else dict(self._data)[photo_id]

    def next(self, photo_id):
        pos = dict(self._data)[photo_id].pos
        return self._data[pos][1] if pos < len(self._data) else None

    def prev(self, photo_id):
        pos = dict(self._data)[photo_id].pos - 2
        return self._data[pos][1] if pos >= 0 else None


class Album(object):
    """Represents a photo album.

    Properties:
    id           -- a string represents the underlying unique identifier
                    from Picasa.  Use this to query Picasa.
    name         -- a string represents a user friendly unique identifier
                    for our purpose.
    title        -- a string represents the album title
    updated      -- a string represents the last updated date.
                    Ex: "2009-01-25T00:29:12.000Z"
    numphotos    -- an int represents the number of photos
    photos_feed_uri -- a string represents the URI to the photo list feed.
    cover_url    -- a string represents URL to the album cover thumbnail
    cover_height -- an int represents the cover thumbnail height (in pixel)
    cover_width  -- an int represents the cover thumbnail width (in pixel)
    """
    def __init__(self): pass

    @permalink
    def get_absolute_url(self):
        return ("album", [self.name])

    def __str__(self):
        return "<PolygonProduction.Album '%s'>" % self.id

    __repr__ = __str__


class Photo(object):
    """Represents a photo.

    Properties:
    id           -- a string represents the unique identifier
    caption      -- a string represents the photo caption
    url          -- a string represents the URL to the photo
    pos          -- an int represents the position of the photo in the
                    photo list.
    thumb_url    -- a string represents the URL to the thumbnail
    thumb_height -- an int represents the thumbnail's height (in pixel)
    thumb_width  -- an int represents the thumbnail's width (in pixel)
    height       -- an int represents the photo height (in pixel)
    width        -- an int represents the photo width (in pixel)
    size         -- an int represents the photo size (in byte)
    album_name   -- the album this photo belongs to.
    """
    def __init__(self): pass

    @permalink
    def get_absolute_url(self):
        return ("photo", [self.album_name, self.id])

    def __str__(self):
        return "<PolygonProduction.Photo '%s'>" % self.id

    __repr__ = __str__
