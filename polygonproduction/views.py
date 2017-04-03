from django.shortcuts import render_to_response
from django.http import Http404

from polygonproduction.models import AlbumList, PhotoList, Album, Photo, Cache
import os, logging


def render_pamphlet(request, page=None):
    route = request.path if page is None else page
    basename = os.path.basename(route)
    name, ext = os.path.splitext(basename)
    return render_to_response("%s%s%s" % (name, ".django", ext), {})

def render_albums(request):
    albums = AlbumList().get()
    return render_to_response("albums.django.html", {"albums" : albums})

def render_album(request, album_name):
    PHOTOS_IN_ROW = 5
    try:
        album  = AlbumList().get(album_name)
        photos = PhotoList(album).get()

        table = []
        start = 0
        end   = start + 5

        for i in range(int(round(len(photos) / float(PHOTOS_IN_ROW)))):
            table.append(photos[start:end])
            start = end
            end   = start + 5

    except KeyError:
        raise Http404
    return render_to_response("album.django.html",
                             {"album"  : album,
                              "table" : table,})

def render_photo(request, album_name, photo_id):
    try:
        album      = AlbumList().get(album_name)
        photolist  = PhotoList(album)
        photo      = photolist.get(photo_id)
        next_photo = photolist.next(photo_id)
        prev_photo = photolist.prev(photo_id)
    except KeyError:
        raise Http404
    return render_to_response("photo.django.html",
                              {"album"      : album,
                               "photo"      : photo,
                               "next_photo" : next_photo,
                               "prev_photo" : prev_photo})

def refresh_view(request):
    if Cache.clear_all():
        message = "All cache clear!"
    else:
        logging.error("memcache.flush_all() failed!")
        message = "Refresh failed!  Please try again."
    return render_to_response("refresh.django.html", {"message" : message})
