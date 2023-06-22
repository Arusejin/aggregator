import tkinter as tk
import subprocess
import json
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Загрузка конфигурации из файла config.json
with open('config.json') as config_file:
    config = json.load(config_file)

# Детали подключения к базе данных
db_config = config["database"]
conn = psycopg2.connect(
    host=db_config["host"],
    port=db_config["port"],
    database=db_config["database"],
    user=db_config["user"],
    password=db_config["password"]
)
cursor = conn.cursor()

# Регулярное выражение для извлечения данных из лог-файла
log_pattern = re.compile(r'^(\S+) (\S+) (\S+) \[(.*?)\] "(.*?)" (\d+) (\d+|-)$')


# Функция для обновления базы данных
def update_database():
    # Чтение лог-файла сервера Apache и сохранение его в базе данных
    cursor.execute(
        """
        DELETE FROM logs;
        """
    )
    with open(config["log_file_path"], 'r') as log_file:
        for line in log_file:
            match = log_pattern.match(line)
            if match:
                ip = match.group(1)
                logname = match.group(2)
                user = match.group(3)
                date = match.group(4)
                request = match.group(5)
                status = int(match.group(6))
                bytes_sent = match.group(7)

                # Вставка записи в базу данных
                cursor.execute(
                    """
                    INSERT INTO logs (ip, logname, usr, dt, request, status, bytes_sent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (ip, logname, user, date, request, status, bytes_sent)
                )

    # Фиксация транзакции базы данных
    conn.commit()

# Функция для извлечения логов и их отображения в терминале
def retrieve_logs(option):
    # Класс для кодирования объектов datetime в JSON
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    # Функция для извлечения логов на основе фильтров
    def get_logs(start_date=None, end_date=None, group_by_ip=False):
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Построение SQL-запроса на основе предоставленных фильтров
        sql_query = """
            SELECT ip, logname, usr, dt, request, status, bytes_sent
            FROM logs
        """

        params = []
        conditions = []

        if start_date:
            conditions.append("dt >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("dt <= %s")
            params.append(end_date)

        if conditions:
            sql_query += "WHERE " + " AND ".join(conditions)

        if group_by_ip:
            sql_query += " GROUP BY ip"

        # Выполнение SQL-запроса
        cursor.execute(sql_query, params)

        # Извлечение результатов
        results = cursor.fetchall()

        # Закрытие курсора
        cursor.close()

        # Возврат логов в виде списка словарей
        return results

    # Извлечение логов на основе фильтров и параметров группировки
    start_date = start_date_entry.get()
    end_date = end_date_entry.get()
    group_by_ip = group_by_ip_var.get()

    logs = get_logs(start_date=start_date, end_date=end_date, group_by_ip=group_by_ip)
    
    if option:
        # Отображение логов в терминале
        terminal_output.delete(1.0, tk.END)
        for i, log in enumerate(logs):
            terminal_output.insert(tk.END, f"Лог #{i+1}\n")
            terminal_output.insert(tk.END, f"ip: {log['ip']}\n")
            terminal_output.insert(tk.END, f"logname: {log['logname']}\n")
            terminal_output.insert(tk.END, f"usr: {log['usr']}\n")
            terminal_output.insert(tk.END, f"dt: {log['dt'].strftime('%Y-%m-%d %H:%M:%S')}\n")
            terminal_output.insert(tk.END, f"request: {log['request']}\n")
            terminal_output.insert(tk.END, f"status: {log['status']}\n")
            terminal_output.insert(tk.END, f"bytes_sent: {log['bytes_sent']}\n\n")


    else:

        # Преобразование логов в формат JSON
        logs_json = json.dumps(logs, cls=DateTimeEncoder)

        # Запись логов в файл logs.json
        with open('logs.json', 'w') as logs_file:
            logs_file.write(logs_json)

# Создание окна Tkinter
window = tk.Tk()

window.title("Агрегатор")

window.iconbitmap(".\ithub.ico")

# Функция для обработки событий нажатия кнопок
def handle_button_click(button_id):
    if button_id == 1:
        update_database()
    elif button_id == 2:
        retrieve_logs(True)
    elif button_id == 3:
        retrieve_logs(False)
        

# Функция для отображения вывода в терминале
def display_terminal_output():
    with open('logs.json', 'r') as logs_file:
        terminal_output.insert(tk.END, logs_file.read())

# Создание кнопок
button1 = tk.Button(window, text="Обновить базу данных", command=lambda: handle_button_click(1))
button2 = tk.Button(window, text="Показать логи", command=lambda: handle_button_click(2))
button3 = tk.Button(window, text="Загрузить в файл JSON", command=lambda: handle_button_click(3))

# Создание области вывода в терминале
terminal_output = tk.Text(window, height=25, width=50)

# Создание текстовых полей для фильтрации по дате
start_date_label = tk.Label(window, text="Дата начала:")
start_date_entry = tk.Entry(window)
end_date_label = tk.Label(window, text="Дата окончания:")
end_date_entry = tk.Entry(window)

# Создание переключателей для опций группировки
group_by_ip_var = tk.IntVar()
group_by_ip_label = tk.Label(window, text="Группировать по IP:")
group_by_ip_yes = tk.Radiobutton(window, text="Да", variable=group_by_ip_var, value=1)
group_by_ip_no = tk.Radiobutton(window, text="Нет", variable=group_by_ip_var, value=0)

# Добавление кнопок, области вывода в терминале, текстовых полей и переключателей в окно
button1.pack()
start_date_label.pack()
start_date_entry.pack()
end_date_label.pack()
end_date_entry.pack()
group_by_ip_label.pack()
group_by_ip_yes.pack()
group_by_ip_no.pack()
button2.pack()
button3.pack()
terminal_output.pack()

# Отображение вывода в терминале при запуске
display_terminal_output()

# Запуск цикла событий Tkinter
window.mainloop()