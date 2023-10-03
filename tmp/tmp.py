import os
import csv
from collections import defaultdict


playlists = defaultdict(list)
with open('../playlists.csv', encoding="utf8", newline='') as f:
    reader = csv.reader((line for line in f if not line.startswith('#')), delimiter=';')
    for line in reader:
        _, txt, _ = line
        with open('../'+txt+'.txt', encoding='utf8') as f:
            for line in f:
                name, _, url, image_url = line.strip().split(',') 
                playlists[txt].append(name)
                try:
                    os.system(f'aria2c -o {name}.mp3 {url}')
                    os.system(f'aria2c -o {name}.jpg {image_url}')
                except:
                    pass

for playlist in playlists:
    names = playlists[playlist]
    f = open('mp4.txt', 'w', encoding='utf8')
    for name in names:
        if os.path.exists(name+'.mp3') and os.path.exists(name+'.jpg'):
            os.system(f'ffmpeg -loop 1 -i {name}.jpg -i {name}.mp3 -c:a copy -c:v libx264 -shortest {name}.mp4')
        if os.path.exists(name+'.mp4'):
            f.write(f'file \'{name}.mp4\'\n')

    f.close()
#    os.system(f'ffmpeg -f concat -safe 0 -i mp4.txt -c copy {playlist}.mp4') 
#    os.system(f'youtube-upload --title {playlist} {playlist}.mp4')
