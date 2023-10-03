import os
import csv


with open('../playlists.csv', encoding="utf8", newline='') as f:
    reader = csv.reader((line for line in f if not line.startswith('#')), delimiter=';')
    for line in reader:
        _, txt, _ = line
        try:
            with open('../'+txt+'.txt', encoding='utf8') as f:
                for line in f:
                    name, _, url, image_url = line.strip().split(',') 
                    os.system(f'aria2c -o {name}.mp3 {url}')
                    os.system(f'aria2c -o {name}.jpg {image_url}')
                    os.system(f'ffmpeg -loop 1 -i {name}.jpg -i {name}.mp3 -c:a copy -c:v libx264 -shortest {name}.mp4')
        except:
            pass
