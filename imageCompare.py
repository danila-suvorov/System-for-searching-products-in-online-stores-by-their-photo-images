import os
import shutil
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
def compare_images_main():

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")

    original_image_folder = ''
    comparison_image_folder = ''
    output_folder = ''

    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)


    original_image_path = os.path.join(original_image_folder, 'cropped_image1.jpg')
    original_image = Image.open(original_image_path)

    inputs = processor(images=original_image, return_tensors="pt")
    with torch.no_grad():
        original_features = model.get_image_features(**inputs)


    for filename in os.listdir(comparison_image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(comparison_image_folder, filename)
            try:
                image = Image.open(image_path)


                inputs = processor(images=image, return_tensors="pt")
                with torch.no_grad():
                    image_features = model.get_image_features(**inputs)


                similarity = torch.cosine_similarity(original_features, image_features, dim=-1)

                if similarity.item() > 0.8: 
                    file_name, rash = os.path.splitext(filename)
                    print('Имя файла',file_name)
                    output_image_path = os.path.join(output_folder, file_name+rash)


                    base, extension = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(output_image_path):
                        output_image_path = os.path.join(output_folder, f"{base}_{counter}{extension}")
                        counter += 1

               
                    shutil.copy(image_path, output_image_path)

            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")

    print(f"Найдено {len(os.listdir(output_folder))} похожих изображений")
