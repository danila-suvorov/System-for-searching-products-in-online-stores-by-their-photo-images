import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import Main_WB
import Main_Ozon
import time
import threading
def upload_and_save_image():

    def clear_images_folder(directory):

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path) 
            except Exception as e:
                print(f"Не удалось удалить файл {file_path}: {e}")

    def save_image(image):
        """Сохранить изображение в папку images под именем image1.jpg."""
        save_dir = "images"
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "image1.jpg")  

        try:
            image.save(save_path) 
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изображение: {e}")


    root = tk.Tk()
    root.title("Загрузка и сохранение изображения")
    root.geometry("400x400")


    image_label = tk.Label(root)
    image_label.pack(pady=10)


    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)

    def upload_image():
        """Загрузить изображение и сохранить его."""
        image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if image_path:
            try:
                uploaded_image = Image.open(image_path)  

              
                clear_images_folder("images")
                save_image(uploaded_image) 

               
                img = uploaded_image.resize((200, 200), Image.LANCZOS)  
                img_tk = ImageTk.PhotoImage(img) 
                image_label.config(image=img_tk)  
                image_label.image = img_tk  

                upload_button.pack_forget()
                wildberries_button.pack(pady=10)  
                ozon_button.pack(pady=10) 

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {e}")

    def parse_wildberries():
    
        print("Запуск парсера Wildberries...")
        import ParserWildberries
        import asyncio
        asyncio.run(ParserWildberries.main_func_parse())
        import imageCompare_WB
        imageCompare_WB.compare_images_main()

        import printimages_WB
        printimages_WB.printimages()




    def parse_ozon():
    
        print("Запуск парсера Ozon...")
        import Parser
        Parser.main_parser()
        import imagefiles
        imagefiles.imagestofile()
        import imageCompare
        imageCompare.compare_images_main()

        import printimages
        printimages.printimages()


    def run_parser(parser_function):
        """Запустить парсер в отдельном потоке."""
        progress_bar.start(10)  
        parser_function()  
        progress_bar.stop()  

    def start_wildberries_parser():
        """Запустить парсер Wildberries в отдельном потоке."""
        threading.Thread(target=run_parser, args=(parse_wildberries,)).start()

    def start_ozon_parser():
        """Запустить парсер Ozon в отдельном потоке."""
        threading.Thread(target=run_parser, args=(parse_ozon,)).start()

    upload_button = tk.Button(root, text="Загрузить изображение", command=upload_image)
    upload_button.pack(pady=10)


    wildberries_button = tk.Button(root, text="Парсинг Wildberries", command=start_wildberries_parser)
    wildberries_button.pack_forget() 


    ozon_button = tk.Button(root, text="Парсинг Ozon", command=start_ozon_parser)
    ozon_button.pack_forget() 

    root.mainloop()
    print("Загрузка и сохранение изображения завершены.")


upload_and_save_image()
