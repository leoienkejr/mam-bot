import requests
from bs4 import BeautifulSoup
import math
import json
import datetime
import time
import tweepy
import random
import shutil
import os

COLLECTION_FILE = 'collection.json'


def update_collection():

    items_per_page = 60
    image = 1
    search_page = 'http://mam.org.br/colecao/'
    USER_AGENT = os.environ.get('USER_AGENT')

    page = requests.get(search_page,
        params={'pp': items_per_page, 'pg': 1, 'i': image},
        headers={'User-Agent': USER_AGENT})

    page = BeautifulSoup(page.text, 'html.parser')
    total_items = page.find('p', {'class': 'search_results_total'})
    total_items = total_items.text
    total_items = int(total_items.split()[0])

    pages_to_search = math.ceil(total_items / items_per_page)

    collection = {}
    collection['collection_size'] = 0
    collection['items'] = []

    for i in range(1, pages_to_search + 1):
        page = requests.get(search_page,
            params={'pp': items_per_page, 'pg': i, 'i': image},
            headers={'User-Agent': USER_AGENT})

        page = BeautifulSoup(page.text, 'html.parser')
        items = page.find_all('li', {'class': 'item_acervo'})
        for item in items:
            new_item = {}
            new_item['artist'] = item.find('a', {'class': 'acervo_artista'}).text
            new_item['title'] = item.find('p', {'class': 'acervo_titulo'}).text
            new_item['year'] = item.find('p', {'class': 'acervo_data'}).text
            new_item['url'] = item.find('a', {'class': 'acervo_detalhes'}).get('href')
            new_item['img_url'] = item.find('img', {'class': 'img-responsive'}).get('src')
            collection['items'].append(new_item)
            collection['collection_size'] += 1

    collection['last_updated'] = str(datetime.datetime.now())
    open(COLLECTION_FILE, mode='w+', encoding='utf8').write(json.dumps(collection, indent=True, ensure_ascii=False))


def save_image(url):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open('image.jpg', 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)


def tweet():
    CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
    ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
    ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET')

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    api = tweepy.API(auth)

    item = open(COLLECTION_FILE, mode='r', encoding='utf8').read()
    item = json.loads(item)
    item = random.choice(item['items'])
    save_image(item['img_url'])

    msg = '{} - {}; {}.'.format(item['title'], item['artist'], item['year'])
    msg = msg + ' #acervomamsp'
    tweet = api.update_with_media('image.jpg', status=msg)
    api.update_status(status=item['url'], in_reply_to_status_id=tweet.id_str)


if __name__ == '__main__':
    update_collection()
    tweets_since_last_update = 0
    while True:
        if tweets_since_last_update < 72:
            tweet()
            tweets_since_last_update += 1
        else:
            tweets_since_last_update = 0
            update_collection()
            tweet()
            tweets_since_last_update += 1
        time.sleep(3600)
