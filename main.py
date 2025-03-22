import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import asyncio
from playwright.async_api import async_playwright
import re
import threading
import os
from datetime import datetime
import time

progress_bars = {}

async def run_check(dungeon_name, character_string, selected_keyword, selected_key):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            await page.goto("https://www.raidbots.com/simbot/droptimizer", timeout=60000)
            await page.locator("#SimcUserInput-input").click()
            await page.locator("#SimcUserInput-input").fill(character_string)
            await page.get_by_text("Mythic+ Dungeons").click()
            await page.get_by_text(selected_keyword).click()

            if selected_key == 1:
                await page.get_by_text("Mythic", exact=True).click()
            else:
                await page.get_by_text(f"Mythic {selected_key}").click()

            time.sleep(1)
            await page.get_by_role("button", name="Run Droptimizer").click()

            previous_status = None
            max_retries = 60
            retry_count = 0

            while retry_count < max_retries:
                try:
                    dungeon_summary_element = page.get_by_role("heading", name="Dungeon Summary")
                    if await dungeon_summary_element.count() > 0:
                        print(f"Элемент 'Dungeon Summary' найден для {dungeon_name}. Задача завершена!")
                        root.after(0, lambda: update_progress_bar(progress_bars[dungeon_name], "Готово", 100))
                        break

                    job_status_element = page.locator("div").filter(has_text=re.compile(r"^Job Status")).first
                    job_status_text = await job_status_element.inner_text()

                    if job_status_text != previous_status:
                        print(f"Текущий статус для {dungeon_name}: {job_status_text}")
                        previous_status = job_status_text

                    if "Processing" in job_status_text:
                        root.after(0, lambda: update_progress_bar(progress_bars[dungeon_name], "Processing", 99))
                        continue

                    match = re.search(r"(\d+)\s*/\s*(\d+)", job_status_text)
                    if match:
                        left_value = int(match.group(1))
                        right_value = int(match.group(2))
                        percentage = (1 - (left_value / right_value)) * 100
                        print(f"Процент выполнения для {dungeon_name}: {percentage:.1f}%")
                        print(f"Место в очереди: {left_value} / {right_value}")
                        root.after(0, lambda: update_progress_bar(progress_bars[dungeon_name], percentage, percentage))

                except Exception as e:
                    print(f"Ошибка при получении статуса для {dungeon_name}: {e}")

                await asyncio.sleep(5)
                retry_count += 1

            if retry_count == max_retries:
                print(f"Превышено максимальное время ожидания для {dungeon_name}.")
                return

            await save_screenshot(page, selected_keyword.replace(':', ''))

        except Exception as e:
            print(f"Ошибка для {dungeon_name}: {e}")
        finally:
            await browser.close()


