import html
import urllib.parse
import time
import json
import requests
import os
from requests.adapters import HTTPAdapter
import pandas as pd
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

filename = input("Please input the file name in csv:")
df = pd.read_csv(filename)
check_row = 0

STORE = 'pchome'
SESSION_TIMEOUT = 3
SESSION_MAX_RETRIES = 3
PCHOME_API_ENDPOINT = 'http://ecshweb.pchome.com.tw/search/v3.3/all/results?q=%s&sort=rnk&price=%s-%s'
PCHOME_PRODUCT_URL_PREFIX = 'http://24h.pchome.com.tw/prod/'
PCHOME_IMG_URL_PREFIX = 'http://ec1img.pchome.com.tw/'


def get_web_content(query_url):
    session = requests.Session()
    session.mount(query_url, HTTPAdapter(max_retries=SESSION_MAX_RETRIES))
    try:
        # The timeout unit is second.
        resp = session.get(query_url, timeout=SESSION_TIMEOUT)
    except requests.exceptions.RequestException as e:
        print(e)
        return None
    return resp


def collect_items(raw_data):
    extracted_items = list()
    raw_items = raw_data['prods']
    count = 0
    if count <9:
        for raw_item in raw_items:
            try:
                item = dict()
                item['name'] = html.unescape(raw_item['name'])
                item['price'] = int(raw_item['price'])
    #            item['describe'] = raw_item['describe']
    #            item['img_url'] = PCHOME_IMG_URL_PREFIX + raw_item['picB']
                item['url'] = PCHOME_PRODUCT_URL_PREFIX + raw_item['Id']

                col_title = "URL_title_"+ str(count+1)
                df.at[check_row,col_title] = item['name']
                col_url = "URL_"+str(count+1)
                df.at[check_row,col_url] = item['url']
                col_price = "price_"+str(count+1)
                df.at[check_row,col_price] = item['price']
                count = count + 1

                extracted_items.append(item)
            except Exception:
                count = count + 1
                pass
    print (extracted_items)
    return extracted_items


def search_pchome(query, min_price, max_price):
    query = urllib.parse.quote(query)
    query_url = PCHOME_API_ENDPOINT % (query, str(min_price), str(max_price))
    resp = get_web_content(query_url)
    if not resp:
        return []

    resp.encoding = 'UTF-8'
    data = resp.json()
    if data['prods'] is None:
        return []

    total_page_count = int(data['totalPage'])
    if total_page_count == 1:
        return collect_items(data)

    urls = []
    current_page = 1
#    while current_page <= total_page_count:
#        current_page_url = query_url + '&page=' + str(current_page)
#        urls.append(current_page_url)
#        current_page += 1

    items = []
    for url in urls:
        resp = get_web_content(url)
        if resp:
            resp.encoding = 'UTF-8'
            items += collect_items(resp.json())
    return items


def save_search_result(data):
    with open('test.json', 'w+', encoding='UTF-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def main(query_str):
#    query_str = 'ASUS RT-AC68U'
    min_price = 100
    max_price = 40000
    items = search_pchome(query_str, min_price, max_price)
    today = time.strftime('%m-%d')
    print('Search item \'%s\' from %s...' % (query_str, STORE))
    print('Search %d records on %s' % (len(items), today))
    for item in items:
        print(item)
    data = {
        'date': today,
        'store': STORE,
        'items': items
    }
    print (df)
#    save_search_result(data)


for row in df.iterrows():
    query_str = df.at[check_row,'model']
    main(query_str)
    time.sleep(5)
    check_row = check_row + 1

filename_prefix = input ('Enter filename prefix (brand e.g.): ')
df.to_csv (str(filename_prefix+'_'+'router_tw_price_updated.csv'),index=False,header=True)
print (filename_prefix + " TW Price Update Mission Completed")