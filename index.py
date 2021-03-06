import json
import requests
import configparser
from urllib import parse
from bs4 import BeautifulSoup

BASE_URL = "https://terms.naver.com"

config = configparser.ConfigParser()
config.read('config.ini')

translate_table = {
    "상품명": "name",
    "주종": "type",
    "도수": "ABV",
    "용량": "volume",
    "가격": "price",
    "원재료": "ingredients",
    "생산자": "manufacturer",
    "제조사": "manufacturer",
    "대표자명": "owner",
    "주소": "address",
    "연락처": "phone",
    "온라인스토어": "store",
    "홈페이지": "homepage"
}


def get_address_content(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"

    payload = 'query=' + parse.quote(address)

    headers = {
        'Authorization': 'KakaoAK ' + config['SECRET']['kakao'],
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    try:
        document = response.json()['documents'][0]

        return {
            "lat": document["x"],
            "lng": document["y"],
            "province": document["address"]["region_1depth_name"],
            "city": document["address"]["region_2depth_name"],
        }
    except:
        return False


def translate_property_name(property_name):
    try:
        return translate_table[property_name]
    except:
        return False


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
            '#size_ct > div.att_type div.thmb.thmb_border > span > a').get('href')
        image_url = parse.unquote(image_detail_url.split('imageUrl=')[1])
    except:
        image_url = ""

    trs = entry_soup.select(
        '#size_ct > div.att_type div.wr_tmp_profile > div > table > tbody > tr')

    whitelist = ["홈페이지", "온라인스토어"]

    for tr in trs:
        label = normalize_string(tr.select_one('th').text)
        content = normalize_string(tr.select_one('td').text)

        if label == "원재료":
            content = content.split(", ")
        if label == "주소":
            address = get_address_content(content)
            if not address:
                return False
            else:
                content = address
        if label == "주종":
            if content in ["탁주", "생탁주", "살균탁주", "전통 수제 탁주", "생막걸리"]:
                content = "탁주"
            elif content in ["청주", "살균약주", "약주(생약주)", "약주"]:
                content = "약주"
            elif content in ["증류주", "소주", "일반증류주", "증류식소주"]:
                content = "소주/증류주"
            elif content in ["과실주(포도)", "과실주"]:
                content = "과실주"
            elif content in ["리큐르"]:
                content = "리큐르"
            else:
                content = "기타"

        if not translate_property_name(label):
            return False

        if label not in whitelist:
            doc[translate_property_name(label)] = content

    if len(doc.keys()) == 10:
        return doc

# 탁주, 생탁주, 살균탁주, 전통 수제 탁주, 생막걸리 -> 탁주
# 청주, 살균약주, 약주(생약주), 약주 -> 약주
# 증류주, 소주, 일반증류주, 증류식소주 -> 소주/증류주
# 과실주 (포도), 과실주 -> 과실주
# 리큐르 -> 리큐르
# 기타주류, 브랜디 -> 기타


def get_docs(CATEGORY_ID, MAX_PAGE):
    docs = []

    for page_num in range(1, MAX_PAGE):
        page_soup = get_soup(
            f'https://terms.naver.com/list.naver?cid=42726&categoryId={CATEGORY_ID}&page=' + str(page_num))

        titles = page_soup.select(
            '#content > div.list_wrap > ul > li > div.info_area > div.subject > strong > a:nth-child(1)')

        for title in titles:
            print(title.text)
            doc = get_doc(BASE_URL + title.get('href'))
            if doc:
                docs.append(doc)

    return docs


def save_as_json(docs, file_name):
    with open(file_name + ".json", "w", encoding='UTF-8-sig') as file:
        file.write(json.dumps({"data": docs}, ensure_ascii=False))


def read_docs(file_name):
    with open(file_name + ".json", "r", encoding='UTF-8-sig') as file:
        docs = json.load(file)
        return docs['data']


if __name__ == '__main__':
    한국전통주백과 = 58635
    한국전통주백과_max_page = 50
    맥주백과 = 59595

    docs = get_docs(한국전통주백과, 한국전통주백과_max_page)
    # docs = read_docs("./data/전통주")

    save_as_json(docs, "./data/전통주")
