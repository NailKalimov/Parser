from selenium import webdriver
import time
from bs4 import BeautifulSoup
from selenium_stealth import stealth
from curl_cffi import requests
import json


def init_webdriver():
    driver = webdriver.Chrome()
    stealth(driver,
            languages=['en-US', 'en'],
            vendor='Google',
            platform='win32',
            webgl_vendor='Intel Inc.')
    driver.maximize_window()
    return driver


def scrolldown(driver, deep=20):
    for _ in range(deep):
        driver.execute_script('window.scrollBy(0, 500)')
        time.sleep(1)


def get_product_info(url):
    session = requests.Session()

    raw_data = session.get(
        "https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=" + url)
    json_data = json.loads(raw_data.content.decode())

    full_name = json_data['seo']['title']

    if json_data['layout'][0]['component'] == 'userAdultModal':
        product_id = str(full_name.split()[-1])[1:-1]
        print(product_id, full_name)
        return product_id, full_name, 'Товар 18+', None, None
    else:
        description = json.loads(json_data["seo"]["script"][0]["innerHTML"])[
            "description"]
        image_url = json.loads(
            json_data["seo"]["script"][0]["innerHTML"])["image"]
        price = json.loads(json_data["seo"]["script"][0]["innerHTML"])["offers"]["price"] + " " +\
            json.loads(json_data["seo"]["script"][0]["innerHTML"])[
            "offers"]["priceCurrency"]
        product_id = json.loads(
            json_data["seo"]["script"][0]["innerHTML"])["sku"]
        try:
            rating = json.loads(json_data["seo"]["script"][0]["innerHTML"])[
                "aggregateRating"]["ratingValue"]
            rating_counter = json.loads(json_data["seo"]["script"][0]["innerHTML"])[
                "aggregateRating"]["reviewCount"]
        except KeyError:
            rating = None
            rating_counter = None
    return (product_id, full_name, description, price, rating, rating_counter, image_url)


def get_mainpage_cards(driver, url):
    driver.get(url)
    scrolldown(driver)
    main_page_html = BeautifulSoup(driver.page_source, 'html.parser')

    content = main_page_html.find('div', {'class': 'container'})
    content = content.findChildren(recursive=False)[-1].find('div')
    content = content.findChildren(recursive=False)
    content = [item for item in content if 'paginator' in str(item)][-1]
    content = content.find('div').find('div').find('div')
    content = content.findChildren(recursive=False)

    all_cards = []
    cards_in_layer = []
    for layer in content:
        layer = layer.find('div')
        cards = layer.findChildren(recursive=False)

        for card in cards:
            card = card.findChildren(recursive=False)

            card_name = card[2].find(
                'span', {'class': 'tsBody500Medium'}).contents[0]
            card_url = card[2].find('a', href=True)['href']
            # print(card_name, card_url)
            product_url = f"https://www.ozon.ru{card_url}"

            product_id, full_name, description, price, rating, rating_counter, image_url = get_product_info(
                card_url)
            card_info = {product_id: {'short_name': card_name,
                                      'full_name': full_name,
                                      'description': description,
                                      'url': product_url,
                                      'raiting': rating,
                                      'raiting_counter': rating_counter,
                                      'price': price,
                                      'img_url': image_url
                                      }
                         }
            cards_in_layer.append(card_info)
        all_cards.extend(cards_in_layer)
    return all_cards


def get_search_page_cards(driver, url, all_cards=[]):
    driver.get(url)
    scrolldown(driver)
    serarch_page_html = BeautifulSoup(driver.page_source, 'html.parser')
    
    content = serarch_page_html.find('div', {'id':'layoutPage'})
    content = content.find("div")

    content_with_cards = content.find("div", {"class": "widget-search-result-container"})
    content_with_cards = content_with_cards.find("div").findChildren(recursive=False)

    cards_in_page = []

    for card in content_with_cards:
        card_url= card.find("a", href=True)["href"]
        card_name = card.find("span", {"class": "tsBody500Medium"}).contents[0]

        product_url = f"https://www.ozon.ru{card_url}"

        product_id, full_name, description, price, rating, rating_counter, image_url = get_product_info(url=card_url)

        card_info = {product_id: {'short_name': card_name,
                                  'full_name': full_name,
                                  'description': description,
                                  'url': product_url,
                                  'raiting': rating,
                                  'raiting_counter': rating_counter,
                                  'price': price,
                                  'img_url': image_url
                                 }      
        }
        cards_in_page.append(card_info)
        print(card_name, "- parsed")

    return cards_in_page
    # next_content = [div for div in content.find_all("div", href=True) if "Дальше" in str(div)]
    # if not next_content:
        # return cards_in_page
    # else:
    #     next_url = f"https://www.ozon.ru + {next_content[0]["href"]}"
    #     all_cards.extend(get_search_page_cards(driver, next_url, all_cards))
    #     return all_cards


if __name__ == "__main__":
    search_tag = "шнурки"
    url_search = f"https://www.ozon.ru/search/?text={search_tag}&from_global=true"
    driver = init_webdriver()
    with open('parsed_data.json', 'w', encoding='utf-8') as f:
        json.dump(get_search_page_cards(driver, url_search),
                f, ensure_ascii=False, indent=4)
