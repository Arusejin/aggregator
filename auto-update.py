import json
import re
import psycopg2

# Загрузка конфигурации из config.json
with open('config.json') as config_file:
    config = json.load(config_file)

# Подробности подключения к базе данных
db_config = config["database"]
conn = psycopg2.connect(
    host=db_config["host"],
    port=db_config["port"],
    database=db_config["database"],
    user=db_config["user"],
    password=db_config["password"]
)
cursor = conn.cursor()

# Шаблон регулярного выражения для извлечения данных из логов
log_pattern = re.compile(r'^(\S+) (\S+) (\S+) \[(.*?)\] "(.*?)" (\d+) (\d+|-)$')


# Функция для обновления базы данных
def update_database():
    # Чтение логов сервера Apache и сохранение их в базе данных
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

                # Вставка записи лога в базу данных
                cursor.execute(
                    """
                    INSERT INTO logs (ip, logname, usr, dt, request, status, bytes_sent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (ip, logname, user, date, request, status, bytes_sent)
                )

    # Фиксация транзакции базы данных
    conn.commit()
