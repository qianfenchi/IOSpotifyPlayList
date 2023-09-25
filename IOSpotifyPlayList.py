from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from imdata import ImData
from urllib import request, parse
import os
import spotipy
import argparse
import datetime
import csv
import re
import string
from chinese_converter import to_simplified

artist_map = {}
with open('artist.csv', encoding='utf8', newline='') as f:
  reader = csv.reader(f)
  for row in reader:
    en, cs = row
    artist_map[en] = cs

artist_set = set()

def search_for_track(sp, track_name, artist_name):
  limit = 10
  offset = 0
  test_artist = None
  def to_cmp(s):
    return to_simplified(re.sub('[（）《》·「」%s\s]'%re.escape(string.punctuation), '', s.lower()))
  while True:
    search_ret = sp.search(track_name, limit=limit, offset=offset)
    search_tracks = search_ret["tracks"]["items"]
    offset += len(search_tracks)
    
    for track in search_tracks:
      test_name  = track["name"]
      if to_cmp(track_name) != to_cmp(test_name):
        continue
      test_artist = track["artists"][0]["name"]
      if test_artist in artist_map:
        test_artist = artist_map[test_artist]
      if to_cmp(artist_name) == to_cmp(test_artist):
        return True , track["uri"]
    if offset > 100 or len(search_tracks) < limit:
        break

  # if offset == 1:
  #   print(f"return the only one track found: {track_name} - {test_artist}")
  #   return True, track["uri"]
  print(f"track not found: {track_name} - {artist_name}")
  artist_set.add(artist_name)
  return False, ""


def creat_sp():
  scope = "playlist-modify-public"
  sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
  return sp

#need to return playlist uri
def create_a_playlist(sp, playlist_name):
  user_id = sp.me()['id']
  ret = sp.user_playlist_create(user_id, playlist_name)
  return ret["uri"]

def get_playlist(sp, playlist_name):
  user_id = sp.me()['id']
  limit = 50
  offset = 0
  ret = None
  while not ret:
    play_lists = sp.user_playlists(user_id, limit=limit, offset=offset)["items"]
    for play_list in play_lists:
      if play_list["name"].lower() == playlist_name.lower():
        ret = play_list["uri"]
        break
    offset += len(play_lists)
    if offset < limit:
        break
  return ret

def add_items_to_playlist(sp, playlist_uri, track_uris, position=None):
  plid = sp._get_id("playlist", playlist_uri)
  ftracks = [sp._get_uri("track", tid) for tid in [track_uris]]
  return sp._post(
         "playlists/%s/tracks" % (plid),
          payload=ftracks,
          position=position,
  )

def process(sp, playlist_name, playlist_url, update=False):
  playlist_id = get_playlist(sp, playlist_name)
  if not playlist_id:
    playlist_id = create_a_playlist(sp, playlist_name)
  elif update != "True":
    return

  tracks_info = ImData.ReadNetEasePlayList(playlist_url)
  tracks_count = len(tracks_info)
  cnt = 0
  items = []
  for track in tracks_info:
    ret,track_uri = search_for_track(sp, track["name"], track["ar"][0]["name"])
    cnt += 1
    if ret and track_uri not in items:
      items.append(track_uri)
      # print(f"Import to \"{playlist_name}\"({cnt} / {tracks_count}) : " + track["name"] + " - " + track["ar"][0]["name"])

  # You can add a maximum of 100 tracks per request
  res = sp.playlist_replace_items(playlist_id, items[:100])
  idx = 100
  while idx < len(items):
    res = sp.playlist_add_items(playlist_id, items[idx:idx+100])
    idx += 100
  
  sp.playlist_change_details(playlist_id, public=True, description=str(datetime.date.today()))
  if "snapshot_id" in res:
    print(f"{len(items)}/{len(tracks_info)} items imported to {playlist_name}")


def get_args():
  parser = argparse.ArgumentParser(description='Move NetEase PlayList into Spotify PlayList')
  parser.add_argument('-csv', '--CSVfile', default="playlists.csv", help='csv file mapping playlists from NetEase to Spotify')
  return parser.parse_args()

def main():
  args = get_args()
  
  if os.getenv("SPOTIPY_CLIENT_ID") == None \
    or os.getenv("SPOTIPY_CLIENT_SECRET") == None \
    or os.getenv("SPOTIPY_REDIRECT_URI") == None :
    if os.path.exists(".env"):
      load_dotenv()
    else:
      print('Please Set or Update your SPOTIPY_CLIENT_ID into enviroment variables')

  sp = creat_sp()

  with open(args.CSVfile, encoding="utf8", newline='') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
      playlist_url, playlist_name, update = row
      process(sp, playlist_name, playlist_url, update='True') # always update for now
  
if __name__ == '__main__':
  main()
  print(artist_set)



