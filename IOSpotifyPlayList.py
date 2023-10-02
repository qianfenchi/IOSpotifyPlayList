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
import pyncm.apis
from pyncm.apis.login import LoginViaAnonymousAccount


artist_map = {}

def search_for_track(sp, track_name, artist_name):
  limit = 10
  offset = 0
  test_artist = None
  def fmt(s):
    s = to_simplified(s.replace('夢', '梦').lower())
    return re.sub('[（《「(].*', '', s).strip() if re.sub('[（《「(].*', '', s).strip() else re.sub('[（《「(]', '', s).strip()  
  while True:
    search_ret = sp.search(fmt(track_name), limit=limit, offset=offset)
    search_tracks = search_ret["tracks"]["items"]
    offset += len(search_tracks)
    
    for track in search_tracks:
      test_name  = track["name"]
      test_artist = track["artists"][0]["name"]
      if fmt(test_name) != fmt(track_name): 
        continue
      if artist_name == test_artist or (artist_name in artist_map and artist_map[artist_name] == test_artist):
        return True , track["uri"]
      artist_ret = sp.search(artist_name, type='artist')['artists']['items']
      for artist in artist_ret:
        if artist['name'] == test_artist:
            artist_map[artist_name] = test_artist
            return True, track['uri']
    if offset > 100 or len(search_tracks) < limit:
        break

  print(f"track not found for: {track_name} - {artist_name}")
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
    playlists = sp.user_playlists(user_id, limit=limit, offset=offset)["items"]
    offset += len(playlists)
    for playlist in playlists:
      if playlist["name"].lower() == playlist_name.lower():
        ret = playlist["uri"]
        break
    if len(playlists) < limit:
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
  elif update != True:
    return

  tracks_info = ImData.ReadNetEasePlayList(playlist_url)
  tracks_count = len(tracks_info)
  cnt = 0
  items = []
  url_file = open(playlist_name, 'w', encoding='utf8')
  writer = csv.writer(url_file)
  for track in tracks_info:
    ret,track_uri = search_for_track(sp, track["name"], track["ar"][0]["name"])
    cnt += 1
    if ret and track_uri not in items:
      items.append(track_uri)
      url = pyncm.apis.track.GetTrackAudio(track['id'])['data'][0]['url']
      writer.writerow([track['name'], track['id'], url])
      print(f"Import to \"{playlist_name}\"({cnt} / {tracks_count}) : " + track["name"] + " - " + track["ar"][0]["name"])

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


  LoginViaAnonymousAccount()
  sp = creat_sp()

  with open(args.CSVfile, encoding="utf8", newline='') as f:
    reader = csv.reader((line for line in f if not line.startswith('#')), delimiter=';')
    for row in reader:
      playlist_url, playlist_name, update = row
      update = True if update=='True' else False
      process(sp, playlist_name, playlist_url, update=update)
  
if __name__ == '__main__':
  main()



