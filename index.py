import json
from urllib import parse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://terms.naver.com"


def translate_property_name(property_name):
    translate_table = {"상품명": "name", "주종": "type",
                       "도수": "ABV", "용량": "volume", "가격": "price",
                       "원재료": "ingredients", "제조사": "manufacturer", "대표자명": "owner",
                       "주소": "address", "연락처": "phone", "온라인스토어": "store",
                       "홈페이지": "homepage"}

    try:
        return translate_table[property_name]
    except:
        return property_name


def get_soup(url):
    req = requests.get(url)
    html = req.text
    return BeautifulSoup(html, 'html.parser')


def normalize_string(text):
    return ' '.join(text.strip().replace("\n", "").split())


def get_term_source(text):
    return normalize_string(text.split('termSource')[
        1].split('hasNotNewAudioInfra')[0].split('</strong>')[1].split('">')[1].split("</p>',")[0].replace("</a>", ""))


def get_doc(url):
    doc = {}
    entry_soup = get_soup(url)

    script = entry_soup.select_one('#termBody > script:nth-child(5)')
    script_text = script.string
    term_source = get_term_source(script_text)

    image_url = None
    try:
        image_detail_url = entry_soup.select_one(
            '#size_ct > div.att_type > div > div.thmb.thmb_border > span > a').get('href')
        image_url = parse.unquote(image_detail_url.split('imageUrl=')[1])
    except:
        image_url = ""

    trs = entry_soup.select(
        '#size_ct > div.att_type div.wr_tmp_profile > div > table > tbody > tr')
    for tr in trs:
        label = normalize_string(tr.select_one('th').text)
        content = normalize_string(tr.select_one('td').text)
        if label == "원재료":
            content = content.split(", ")
        doc[translate_property_name(label)] = content

    doc["source"] = term_source
    doc["image"] = image_url

    return doc


def get_docs():
    docs = []

    for page_num in range(1, 38):
        page_soup = get_soup(
            'https://terms.naver.com/list.naver?cid=42726&categoryId=58635&page=' + str(page_num))

        titles = page_soup.select(
            '#content > div.list_wrap > ul > li > div.info_area > div.subject > strong > a:nth-child(1)')

        for title in titles:
            print(title.text)
            doc = get_doc(BASE_URL + title.get('href'))
            docs.append(doc)

    return docs


def save_as_json(docs, file_name):
    with open(file_name + ".json", "w", encoding='UTF-8-sig') as file:
        file.write(json.dumps({"data": docs}, ensure_ascii=False))


if __name__ == '__main__':
    docs = get_docs()
    save_as_json(docs, "data")
