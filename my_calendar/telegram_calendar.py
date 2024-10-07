import calendar
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes


class Calendar:
    def __init__(self, db):
        self.db = db

    def create_calendar(self, user_id, year, month):
        now = datetime.now()
        today = now.day

        markup = [
            [
                InlineKeyboardButton(
                    f"{calendar.month_name[month]} {year}", callback_data="ignore"
                )
            ]
        ]

        week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        markup.append(
            [InlineKeyboardButton(day, callback_data="ignore") for day in week_days]
        )

        # Получаем первый день недели для текущего месяца (0 - понедельник, 6 - воскресенье)
        first_day_of_month = calendar.weekday(year, month, 1)

        # Получаем количество дней в предыдущем месяце
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        days_in_prev_month = calendar.monthrange(prev_year, prev_month)[1]

        # Заполняем дни предыдущего месяца
        row = []
        for i in range(first_day_of_month):
            prev_day = days_in_prev_month - first_day_of_month + i + 1
            row.append(InlineKeyboardButton(str(prev_day), callback_data="ignore"))

        # Заполняем дни текущего месяца
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            date = f"{year}-{month:02d}-{day:02d}"
            event = self.db.get_event(user_id, date)

            display_day = str(day)
            symbol = ""

            if day == today and now.month == month and now.year == year:
                symbol += "♬"

            if event is not None:
                symbol += "☼" if event else "☽"  # Круг для дня, полумесяц для ночи

            display_text = f"{display_day}{symbol}"
            row.append(
                InlineKeyboardButton(
                    display_text, callback_data=f"day_{year}_{month}_{day}"
                )
            )

            if len(row) == 7:
                markup.append(row)
                row = []

        if row:
            next_month_day = 1
            while len(row) < 7:
                row.append(
                    InlineKeyboardButton(str(next_month_day), callback_data="ignore")
                )
                next_month_day += 1
            markup.append(row)

        # Проверяем последние 4 события
        last_four_events = self.db.get_last_four_events(user_id, year, month)

        if last_four_events == [0, 0, 1, 1]:
            markup.append(
                [
                    InlineKeyboardButton(
                        "Заполнить до конца месяца?",
                        callback_data=f"fill_month_{year}_{month}",
                    )
                ]
            )

            # Кнопка удаления
        all_events = self.db.get_events(user_id, year, month)
        print(all_events)
        if all_events:
            markup.append(
                [
                    InlineKeyboardButton(
                        "Очистить смены за месяц",
                        callback_data=f"clear_events_{year}_{month}",
                    )
                ]
            )

        markup.append(
            [
                InlineKeyboardButton("<<", callback_data=f"prev_{year}_{month}"),
                InlineKeyboardButton(">>", callback_data=f"next_{year}_{month}"),
            ]
        )

        return InlineKeyboardMarkup(markup)

    def create_day_night_keyboard(self, user_id, year, month, day):
        date = f"{year}-{month:02d}-{day:02d}"
        event = self.db.get_event(user_id, date)

        keyboard = [
            [
                InlineKeyboardButton(
                    "☀️ День", callback_data=f"add_day_{year}_{month}_{day}"
                ),
                InlineKeyboardButton(
                    "🌙 Ночь", callback_data=f"add_night_{year}_{month}_{day}"
                ),
            ]
        ]

        # Добавляем кнопку "Удалить событие", если оно существует
        if event is not None:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "❌ Удалить смену",
                        callback_data=f"delete_event_{year}_{month}_{day}",
                    )
                ]
            )

        keyboard.append(
            [InlineKeyboardButton("Отмена", callback_data=f"cancel_{year}_{month}")]
        )
        return InlineKeyboardMarkup(keyboard)

    async def edit_message(self, query, text, reply_markup):
        try:
            await query.edit_message_text(text, reply_markup=reply_markup)
        except Exception as e:
            print(f"Error editing message: {e}")
            await query.edit_message_reply_markup(reply_markup=reply_markup)

    async def calendar_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        now = datetime.now()
        user_id = update.effective_user.id
        await update.message.reply_text(
            "Когда на завод?",
            reply_markup=self.create_calendar(user_id, now.year, now.month),
        )

    async def calendar_callback(self, update: Update, context):
        query = update.callback_query
        user_id = query.from_user.id

        if query.data.startswith("day"):
            _, year, month, day = query.data.split("_")
            year, month, day = int(year), int(month), int(day)
            await self.edit_message(
                query,
                f"{day}.{month}.{year} смена в ",
                self.create_day_night_keyboard(user_id, year, month, day),
            )
            return

        if query.data.startswith("add_day") or query.data.startswith("add_night"):
            _, is_day, year, month, day = query.data.split("_")
            year, month, day = int(year), int(month), int(day)
            date = f"{year}-{month:02d}-{day:02d}"
            self.db.add_event(user_id, date, is_day == "day")
            event_type = "Дневной" if is_day == "day" else "Ночной"
            await query.answer(f"{event_type} завод будет {day}.{month}.{year}")
            await self.edit_message(
                query, "Когда на завод?", self.create_calendar(user_id, year, month)
            )
            return

        if query.data.startswith("clear_events"):
            parts = query.data.split("_")
            if len(parts) == 4:
                _, _, year, month = parts
                year, month = int(year), int(month)
                self.db.delete_events_for_month(user_id, year, month)
                await query.answer(f"Удалено")
                await self.edit_message(
                    query, "Когда на завод?", self.create_calendar(user_id, year, month)
                )
                return
            else:
                await query.answer("Ошибка: неверный формат данных.")
                return

        if query.data.startswith("fill_month"):
            parts = query.data.split("_")
            if len(parts) == 4:
                _, _, year, month = parts
                year, month = int(year), int(month)

                # Заполняем оставшиеся дни месяца по шаблону: 4 пропуска, 2 дня, 2 ночи
                num_days = calendar.monthrange(year, month)[1]
                last_event = self.db.get_last_event(user_id, year, month)
                last_event_date = datetime.strptime(last_event[1], "%Y-%m-%d")
                day_counter = last_event_date.day + 5
                skip_counter = 4  # Изначально пропускаем 4 дня

                while day_counter <= num_days:
                    if skip_counter < 4:
                        skip_counter += 1
                    elif skip_counter < 6:
                        date = f"{year}-{month:02d}-{day_counter:02d}"
                        self.db.add_event(user_id, date, True)  # True - дневное событие
                        skip_counter += 1
                    elif skip_counter < 8:
                        date = f"{year}-{month:02d}-{day_counter:02d}"
                        self.db.add_event(user_id, date, False)
                        skip_counter += 1
                        if skip_counter == 8:
                            skip_counter = 0
                    else:
                        skip_counter = 0

                    day_counter += 1

                await query.answer("Месяц заполнен по шаблону.")
                await self.edit_message(
                    query, "Когда на завод?", self.create_calendar(user_id, year, month)
                )
                return
            else:
                await query.answer("Ошибка: неверный формат данных.")
                return

        if query.data.startswith("delete_event"):
            _, _, year, month, day = query.data.split("_")
            year, month, day = int(year), int(month), int(day)
            date = f"{year}-{month:02d}-{day:02d}"
            if self.db.delete_event(user_id, date):
                await query.answer(f"Завод на {day}.{month}.{year} удален.")
            else:
                await query.answer(f"Завода на {day}.{month}.{year} не найдено.")
            await self.edit_message(
                query, "Когда на завод?", self.create_calendar(user_id, year, month)
            )
            return

        if query.data.startswith("prev") or query.data.startswith("next"):
            _, year, month = query.data.split("_")
            year, month = int(year), int(month)
            if query.data.startswith("prev"):
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
            else:  # next
                month += 1
                if month > 12:
                    month = 1
                    year += 1
        elif query.data.startswith("cancel"):
            _, year, month = query.data.split("_")
            year, month = int(year), int(month)
        else:
            await query.answer()
            return

        await self.edit_message(
            query, "Когда на завод?", self.create_calendar(user_id, year, month)
        )

    @classmethod
    def setup(cls, application, db):
        calendar_instance = cls(db)

        application.add_handler(
            MessageHandler(
                filters.Text(["Календарь"]), calendar_instance.calendar_command
            )
        )
        application.add_handler(
            CallbackQueryHandler(calendar_instance.calendar_callback)
        )