async def save_screenshot(page, selected_keyword):
    os.makedirs("./Result/", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Уникальный временной штамп
    file_path = f"./Result/{selected_keyword}_{timestamp}.png"
    await page.screenshot(path=file_path, full_page=True)
    print(f"Скриншот сохранен: {file_path}")


def update_progress_bar(progress_bar_data, value, progress_value=None):
    progress_bar = progress_bar_data["progress"]
    label = progress_bar_data["label"]

    if isinstance(value, str):
        label.config(text=f"{label['text'].split(' (')[0]} ({value})")
    else:
        label.config(text=f"{label['text'].split(' (')[0]} ({value:.1f}%)")

    if progress_value is not None:
        progress_bar['value'] = progress_value

    root.update_idletasks()


def run_code():
    for widget in progress_frame.winfo_children():
        widget.destroy()

    character = text_area.get("1.0", tk.END).strip()
    print(f"Character: {character}")

    selected_items = [item for item, var in checkboxes.items() if var.get()]
    print(f"Selected Items: {selected_items}")

    selected_keywords = [
        data["keyword"] for data in checkbox_data
        if checkboxes[data["text"]].get()
    ]

    selected_key = selected_value.get()

    for item in selected_items:
        create_progress_bar(item)

    threading.Thread(target=lambda: asyncio.run(run_all_checks(selected_items, selected_keywords, selected_key))).start()


def create_progress_bar(name):
    frame = tk.Frame(progress_frame)
    frame.pack(fill="x", pady=5)

    label = tk.Label(frame, text=f"{name} (0.0%)", font=("Arial", 12))
    label.pack(side="left")

    progress = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
    progress.pack(side="right", padx=10)
    progress_bars[name] = {"progress": progress, "label": label}


async def run_all_checks(selected_items, selected_keywords, selected_key):
    tasks = []
    for dungeon_name, selected_keyword in zip(selected_items, selected_keywords):
        character = text_area.get("1.0", tk.END).strip()
        task = asyncio.create_task(run_check(dungeon_name, character, selected_keyword, selected_key))
        tasks.append(task)

    await asyncio.gather(*tasks)


root = tk.Tk()
root.title("RaidbotsFucker")
root.state('zoomed')

left_frame = tk.Frame(root)
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

right_frame = tk.Frame(root)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

header_label = tk.Label(left_frame, text="Выберите инст", font=("Arial", 16))
header_label.pack(pady=10)

checkbox_frame = tk.Frame(left_frame)
checkbox_frame.pack(pady=10)

checkboxes = {}

checkbox_data = [
    {"text": "Cinderbrew Meadery (Искроварня)", "image_path": "./Images/Cinderbrew_Meadery.png", "keyword": "Cinderbrew Meadery"},
    {"text": "Operation: Floodgate (Операция Шлюх)", "image_path": "./Images/Operation_Floodgate.png", "keyword": "Operation: Floodgate"},
    {"text": "Operation: Mechagon (Операция Мехагон)", "image_path": "./Images/Operation_Mechagon.png", "keyword": "Operation: Mechagon"},
    {"text": "Darkflame Cleft (Расселина темного пламени)", "image_path": "./Images/Darkflame_Cleft.png", "keyword": "Darkflame Cleft"},
    {"text": "Priory of the Sacred Flame (Приорал)", "image_path": "./Images/Priory_of_the_Sacred_Flame.png", "keyword": "Priory of the Sacred Flame"},
    {"text": "The MOTHERLODE!! (Золотая Жила)", "image_path": "./Images/The_MOTHERLODE!!.png", "keyword": "The MOTHERLODE!!"},
    {"text": "The Rookery (Гнездовье)", "image_path": "./Images/The_Rookery.png", "keyword": "The Rookery"},
    {"text": "Theater of Pain (Театр)", "image_path": "./Images/Theater_of_Pain.png", "keyword": "Theater of Pain"},
]

for data in checkbox_data:
    image = Image.open(data["image_path"])
    image = image.resize((140, 80))
    photo = ImageTk.PhotoImage(image)

    var = tk.BooleanVar()
    checkboxes[data["text"]] = var

    checkbox = tk.Checkbutton(
        checkbox_frame,
        text=data["text"],
        variable=var,
        image=photo,
        compound="left",
        font=("Arial", 12),
    )
    checkbox.image = photo
    checkbox.pack(anchor="w")

text_frame = tk.Frame(left_frame)
text_frame.pack(pady=10)

text_label = tk.Label(text_frame, text="Введите строку из /simc:", font=("Arial", 12))
text_label.pack()

text_area = tk.Text(text_frame, height=5, width=50, font=("Arial", 12))
text_area.pack()

radio_frame = tk.Frame(right_frame)
radio_frame.pack(pady=10)

radio_label = tk.Label(radio_frame, text="Выберите ключ:", font=("Arial", 12))
radio_label.pack()

selected_value = tk.IntVar()
for i in range(1, 11):
    radio = tk.Radiobutton(radio_frame, text=str(i), variable=selected_value, value=i, font=("Arial", 12))
    radio.pack(anchor="w")

progress_frame = tk.Frame(root)
progress_frame.pack(side="bottom", fill="x", pady=10)

run_button = tk.Button(root, text="Запустить", command=run_code, font=("Arial", 14), bg="lightblue")
run_button.pack(side="bottom", pady=20)

root.mainloop()