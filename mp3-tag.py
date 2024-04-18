from music_tag import load_file
from pandas.io.html import read_html
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import wikipedia
import os, argparse

PATH = "./"
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', None)
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', None)

client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def download_image(song: str, directory: str) -> None:
    results = sp.search(q=song, type='track', limit=1)
    img_file = None
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        if track['album']['images']:
            image_url = track['album']['images'][0]['url']
            img_file = os.path.join(directory, f"{song}.jpg")
            try:
                response = requests.get(image_url)
                os.makedirs(os.path.dirname(img_file), exist_ok=True)
                with open(img_file, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded: {img_file}")
            except Exception as e:
                print(f"Error: {e}")
    return img_file

def get_album(title: str, artist: str) -> str:
    try:
        search_results = wikipedia.search(f"{title} {artist} song")
        if not search_results:
            print("Not found")
            return None
        page = wikipedia.page(search_results[0])
        infobox = read_html(page.url, index_col=0, attrs={"class":"infobox"})[0]
        for i,_ in infobox.iterrows():
            if isinstance(i, str) and "from the album" in i:
                return i.removeprefix("from the album ")
    except Exception as e:
        print(f"Error: {e}")

def tag(root: str, file: str) -> None:
    try:
        artist, title = file.removesuffix('.mp3').split(' - ')
        album = get_album(title,artist)
        img = download_image(file.removesuffix('.mp3'), root)

        mp3 = load_file(os.path.join(root, file))
        mp3['title'] = title
        mp3['artist'] = artist
        if album: mp3['album'] = album
        if img:
            with open(img, 'rb') as img_in:
                mp3['artwork'] = img_in.read()
            os.remove(img)

        mp3.save()
        print(f"Title: {title}; Artist: {artist}; Album: {album}")
    except Exception as e:
        print(f"{file} - Error: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Tag .mp3 files.  Required format: '<artists> - <title>.mp3'")
    parser.add_argument('directory', nargs='?', type=str, default=PATH, help='Directory or file to tag')
    args = parser.parse_args()
    for root, _, files in os.walk(args.directory):
        for file in files:
            if file.endswith('.mp3'):
                tag(root, file)
    print("Done")
