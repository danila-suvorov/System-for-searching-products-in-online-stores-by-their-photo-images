import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import webbrowser
import re

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class ImageDisplayApp:
    def __init__(self, root, folder_path, json_path):
        self.root = root
        self.root.title("Display Images with Product Info")
        self.image_labels = []  
        self.img_tk_objects = []  
        self.products = self.load_json(json_path)  


        self.scroll_frame = ScrollableFrame(root)
        self.scroll_frame.pack(fill="both", expand=True)

        self.load_images(folder_path)
        for i in range(2):
            self.scroll_frame.scrollable_frame.grid_columnconfigure(i, weight=0)

    def load_json(self, json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                print(f"[DEBUG] Загружено {len(data)} товаров из JSON")
                return data
        except Exception as e:
            print(f"Ошибка при загрузке JSON: {e}")
            return {}

    def load_images(self, folder_path):
        max_cols = 2  
        row = 0
        col = 0
        for filename in os.listdir(folder_path):
            img_path = os.path.join(folder_path, filename)
            if os.path.isfile(img_path) and img_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.display_image(img_path, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 2

    def display_image(self, img_path, row, col):

        try:
            img = Image.open(img_path)
            img.thumbnail((400, 400)) я
            img_tk = ImageTk.PhotoImage(img)


            label = tk.Label(self.scroll_frame.scrollable_frame, image=img_tk)
            label.image = img_tk 
            label.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            self.img_tk_objects.append(img_tk)
            self.image_labels.append(label)

            
            product = self.find_product_by_image(img_path)
            if product:
                self.display_product_info(product, row + 1, col)

        except Exception as e:
            print(f"Ошибка при открытии изображения {img_path}: {e}")

    def find_product_by_image(self, img_path):

        img_filename = os.path.basename(img_path).split('.')[0] 
        for product_id, product in self.products.items():

            if product_id == img_filename: 
                print("img_filename =", img_filename)
                print("keys in JSON =", product_id)
                return product
        return None

    def display_product_info(self, product, row, col):
 
        frame = tk.Frame(self.scroll_frame.scrollable_frame, bd=1, relief="solid")
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        name_label = tk.Label(frame, text=product["name"], font=("Arial", 16, "bold"), wraplength=300)
        name_label.pack()

       
        price_str = product['price'].replace('₽', '').replace(' ', '')  
        price_str = re.sub(r'[^\d]', '', price_str)  
        price = float(price_str) if price_str else 0.0 

        price_label = tk.Label(frame, text=f"Цена: {price} руб.", font=("Arial", 16))
        price_label.pack()

        rating_label = tk.Label(frame, text=f"Рейтинг: {product['rating'].strip()}", font=("Arial", 16))
        rating_label.pack()

        url_button = tk.Button(frame, text="Ссылка на товар", command=lambda: self.open_url(product['link']))
        url_button.pack()

    def open_url(self, url):
        """Открывает URL в браузере."""
        webbrowser.open(url)

def printimages():
    root = tk.Toplevel()
    root.geometry("900x800")
    folder_path = r'C:\Users\Пользователь\PycharmProjects\Diplom\.venv\similar_images'  
    json_path = r'result_Ozon.json'
    app = ImageDisplayApp(root, folder_path, json_path)
    root.mainloop()

printimages()
