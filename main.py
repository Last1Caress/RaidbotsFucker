import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import asyncio
from playwright.async_api import async_playwright

# Словарь для хранения прогресс-баров и их текущих значений
progress_bars = {}

# Функция для запуска проверок и обновления прогресса
async def run_check(dungeon_name, progress_bar, character_string, selected_keyword, selected_key):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=False для отладки
        page = await browser.new_page()

        try:
            #print(selected_key)
            # Переход на страницу Raidbots Droptimizer
            await page.goto("https://www.raidbots.com/simbot/droptimizer", timeout=60000)
            await page.locator("#SimcUserInput-input").click()
            await page.locator("#SimcUserInput-input").fill(character_string)
            await page.get_by_text("Mythic+ Dungeons").click()
            #await page.locator("div").filter(has_text=re.compile(r"^Cinderbrew Meadery$")).nth(1).click()
            await page.get_by_text(selected_keyword).click()
            if(selected_key == 1):
                await page.get_by_text(f"Mythic", exact=True).click()
            else:
                await page.get_by_text(f"Mythic {selected_key}").click()
            await page.pause()
        except Exception as e:
            print(f"Ошибка для {dungeon_name}: {e}")
        finally:
            await browser.close()

# Функция, которая будет выполняться при нажатии на кнопку "Запустить"
def run_code():
    # Очистка предыдущих прогресс-баров
    for widget in progress_frame.winfo_children():
        widget.destroy()

    # Получаем текст из текстового поля
    character = text_area.get("1.0", tk.END).strip()
    print(f"Character: {character}")

    # Получаем выбранные чекбоксы
    selected_items = [item for item, var in checkboxes.items() if var.get()]
    print(f"Selected Items: {selected_items}")

    selected_keywords = [
        data["keyword"] for data in checkbox_data
        if checkboxes[data["text"]].get()
    ]

    selected_key = selected_value.get()

    # Создаем прогресс-бары для каждого выбранного значения
    for item in selected_items:
        create_progress_bar(item)

    # Запускаем асинхронные задачи для каждого выбранного подземелья
    asyncio.run(run_all_checks(selected_items, selected_keywords, selected_key))

# Функция для создания прогресс-бара
def create_progress_bar(name):
    frame = tk.Frame(progress_frame)
    frame.pack(fill="x", pady=5)

    label = tk.Label(frame, text=name, font=("Arial", 12))
    label.pack(side="left")

    progress = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
    progress.pack(side="right", padx=10)

    # Сохраняем прогресс-бар в словаре
    progress_bars[name] = progress

# Функция для запуска всех проверок параллельно
async def run_all_checks(selected_items, selected_keywords, selected_key):
    tasks = []
    for dungeon_name, selected_keyword in zip(selected_items, selected_keywords):
        progress_bar = progress_bars[dungeon_name]
        character = text_area.get("1.0", tk.END).strip()
        task = asyncio.create_task(run_check(dungeon_name, progress_bar, character, selected_keyword, selected_key))
        tasks.append(task)

    # Ждем завершения всех задач
    await asyncio.gather(*tasks)

# Создание главного окна
root = tk.Tk()
root.title("UI Приложение")
#root.geometry("800x600")  # Размер окна
root.state('zoomed')

# Разделение экрана на левую и правую части
left_frame = tk.Frame(root)
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

right_frame = tk.Frame(root)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# 1. Текст заголовка
header_label = tk.Label(left_frame, text="Выберите инст", font=("Arial", 16))
header_label.pack(pady=10)

# 2. Левая часть: Меню с чекбоксами (текст + картинка)
checkbox_frame = tk.Frame(left_frame)
checkbox_frame.pack(pady=10)

# Словарь для хранения состояний чекбоксов
checkboxes = {}

# Пример данных для чекбоксов (текст и путь к картинке)
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

# Загрузка картинок и создание чекбоксов
for data in checkbox_data:
    # Загрузка картинки
    image = Image.open(data["image_path"])
    image = image.resize((140, 80))  # Уменьшаем размер картинки
    photo = ImageTk.PhotoImage(image)

    # Переменная для состояния чекбокса
    var = tk.BooleanVar()
    checkboxes[data["text"]] = var

    # Создание чекбокса с текстом и картинкой
    checkbox = tk.Checkbutton(
        checkbox_frame,
        text=data["text"],
        variable=var,
        image=photo,
        compound="left",
        font=("Arial", 12),
    )
    checkbox.image = photo  # Сохраняем ссылку на картинку
    checkbox.pack(anchor="w")

# 3. Область для текста
text_frame = tk.Frame(left_frame)
text_frame.pack(pady=10)

text_label = tk.Label(text_frame, text="Введите строку из /simc:", font=("Arial", 12))
text_label.pack()

text_area = tk.Text(text_frame, height=5, width=50, font=("Arial", 12))
text_area.pack()

# 4. Правая часть: Радиокнопки для выбора числа от 1 до 10
radio_frame = tk.Frame(right_frame)
radio_frame.pack(pady=10)

radio_label = tk.Label(radio_frame, text="Выберите ключ:", font=("Arial", 12))
radio_label.pack()

selected_value = tk.IntVar()  # Переменная для хранения выбранного значения
for i in range(1, 11):
    radio = tk.Radiobutton(radio_frame, text=str(i), variable=selected_value, value=i, font=("Arial", 12))
    radio.pack(anchor="w")

# 5. Нижняя часть: Прогресс-бары
progress_frame = tk.Frame(root)
progress_frame.pack(side="bottom", fill="x", pady=10)

# 6. Кнопка для запуска кода
run_button = tk.Button(root, text="Запустить", command=run_code, font=("Arial", 14), bg="lightblue")
run_button.pack(side="bottom", pady=20)

# Запуск главного цикла
root.mainloop()