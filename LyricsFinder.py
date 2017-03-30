# -*- coding: utf-8 -*-
"""
Created on Thu Mar 16 17:20:40 2017

@author: Charlie Vincent

Give an artist name

Grab all their albums from the spotify API

Grab all the tracks from those albums

Get the Genius track URL via the Genius API

scrape the lyrics via BeautifulSoup4
"""

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import json
import time
import urllib


def get_spotify_data(artist_name):
    params = {"q": artist_name, "type": "artist"}
    r_spotify_search = requests.get('https://api.spotify.com/v1/search', params=params)

    JSON_artist_search = r_spotify_search.json()

    artist_info = JSON_artist_search["artists"]["items"][0]
    spotify_artist_id = artist_info["id"]

    # get that artists' albums GET https://api.spotify.com/v1/artists/{id}/albums
    params_albums = {"limit": 50}
    r_spotify_artist_albums = requests.get("https://api.spotify.com/v1/artists/{}/albums".format(spotify_artist_id),
                                           params=params_albums)
    JSON_artist_albums = r_spotify_artist_albums.json()["items"]
    albums = {}
    for album in JSON_artist_albums:
        if album["album_type"] == "album" and album["name"].strip() not in albums:
            if "(" or "[" in album:
                albums[album["name"].split("(")[0].strip()] = album["id"]
            else:
                albums[album["name"].strip()] = album["id"]

    albums_df = pd.DataFrame.from_dict(albums, orient="index")
    albums_df.columns = ["id"]

    # get the albums tracks GET https://api.spotify.com/v1/albums/{id}/tracks
    albums_df["Tracks"] = None
    for i, album_id in enumerate(albums_df.id):
        params_tracks = {"limit": 30}
        r_get_spotify_tracks = requests.get("https://api.spotify.com/v1/albums/{}/tracks".format(album_id),
                                            params=params_tracks)

        JSON_tracks = r_get_spotify_tracks.json()["items"]
        track_list = []
        for track in JSON_tracks:
            track_list.append(track["name"].split("-")[0].strip())
        albums_df["Tracks"][i] = pd.DataFrame(track_list, columns=["Track Names"])

    return albums_df


def getGeniusURL(artist_name, artist_df):
    ACCESS_TOKEN = "yzgdmuWobHrplHaxzH5MjQ0x9QzFirG8j1R3eiHmBNHtNSKxPGWvEBWwyBVd9qby"
    # search track by track
    for album_df in artist_df.Tracks:
        album_df["Genius URL"] = None
        for i, track_name in enumerate(album_df["Track Names"]):
            # search track by track in Genius API GET /search
            params = {"q": artist_name + " " + track_name, "access_token": ACCESS_TOKEN}

            print(params)
            r_Genius_search = requests.get("https://api.genius.com/search", params).json()

            try:
                genius_url = r_Genius_search["response"]["hits"][0]["result"]["url"]

                if r_Genius_search["response"]["hits"][0]["result"]["primary_artist"]["name"] != artist_name:
                    print(r_Genius_search["response"]["hits"][0]["result"]["primary_artist"]["name"])
                    raise Exception
            except:
                print("Track not found")
                continue
            print(genius_url)

            album_df["Genius URL"].iloc[i] = genius_url

    return artist_df


def scrapeLyrics(genius_URL):
    header = {
        "User Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}

    r_genius_url = requests.get(genius_URL, headers=header)

    html_text = r_genius_url.text
    soup = BeautifulSoup(html_text, "html.parser")
    lyrics = soup.find("lyrics").get_text()
    lyrics = lyrics.replace("\n", " ").replace('"', "'")

    return lyrics


if __name__ == "__main__":

    artist_name = input("Enter an Artist:")

    albums_and_tracks = get_spotify_data(artist_name)

    albums_and_tracks = getGeniusURL(artist_df=albums_and_tracks, artist_name=artist_name)

    for tracks_df in albums_and_tracks.Tracks:
        tracks_df["Lyrics"] = None
        for i, URL in enumerate(tracks_df["Genius URL"]):
            if URL:
                lyrics = scrapeLyrics(URL)
                tracks_df.Lyrics.iloc[i] = scrapeLyrics(URL)
