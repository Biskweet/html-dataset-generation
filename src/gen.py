import json
import os
from time import time
import random
import subprocess
import threading
import numpy as np
from PIL import Image

from . import utils


class Generator:
    input_types = [     # number    index
        "button",       # 0         0  
        # "carousel",     # 1   
        "checkbox",     # 2         1
        "header",       # 3         2
        "image",        # 4         3
        "label",        # 5         4
        "link",         # 6         5
        # "pagination",   # 7
        "paragraph",    # 8         6
        "radio",        # 9         7
        "select",       # 10        8
        # "table",        # 11
        "textarea",     # 12        9
        "textbox"       # 13        10
    ]

    def __init__(self, args):
        if len(args) not in (3, 4) and args[1] != "multiple":
            print("Too many or no input file provided. Please provide one JSON \
                  data file for the generation (and optionally one destination file).")
            raise SystemExit("Aborting.")


        # Single file generation
        if (args[1] == "single"):
            try:
                with open(args[2], "r") as file:
                    content = file.read()
                    self.data = json.loads(content)
            except Exception as e:
                print("File", args[2], "was not found, has wrong data format or \
                       is corrupted. Please check your input file.", e)
                raise SystemExit("Aborting.")

        # Multiple file generation
        elif (args[1] == "multiple"):
            self.data = []
            try:
                for file in args[2:]:
                    with open(file, "r") as f:
                        content = f.read()
                        self.data.append(json.loads(content))
            except Exception:
                print("File was not found, has wrong data format or is \
                       corrupted. Please check your input files.")
                raise SystemExit("Aborting.")

        # Setting img file destination with custom/default
        # Trimming the destination file name to remove the extension
        self.dest = args[3].split('.')[0] if (len(args) == 4 and args[1] == "single") else "./image"


    @staticmethod
    def generate_html_2(data):
        data = data.get("data")

        if data is None:
            print("Incorrect input")
            raise SystemExit("Aborting.")

        # Verifying presence of `wkhtmltoimage`
        with open(os.devnull, "wb") as devnull:
            try:
                subprocess.check_call(["wkhtmltoimage", "-V"], stdout=devnull, stderr=subprocess.STDOUT)
            except Exception:
                print("Package wkhtmltoimage is not installed!")
                raise SystemExit("Aborting.")

        # Defining the CWD to avoid calling it multiple times later
        cwd = os.getcwd()

        # Beginning webpage
        document = """
        <!DOCTYPE html>
        <head>
            <style>
                @font-face {
                    font-family: 'Libre Baskerville';
                    src: url('/home/gaspard/Documents/Prog/html-dataset-generation/tests/fonts/Libre_Baskerville.ttf');
                }
                @font-face {
                    font-family: Kalam;
                    src: url('/home/gaspard/Documents/Prog/html-dataset-generation/tests/fonts/Kalam.ttf');
                }
                @font-face {
                    font-family: Kaushan;
                    src: url('/home/gaspard/Documents/Prog/html-dataset-generation/tests/fonts/Kaushan.ttf');
                }
                @font-face {
                    font-family: 'Letters for learners';
                    src: url('/home/gaspard/Documents/Prog/html-dataset-generation/tests/fonts/Letters_for_learners.ttf');
                }
                @font-face {
                    font-family: Roboto;
                    src: url('/home/gaspard/Documents/Prog/html-dataset-generation/tests/fonts/Roboto.ttf');
                }
                body{
                    padding: 0;
                    margin: 0;
                    border: 0;
                }
            </style>
        </head>
        <body>"""

        for element in data:
            elem_type = element.get("type")
            content = element.get("content")
            # name = element.get(   "name")
            # value = element.get("value")

            # Coordinates and size are required arguments. If they do not
            # exist, the program will crash.
            try:
                coord = element["coordinates"]["x"], element["coordinates"]["y"]
            except KeyError:
                print("No coordinates found in file")
                raise SystemExit("Aborting.")

            height, width = (
                element["coordinates"]["height"],  # x-pos
                element["coordinates"]["width"]    # y-pos
            )

            font = ''
            if elem_type in ("label", "link", "paragraph", "button", "header", "select"):
                font = random.choice(utils.FONTS)

            # We start filling the document from there
            document += f"<div style='position:absolute;left:{coord[0]}px;top:{coord[1]}px'>"

            if elem_type in ("checkbox", "radio"):
                document += f"<input type='{elem_type}' style='width:{width};height:{height}'>"

            elif elem_type == "button":
                document += f"<input type='button' style='width:{width}px;height:{height}px;font-family:{font}' value='{content}'>"

            elif elem_type == "textbox":
                document += f"<input type='textbox' style='width:{width-3}px;height:{height-3}px'>"

            elif elem_type == "image":
                document += f"<img src='{cwd}/src/cross.svg'style='transform-origin:top left;transform:scale({width}, {height-15})'>"

            elif elem_type == "label":
                document += f"<label style='font-size:{min(height, 20)}px;font-family:{font}'>Label</label>"

            elif elem_type == "link":
                document += f"<a href style='font-size:{min(height, 20)}px;font-family:{font}'>Link</a>"

            elif elem_type == "header":
                document += f"<h1 style='font-family:{font}'>Header</h1>"

            elif elem_type == "paragraph":
                document += f"<textarea style='width:{width}px;height:{height}px;border:none;resize:none;overflow:hidden;font-family:{font}'>{content}</textarea>"

            elif elem_type == "textarea":
                document += f"<textarea style='width:{width-5}px;height:{height-5}px;overflow:scroll'></textarea>"

            elif elem_type == "select":
                document += f"<select style='width:{width}px;height:{height}px;font-family:{font}'><option>Select</option></select>"

            document += "</div>"

        document += "</html>"

        return document


    @staticmethod
    def generate_json(amount, lower_elem_bound=1, upper_elem_bound=10, xmax=500, ymax=500, dimmin=10, dimmax=200):
        for i in range(amount):
            print(f"Generated {i+1}/{amount} JSON files.", end="\r")
            elements = {"data": []}
            nbelem = random.randint(lower_elem_bound, upper_elem_bound)

            for _ in range(nbelem):
                # Generating valid, non-overlapping dimensions for each element
                elem_type = random.choice(Generator.input_types)

                # Generating base random data
                width, height, posx, posy = utils.generate_random(elem_type, dimmin, dimmax, xmax, ymax)

                while utils.has_collision(posx, posy, width, height, elements["data"]):
                    width, height, posx, posy = utils.generate_random(elem_type, dimmin, dimmax, xmax, ymax)

                if elem_type == "paragraph":
                    content = utils.generate_text_content()
                elif elem_type == "button":
                    content = utils.generate_text_content(length=random.randint(1, 3))
                else:
                    content = "content"


                elements["data"].append({
                    "type": elem_type,
                    "value": "value",
                    "name": "name",
                    "content": content,
                    "coordinates": {"x": posx, "y": posy, "width": width, "height": height}
                })

            with open(f"./jsons/{str(i).zfill(len(str(amount)))}.json", "w") as file:
                json.dump(elements, file)

        print()


    @staticmethod
    def generate_dataset(size):
        Generator.generate_json(size)

        args = [None, "multiple"]
        args += list(map(lambda filename: "./jsons/" + filename, sorted(os.listdir("./jsons/."))))
        app = Generator(args)
        done = [False]
        app.generate_multiple_images(done)
        while not done[0]:
            time.sleep(0.5)

        app.generate_labels()

        print("\n\nDone.")


    def generate_labels(self):
        for i, page in enumerate(self.data):
            page_data = page["data"]
            filename = str(i).zfill(len(str(len(self.data))))

            with open(f"./labels/{filename}.txt", "w") as file:
                img = Image.open(f"./images/{filename}.jpg")

                for elem in page_data:
                    category_id = Generator.input_types.index(elem["type"])
                    width = elem["coordinates"]["width"] / img.width
                    height = elem["coordinates"]["height"] / img.height
                    center_x = (elem["coordinates"]["x"] + (elem["coordinates"]["width"] / 2)) / img.width
                    center_y = (elem["coordinates"]["y"] + (elem["coordinates"]["height"] / 2)) / img.height

                    center_x = min(1, center_x)
                    center_y = min(1, center_y)

                    file.write(f"{category_id} {center_x} {center_y} {width} {height}\n")

            print(f"\rGenerated {i+1}/{len(self.data)} labels.", end=" ")


    def generate_image(self, page=None, dest=None):
        filename = dest or self.dest
        html = Generator.generate_html_2(page or self.data)
        with open(f"./htmls/{filename}.html", "w") as file: file.write(html)
        error = os.system(f"wkhtmltoimage --enable-local-file-access ./htmls/{filename}.html ./images/{filename}.jpg")
        if error:
            print("Error while converting the HTML.")


    def generate_multiple_images(self, done=[False]):
        """
        Calls the `generate_image` func on each element of the data list.
        Does not allow to set a destination file.
        """

        # Creating N threads to generate data faster
        threads = []
        
        # cpu_count = psutil.cpu_count(logical=False)
        cpu_count = 32
        reserved = 0
        processed_count = [0]
        for sublist in np.array_split(self.data, cpu_count):
            threads.append(threading.Thread(target=self.image_generation_thread, args=(sublist, reserved, processed_count)))
            reserved += len(sublist)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        done[0] = True

        print()


    def image_generation_thread(self, sublist, reserved, processed_count):
        for i, page in enumerate(sublist):
            filename = str(reserved + i).zfill(len(str(len(self.data))))
            html = Generator.generate_html_2(page)
            with open(f"./htmls/{filename}.html", "w") as file: file.write(html)

            error = os.system(f"wkhtmltoimage --enable-local-file-access --quiet ./htmls/{filename}.html ./images/{filename}.jpg")
            if error:
                print(f"Error for file {filename}.html => {filename}.jpg ({error})\n")
            else:
                processed_count[0] += 1
                print(f"\rRendered {processed_count[0]}/{len(self.data)} images.", end=" ")
