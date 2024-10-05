import sqlite3


class Database:
    def __init__(self, db_path="calendar.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Создание таблицы для хранения событий, если она не существует"""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                is_day BOOLEAN NOT NULL,
                UNIQUE(user_id, date)
            )
        """
        )
        self.conn.commit()

    def add_event(self, user_id, date, is_day):
        """Добавление или обновление события в базе данных"""
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO events (user_id, date, is_day)
                VALUES (?, ?, ?)
            """,
                (user_id, date, is_day),
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка добавления события: {e}")

    def get_event(self, user_id, date):
        """Получение события на конкретную дату"""
        try:
            self.cursor.execute(
                """
                SELECT is_day FROM events
                WHERE user_id = ? AND date = ?
            """,
                (user_id, date),
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Ошибка получения события: {e}")
            return None

    def delete_event(self, user_id, date):
        print(user_id)
        """Удаление события на конкретную дату"""
        try:
            self.cursor.execute(
                """
                SELECT id FROM events
                WHERE user_id = ? AND date = ?
                LIMIT 1
            """,
                (user_id, date),
            )
            event_id = self.cursor.fetchone()
            if event_id:
                self.cursor.execute(
                    """
                    DELETE FROM events
                    WHERE id = ?
                """,
                    (event_id[0],),
                )
                self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка удаления события: {e}")

    def get_events(self, user_id, year, month):
        """Получение всех событий за конкретный месяц"""
        try:
            month_str = f"{year}-{month:02d}"
            self.cursor.execute(
                """
                SELECT date, is_day FROM events
                WHERE user_id = ? AND strftime('%Y-%m', date) = ?
            """,
                (user_id, month_str),
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка получения событий: {e}")
            return []

    def get_all_users(self):
        """Получение всех уникальных user_id из таблицы events"""
        try:
            self.cursor.execute("SELECT DISTINCT user_id FROM events")
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Ошибка получения всех пользователей: {e}")
            return []

    def close(self):
        """Закрытие соединения с базой данных"""
        self.conn.close()
