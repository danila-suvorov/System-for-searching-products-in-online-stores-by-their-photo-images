import asyncio
import aiohttp
import aiofiles
import json
import os
from urllib.parse import quote
import photoToText
from contextlib import asynccontextmanager


write_lock = asyncio.Lock()


def clean_string(value):

    if isinstance(value, str):
        return value.encode('utf-8', 'ignore').decode('utf-8').strip()
    return value


def find_basket(product_id):
    vol = product_id // 100000
    baskets = [
        (0, 143, "01"), (144, 287, "02"), (288, 431, "03"),
        (432, 719, "04"), (720, 1007, "05"), (1008, 1061, "06"),
        (1062, 1115, "07"), (1116, 1169, "08"), (1170, 1313, "09"),
        (1314, 1601, "10"), (1602, 1655, "11"), (1656, 1919, "12"),
        (1920, 2045, "13")
    ]
    for start, end, code in baskets:
        if start <= vol <= end:
            return code
    return "01"


async def get_description(session, product_id, basket_number):
    url = f"https://basket-{basket_number}.wbbasket.ru/vol{str(product_id)[:4]}/part{str(product_id)[:6]}/{product_id}/info/ru/card.json"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                description = data.get("description", "")
                return clean_string(description)
            return ""
    except Exception as e:
        print(f"[ERROR] Ошибка описания {product_id}: {str(e)}")
        return ""


async def get_product_list(session, name):
    url = (f"https://search.wb.ru/exactmatch/ru/common/v9/search?"
           f"ab_testing=false&appType=1&curr=rub&dest=-1581689&"
           f"query={quote(name)}&resultset=catalog&sort=popular&spp=30")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        async with session.get(url, headers=headers) as response:
            content = await response.text()
            try:
                data = json.loads(content)
                if "data" in data and "products" in data["data"]:
                    return data["data"]["products"]
                return []
            except json.JSONDecodeError:
                print(f"[ERROR] Невалидный JSON ответ")
                return []
    except Exception as e:
        print(f"[ERROR] Ошибка запроса: {str(e)}")
        return []


async def download_image(session, product_id, basket_number):
    product_id = str(product_id)
    name = f"{product_id}_1.png"
    img_path = f"imgWB/{name}"

    if os.path.exists(img_path):
        return name

    async def try_download(url):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(img_path, "wb") as f:
                        await f.write(content)
                    return True
                return False
        except Exception:
            return False

    base_urls = []
    for basket_num in range(1, 27):
        current_basket = f"{basket_num:02d}"
        templates = [
            f"vol{product_id[:4]}/part{product_id[:6]}",
            f"vol{product_id[:3]}/part{product_id[:5]}",
            f"vol{product_id[:4]}/part{product_id[:5]}",
            f"vol{product_id[:3]}/part{product_id[:6]}"
        ]
        for template in templates:
            base_urls.append(
                f"https://basket-{current_basket}.wbbasket.ru/{template}/{product_id}/images/big/1.webp"
            )

    semaphore = asyncio.Semaphore(50)

    async def fetch(url):
        async with semaphore:
            return (url, await try_download(url))

    tasks = [fetch(url) for url in base_urls]
    results = await asyncio.gather(*tasks)

    for url, result in results:
        if result:
            return name
    return None


def clear_folder(folder_path):
    if os.path.exists(folder_path):
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"[ERROR] Ошибка удаления файла: {str(e)}")
    else:
        os.makedirs(folder_path, exist_ok=True)


async def get_product_info(session, product):
    try:
        product_id = product.get("id")
        if not product_id:
            return None

        basket_number = find_basket(product_id)

        return {
            "product_id": product_id,
            "name": clean_string(product.get("name", "Без названия")),
            "description": await get_description(session, product_id, basket_number),
            "brand": clean_string(product.get("brand", "Неизвестный бренд")),
            "rating": float(product.get("reviewRating", 0)),
            "feedbacks": int(product.get("feedbacks", 0)),
            "price": float(product.get("sizes", [{}])[0].get("price", {}).get("product", 0)),
            "url": f'https://www.wildberries.ru/catalog/{product_id}/detail.aspx'
        }
    except Exception as e:
        print(f"[ERROR] Ошибка информации о товаре: {str(e)}")
        return None


async def save_to_json(file_name, data):
    async with write_lock:
        try:
            async with aiofiles.open(file_name, "r+b") as f:
                try:
                    content = await f.read()
                    existing_data = json.loads(content.decode('utf-8', 'ignore'))
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_data = {}


                cleaned_data = {
                    k: clean_string(v) if isinstance(v, str) else v
                    for k, v in data.items()
                }

                existing_data.update(cleaned_data)

                await f.seek(0)
                await f.write(json.dumps(existing_data, indent=4, ensure_ascii=False).encode('utf-8'))
                await f.truncate()
        except Exception as e:
            print(f"[CRITICAL] Ошибка сохранения: {str(e)}")
            raise


async def process_product(session, product):
    try:
        product_info = await get_product_info(session, product)
        if not product_info:
            return

        required = ["product_id", "name", "price"]
        if any(field not in product_info for field in required):
            return

        image = await download_image(session, product_info["product_id"], product_info.get("basket_number", "01"))
        product_info["image"] = image if image else ""

        await save_to_json("products_urls_dict_WB.json", {
            product_info["product_id"]: product_info
        })

    except Exception as e:
        print(f"[ERROR] Ошибка обработки товара: {str(e)}")


async def process_products_concurrently(session, products, limit=20):
    semaphore = asyncio.Semaphore(limit)

    async def process_with_limit(product):
        async with semaphore:
            return await process_product(session, product)

    await asyncio.gather(*[process_with_limit(p) for p in products])


async def main_func_parse():
    try:

        print("[SYSTEM] Инициализация парсера")
        clear_folder("imgWB")
        async with write_lock:
            async with aiofiles.open("products_urls_dict_WB.json", "wb") as f:
                await f.write(b"{}")
        async with write_lock:
            if not os.path.exists("products_urls_dict_WB.json"):
                async with aiofiles.open("products_urls_dict_WB.json", "wb") as f:
                    await f.write(b"{}")

        name = await asyncio.to_thread(photoToText.describe_and_save_main_object)
        print(f"[SYSTEM] Поиск по запросу: '{clean_string(name)}'")

        async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=100),
                timeout=aiohttp.ClientTimeout(total=60)
        ) as session:
            products = await get_product_list(session, name)
            print(f"[SYSTEM] Найдено товаров: {len(products)}")

            chunk_size = 50
            for i in range(0, len(products), chunk_size):
                chunk = products[i:i + chunk_size]
                await process_products_concurrently(session, chunk)
                print(f"[PROGRESS] Обработано {min(i + chunk_size, len(products))}/{len(products)}")

            print("[SYSTEM] Финализация данных...")
            async with write_lock:
                async with aiofiles.open("products_urls_dict_WB.json", "r+b") as f:
                    content = await f.read()
                    try:
                        data = json.loads(content.decode('utf-8', 'ignore'))
                    except json.JSONDecodeError:
                        data = {}
                    await f.seek(0)
                    await f.write(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8'))
                    await f.truncate()

    except Exception as e:
        print(f"[FATAL] Критическая ошибка: {str(e)}")
    finally:
        print("[SYSTEM] Работа завершена")


if __name__ == "__main__":
    asyncio.run(main_func_parse())
