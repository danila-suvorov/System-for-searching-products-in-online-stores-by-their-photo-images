import json
import requests
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_image(image_url, image_name, images_folder):

    try:
        response = requests.get(image_url)
        response.raise_for_status()  

      
        image_path = os.path.join(images_folder, f"{image_name}.jpg")

    
        with open(image_path, 'wb') as img_file:
            img_file.write(response.content)

        return image_path 

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке изображения {image_url}: {e}")
        return None  

def imagestofile():
    
    json_file_path = ''
  
    images_folder = 'downloaded_images'

 
    if os.path.exists(images_folder):
        shutil.rmtree(images_folder)
    os.makedirs(images_folder)

   
    with open(json_file_path, 'r', encoding='utf-8') as file:
        products = json.load(file)


    downloaded_images = []

 
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for key, product in products.items():  
            image_url = product.get('link_image')

            if image_url:
          
                futures.append(executor.submit(download_image, image_url, key, images_folder)) 

  
        for future in as_completed(futures):
            result = future.result()
            if result:
                downloaded_images.append(result)

    print(f"Загружено изображений: {len(downloaded_images)}")


