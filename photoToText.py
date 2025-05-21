from PIL import Image
import torch
from transformers import BlipProcessor, BlipForQuestionAnswering
from deep_translator import GoogleTranslator
from ultralytics import YOLO
import os
import shutil

processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base", local_files_only=True)
model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base", local_files_only=True)
yolo_model = YOLO("yolov8n.pt")



def detect_center_object(image_path):
    try:
        results = yolo_model(image_path)[0]
        if len(results.boxes) == 0:
            print("YOLO не обнаружил объектов на изображении")
            return None

        image = Image.open(image_path).convert("RGB")
        w, h = image.size
        center_x, center_y = w / 2, h / 2

        min_dist = float("inf")
        target_box = None
        for box in results.boxes.xyxy:
            x1, y1, x2, y2 = box.tolist()
            box_cx = (x1 + x2) / 2
            box_cy = (y1 + y2) / 2
            dist = ((box_cx - center_x) ** 2 + (box_cy - center_y) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                target_box = (int(x1), int(y1), int(x2), int(y2))

        return image.crop(target_box) if target_box else None
    except Exception as e:
        print(f" Ошибка при детекции: {str(e)}")
        return None



def get_object_and_color_caption(image):
    try:
        object_question = "What object is this?"
        object_input = processor(images=image, text=object_question, return_tensors="pt")
        with torch.no_grad():
            object_output = model.generate(**object_input, max_new_tokens=10)
        object_caption = processor.decode(object_output[0], skip_special_tokens=True)

        color_question = f"What color is the {object_caption}?"
        color_input = processor(images=image, text=color_question, return_tensors="pt")
        with torch.no_grad():
            color_output = model.generate(**color_input, max_new_tokens=7)
        color_caption = processor.decode(color_output[0], skip_special_tokens=True)

        return f"{object_caption} in {color_caption}"
    except Exception as e:
        print(f"Ошибка генерации описания: {str(e)}")
        return "unknown object"



def describe_and_save_main_object():
    image_path = ""
    save_folder = ''
    try:

        if not os.path.exists(image_path):
            print(f" Файл {image_path} не найден")

        if os.path.exists(save_folder):
           
            for filename in os.listdir(save_folder):
                file_path = os.path.join(save_folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)  
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  
                except Exception as e:
                    print(f" Ошибка при удалении {file_path}: {e}")
        else:
            os.makedirs(save_folder, exist_ok=True)
       
        os.makedirs(save_folder, exist_ok=True)

        cropped = detect_center_object(image_path)
        if cropped is None:
            print(" Объект не найден или ошибка детекции")


   
        caption_en = get_object_and_color_caption(cropped)
        caption_ru = GoogleTranslator(source="auto", target="ru").translate(caption_en)

        base_name = os.path.basename(image_path)
        file_name = os.path.join(save_folder, f"cropped_{base_name}")

        if os.path.exists(file_name):
            print(f" Файл {file_name} уже существует, будет перезаписан")

        cropped.save(file_name)
        print("\n" + "=" * 40)
        print("EN:", caption_en)
        print("🇷RU:", caption_ru)
        print(f" Сохранено в {file_name}")
        print("=" * 40 + "\n")

    except Exception as e:
        print(f" Критическая ошибка: {str(e)}")
    return caption_ru



describe_and_save_main_object()


