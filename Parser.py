import json
import time
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from curl_cffi import requests
from selenium.webdriver.chrome.options import Options
import os
from photoToText import  describe_and_save_main_object
def get_cookies():
    with uc.Chrome(service=ChromeService(ChromeDriverManager().install()),executable_path=executable_path) as driver:
        driver.implicitly_wait(60)
        driver.get("https://www.ozon.ru")
        driver.find_element(By.CSS_SELECTOR, "#stickyHeader")
        user_agent = driver.execute_script("return navigator.userAgent")
        cookies = driver.get_cookies()

    cookies_dict = {i["name"]:i["value"] for i in cookies}

    return user_agent, cookies_dict

user_agent, cookies_dict = get_cookies()
def get_page(text: str, page: int):

    print(f"Parse page: {page}")
    response = requests.get(f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/search/?__rr=1&abt_att=1%5C&from_global=true&layout_container=categorySearchMegapagination&layout_page_index={page}&page={page}&text={text}",
                            cookies=cookies_dict, headers={"user-agent": user_agent},verify=False)



    with open("json.json", "w", encoding="utf-8") as file:
        json.dump(response.json(), file)

    total_pages = json.loads(response.json()["shared"])["catalog"]["totalPages"]

    return response, total_pages

existing_data = []
def get_data_json(response_json):

    result = []


    search_results_key = None
    for key in response_json["widgetStates"].keys():
        if key.startswith("tileGridDesktop"):
            search_results_key = key
            break

    if search_results_key is None:
        print("Ошибка: ключ не найден.")
        return result

    data = json.loads(response_json["widgetStates"][search_results_key])
    print(data)
    for item in data["items"]:
        link = item['action']['link']
        link='https://www.ozon.ru'+link
        link_image = item['tileImage']['items'][0]['image']['link'] if item['tileImage']['items'] else None

        price = ""
        name = ""
        rating = ""

        for info_item in item["mainState"]:

            if info_item["type"] == "priceV2":
                price = info_item["priceV2"]["price"][0]["text"]
            elif info_item["type"] == "textAtom":
                name = info_item["textAtom"]["text"]
            elif info_item["type"] == "labelList":
                rating = info_item['labelList']['items'][0]['title']  

        print("--------")
        print(f"Название: {name}")
        print(f"Цена: {price}")
        print(f"Ссылка: {link}")
        print(f"Ссылка на изображение: {link_image}")
        print(f"Рейтинг: {rating}")

        result.append({
            "name": name,
            "price": price,
            "link": link,
            "link_image": link_image,
            "rating": rating
        })



    existing_data.extend(result)


    ordered_dict = {str(i + 1): item for i, item in enumerate(existing_data)}


    with open("result_Ozon.json", "w", encoding="utf-8") as json_file:
        json.dump(ordered_dict, json_file, ensure_ascii=False, indent=4)


    return result


def main_parser():

    text=describe_and_save_main_object()
    response, total_pages = get_page(text, 1)
    list_items = get_data_json(response.json())

    for page in range(2, 20):
        response = get_page(text, page)[0]
        for i in get_data_json(response.json()):
            list_items.append(i)

