!pip install pyTelegramBotAPI

import telebot
from telebot import types
import random
import json
import os
import time

TOKEN = '8620843237:AAHULubxLRh3spBcUJILIw-GFqU8X2oAjU0'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "aviastroy_ultimate_survival_saves.json"
players = {}

# ==================== ОГРОМНАЯ БАЗА ДАННЫХ ИГРОВОГО МИРА ====================

LOCATIONS = {
    "sotsgorod": {
        "name": "🌳 Соцгород (Парк Крылья Советов)",
        "desc": "Район сталинской застройки, ДК Ленина и Казанского авиационно-технического колледжа (КАТК). Относительно тихий и спокойный район. По аллеям гуляют мамы с колясками, студенты прогуливают пары, а бабушки на лавках контролируют порядок. Отличное место, чтобы начать свой путь, подзаработать на листовках или безопасно обшарить кусты.",
        "energy_cost": 10,
        "danger_level": "Низкий",
        "loot": ["copper_wire", "glass_bottle", "shaurma_coupon"],
        "mobs": ["Студент-прогульщик КАТК 🎒", "Бродячий пес 🐕", "Подозрительный тип в кепке 👀"]
    },
    "karavaevo": {
        "name": "🏭 Караваево (Промзона)",
        "desc": "Индустриальная зона, окруженная заборами авиастроительного завода КАПО им. Горбунова. Пахнет мазутом, керосином и тяжелым трудом. Вдоль гаражей и заброшенных складов можно найти много ценного цветного металла, но бродячие рабочие и суровые заводские сторожа очень не любят посторонних.",
        "energy_cost": 20,
        "danger_level": "Средний",
        "loot": ["copper_wire", "iron_pipe", "blue_tape", "old_battery"],
        "mobs": ["Сторож Михалыч с берданкой 🧹", "Уставший сварщик третьего разряда 🧑‍焊接", "Свора гаражных псов 🐕🐕"]
    },
    "zhilka": {
        "name": "🧱 Жилплощадка (Жилка)",
        "desc": "Легендарный и самый опасный микрорайон Авиастроя с суровой историей. Здесь не любят глупых вопросов и кастомных форсов. Чужаков видят за версту. Но именно на Жилке можно раздобыть самый редкий и дорогой хабар, а также заработать непререкаемый авторитет среди пацанов, если сможешь выжить на рамсах.",
        "energy_cost": 30,
        "danger_level": "ОЧЕНЬ ВЫСОКИЙ 💀",
        "loot": ["iron_pipe", "blue_tape", "old_battery", "golden_chain"],
        "mobs": ["Гопник с Жилки 🚬", "Местный авторитетный пацан Вахит 🧢", "Охотник за кастомными кроссовками 👟"]
    },
    "sukhaya_reka": {
        "name": "🌊 Сухая Река (Дачный сектор)",
        "desc": "Окраина района, переходящая в бесконечные садовые товарищества и частный сектор. Здесь тихо, пахнет яблоками и баней. Можно спокойно перевести дух, поискать ягоды на чужих грядках или нарваться на злого дачника с лопатой.",
        "energy_cost": 15,
        "danger_level": "Низкий",
        "loot": ["fresh_apple", "copper_wire", "glass_bottle"],
        "mobs": ["Разгневанный дачник с лопатой 🧑‍🌾", "Разъяренный домашний гусь 🪿", "Местный бродяга у костра 🔥"]
    },
    "market": {
        "name": "🏪 Рынок на Дементьева",
        "desc": "Эпицентр торговли Авиастроительного района. Шумные торговые ряды, палатки со спортивками, запах специй и шаурмы. Здесь можно продать весь найденный на заброшках хлам, закупиться топовым шмотом у торговцев, встретить квестодателей или сыграть в азартные игры с местными каталами.",
        "energy_cost": 5,
        "danger_level": "Безопасно",
        "loot": ["glass_bottle"],
        "mobs": ["Рыночный карманник 🕵️", "Наглый продавец арбузов 🍉"]
    }
}

ITEMS = {
    # Ресурсы
    "copper_wire": {"name": "🪵 Медный кабель", "type": "resource", "price": 15, "desc": "Толстый кусок медной проволоки. Отличный цветмет, который с удовольствием примут на любой металлобазе Авиастроя."},
    "iron_pipe": {"name": "🪠 Стальная труба", "type": "resource", "price": 25, "desc": "Тяжелый кусок стальной водопроводной трубы. Нужен для крафта серьезного холодного оружия."},
    "blue_tape": {"name": "🔵 Синяя изолента", "type": "resource", "price": 10, "desc": "Легендарная синяя изолента. Способна починить всё в этом мире. Необходимый компонент для любого крафта."},
    "old_battery": {"name": "🔋 Батарейка 'Крона'", "type": "resource", "price": 30, "desc": "Старая, но еще рабочая батарейка. Выдает неплохой разряд тока. Нужна для создания электрошокера."},
    "glass_bottle": {"name": "🍾 Пивная бутылка", "type": "resource", "price": 5, "desc": "Пустая стеклянная бутылка из-под пива. На рынке Дементьева её можно выгодно сдать Бабе Люде."},
    "golden_chain": {"name": "🪙 Золотая цепочка", "type": "resource", "price": 120, "desc": "Толстая золотая цепочка, потерянная кем-то во время районных разборок. Дорогой сувенир."},

    # Еда
    "fresh_apple": {"name": "🍎 Садовое яблоко", "type": "food", "heal": 15, "price": 5, "desc": "Сочное, слегка кислое яблоко, сорванное в садах Сухой Реки. Немного восстанавливает здоровье."},
    "shaurma_coupon": {"name": "🌯 Шаурма у КАТК", "type": "food", "heal": 55, "price": 25, "desc": "Легендарная сытная шаурма. Мгновенно восстанавливает средний запас здоровья и поднимает настроение."},
    "chak_chak": {"name": "🍯 Чак-Чак праздничный", "type": "food", "heal": 100, "price": 60, "desc": "Национальное татарское лакомство, щедро политое медом. Полностью восстанавливает здоровье."},
    "pivo_lyskovo": {"name": "🍺 Лысковское холодное", "type": "food", "heal": 25, "price": 15, "desc": "Классическое пиво для расслабления после тяжелого рабочего дня. Слегка лечит раны и придает сил."},

    # Оружие
    "armatura": {"name": "🪵 Обрез арматуры", "type": "weapon", "atk": 8, "price": 50, "desc": "Ржавый обрез строительной арматуры. Классическое оружие ближнего боя на улицах Казани."},
    "ballon_shpaga": {"name": "💨 Баллончик 'Шпага'", "type": "weapon", "atk": 14, "price": 100, "desc": "Газовый перцовый баллончик. Позволяет держать дистанцию в драке и заливать глаза агрессивным оппонентам."},
    "forces_krasnye": {"name": "👟 Кровавые Форсы", "type": "weapon", "atk": 25, "price": 280, "desc": "Твои легендарные кастомные кроссовки. Удар с ноги в этих форсах наносит огромный урон."},
    "bita_shyp": {"name": "🏒 Шипованная бита", "type": "weapon", "atk": 35, "price": 400, "desc": "Деревянная бейсбольная бита, утыканная ржавыми гвоздями и обмотанная изолентой. Оружие сокрушительной силы. Крафт."},
    "shoker_samopal": {"name": "⚡ Самодельный шокер", "type": "weapon", "atk": 48, "price": 550, "desc": "Связка батареек, медных проводов и стальных контактов. Бьет током прямо через плотные куртки. Крафт."},

    # Броня
    "zipka_black": {"name": "🧥 Черная Зипка", "type": "armor", "defense": 3, "price": 45, "desc": "Плотная хлопковая зипка с глубоким капюшоном. Позволяет скрывать лицо в темноте и защищает от царапин."},
    "abibas_three": {"name": "👖 Спортивка Abibas", "type": "armor", "defense": 8, "price": 110, "desc": "Классический спортивный костюм с тремя полосками. Дарует уважение дворовых пацанов и защищает в драках."},
    "kozhanka_starsh": {"name": "🧥 Кожанка Старшего", "type": "armor", "defense": 20, "price": 260, "desc": "Тяжелая кожаная куртка, доставшаяся от старших пацанов. Отличная защита от ударов тупыми предметами."}
}

CRAFT_RECIPES = {
    "bita_shyp": {
        "ingredients": {"iron_pipe": 2, "blue_tape": 1},
        "result": "bita_shyp",
        "desc": "🪠 Стальная труба (2 шт.) + 🔵 Синяя изолента (1 шт.)"
    },
    "shoker_samopal": {
        "ingredients": {"old_battery": 2, "copper_wire": 3, "blue_tape": 1},
        "result": "shoker_samopal",
        "desc": "🔋 Батарейка Крона (2 шт.) + 🪵 Медный кабель (3 шт.) + 🔵 Синяя изолента (1 шт.)"
    }
}

JOBS = {
    "leaflets": {
        "name": "📄 Раздавать листовки у КАТК",
        "energy": 15,
        "pay": 25,
        "respect": 5,
        "fail_chance": 0.1,
        "desc": "Раздавать листовки с рекламой местной шаурмы студентам авиационного колледжа у входа.",
        "fail_msg": "Куратор КАТК заметил тебя на крыльце, устроил скандал и отобрал половину листовок. Выплата урезана!"
    },
    "loader": {
        "name": "📦 Грузчик в 'Пятерочке'",
        "energy": 35,
        "pay": 60,
        "respect": 12,
        "fail_chance": 0.25,
        "desc": "Разгрузка фуры с продуктами. Тяжелая физическая работа, от которой будет ныть спина.",
        "fail_msg": "Во время разгрузки ты случайно уронил коробку с Лысковским пивом. Директор магазина вычел стоимость из твоей зарплаты!"
    },
    "delivery": {
        "name": "🚴 Курьер 'Самоката' на велике",
        "energy": 50,
        "pay": 110,
        "respect": 18,
        "fail_chance": 0.35,
        "desc": "Быстрая доставка заказов по ямам, лужам и бездорожью Авиастроительного района с огромной сумкой.",
        "fail_msg": "На Караваево на тебя напала стая бродячих собак. Пришлось бросить велосипед с заказом и спасаться бегством!"
    },
    "copper_run": {
        "name": "🪵 Сбор меди в гаражах Караваево",
        "energy": 30,
        "pay": 50,
        "respect": 10,
        "fail_chance": 0.2,
        "desc": "Поиск остатков медных кабелей и труб в полузаброшенных гаражных кооперативах.",
        "fail_msg": "Тебя заметил бдительный председатель кооператива и натравил своего злого кавказца. Еле унес ноги!"
    }
}

QUESTS = {
    "valera_copper": {
        "giver": "👴 Дядя Валера (Караваево)",
        "desc": "Принести Дяде Валере 3 медных кабеля для ремонта его старого мотоцикла.",
        "target_item": "copper_wire",
        "amount": 3,
        "reward_cash": 120,
        "reward_respect": 40,
        "reward_item": "armatura"
    },
    "lyuda_bottles": {
        "giver": "👵 Баба Люда (Рынок Дементьева)",
        "desc": "Собрать на Соцгороде 4 пустые пивные бутылки и сдать Бабе Люде.",
        "target_item": "glass_bottle",
        "amount": 4,
        "reward_cash": 70,
        "reward_respect": 25,
        "reward_item": "shaurma_coupon"
    }
}

# ==================== СИСТЕМА СОХРАНЕНИЙ И КЛАССЫ (ООП) ====================

def save_game_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=4)

def load_game_data():
    global players
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                players = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки файлов сохранения: {e}")
            players = {}

class PlayerSystem:
    @staticmethod
    def create_new_character(uid, name):
        players[str(uid)] = {
            "name": name,
            "hp": 100,
            "max_hp": 100,
            "energy": 100,
            "max_energy": 100,
            "level": 1,
            "respect": 0,
            "cash": 80,
            "inventory": ["shaurma_coupon", "glass_bottle"],
            "weapon": None,
            "armor": None,
            "state": "IDLE", # IDLE, FIGHT, SHOP, CRAFT, QUESTS, GAMBLE, JOBS
            "current_location": "sotsgorod",
            "active_enemy": None,
            "active_quests": [] # ID принятых квестов
        }
        save_game_data()

    @staticmethod
    def get_attack(uid):
        p = players[str(uid)]
        weapon_atk = ITEMS[p["weapon"]]["atk"] if p["weapon"] else 0
        return 5 + (p["level"] * 3) + weapon_atk

    @staticmethod
    def get_defense(uid):
        p = players[str(uid)]
        armor_def = ITEMS[p["armor"]]["defense"] if p["armor"] else 0
        return 2 + (p["level"] * 2) + armor_def

    @staticmethod
    def check_level_up(uid):
        p = players[str(uid)]
        needed_xp = p["level"] * 100
        if p["respect"] >= needed_xp:
            p["level"] += 1
            p["respect"] -= needed_xp
            p["max_hp"] += 20
            p["hp"] = p["max_hp"]
            p["max_energy"] += 10
            p["energy"] = p["max_energy"]
            save_game_data()
            return True
        return False

# ==================== ГЕНЕРАТОРЫ ИНТЕРФЕЙСА ====================

def main_menu_kb(uid):
    p = players[str(uid)]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🗺️ Карта Авиастроя", callback_data="nav_map"),
        types.InlineKeyboardButton("🎒 Мой статус и Рюкзак", callback_data="nav_hero")
    )
    markup.add(
        types.InlineKeyboardButton("🛠️ Верстак (Крафт)", callback_data="nav_craft"),
        types.InlineKeyboardButton("🔨 Биржа Труда (Работа)", callback_data="nav_jobs")
    )
    markup.add(
        types.InlineKeyboardButton("👵 Квесты района", callback_data="nav_quests"),
        types.InlineKeyboardButton("💤 Поспать в подъезде (+Энергия)", callback_data="nav_sleep")
    )
    if p["current_location"] == "market":
        markup.add(types.InlineKeyboardButton("🎲 Сыграть в Напёрстки с Гришей", callback_data="gamble_menu"))
    return markup

def map_kb():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for lid, loc in LOCATIONS.items():
        markup.add(types.InlineKeyboardButton(f"{loc['name']} (Энергия: -{loc['energy_cost']})", callback_data=f"map_go_{lid}"))
    markup.add(types.InlineKeyboardButton("⬅️ Вернуться назад", callback_data="nav_back"))
    return markup

def location_action_kb(lid):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 Обшарить заброшку / кусты", callback_data=f"loc_loot_{lid}"),
        types.InlineKeyboardButton("🗺️ Поехать в другой район", callback_data="nav_map"),
        types.InlineKeyboardButton("🏠 На базу (Главное меню)", callback_data="nav_back")
    )
    if lid == "market":
        markup.add(types.InlineKeyboardButton("🛍️ Зайти в палатку к Бабаю", callback_data="nav_shop"))
    return markup

def combat_kb():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👊 Прописать двоечку", callback_data="fight_hit_normal"),
        types.InlineKeyboardButton("🦶 Подлый пинок по голени", callback_data="fight_hit_sneak")
    )
    markup.add(
        types.InlineKeyboardButton("🛡️ Уйти в глухой блок", callback_data="fight_hit_block"),
        types.InlineKeyboardButton("🌯 Сьесть шаурму (Лечение)", callback_data="fight_heal")
    )
    markup.add(types.InlineKeyboardButton("🏃 Рвануть во дворы (Побег)", callback_data="fight_flee"))
    return markup

def shop_kb(uid):
    p = players[str(uid)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for iid, item in ITEMS.items():
        if item["type"] in ["weapon", "armor", "food"] and "bita_" not in iid and "shoker_" not in iid:
            markup.add(types.InlineKeyboardButton(f"Купить {item['name']} — {item['price']} ₽", callback_data=f"shop_buy_{iid}"))
    markup.add(types.InlineKeyboardButton("💰 Сдать цветмет и пустые бутылки", callback_data="shop_sell_menu"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад во дворик", callback_data="nav_back"))
    return markup

def sell_kb(uid):
    p = players[str(uid)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    unique_items = set(p["inventory"])
    for iid in unique_items:
        item = ITEMS[iid]
        sell_price = int(item["price"] * 0.6)
        qty = p["inventory"].count(iid)
        markup.add(types.InlineKeyboardButton(f"Продать {item['name']} x{qty} — {sell_price} ₽/шт", callback_data=f"shop_sell_{iid}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад к покупкам", callback_data="nav_shop"))
    return markup

def craft_kb(uid):
    p = players[str(uid)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for rid, recipe in CRAFT_RECIPES.items():
        can_craft = True
        ing_strings = []
        for ing, count in recipe["ingredients"].items():
            player_count = p["inventory"].count(ing)
            ing_strings.append(f"{ITEMS[ing]['name']} ({player_count}/{count})")
            if player_count < count:
                can_craft = False

        emoji = "✅" if can_craft else "❌"
        markup.add(types.InlineKeyboardButton(f"{emoji} {recipe['result_name']} | Нужна: {', '.join(ing_strings)}", callback_data=f"craft_build_{rid}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="nav_back"))
    return markup

def jobs_kb():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for jid, job in JOBS.items():
        markup.add(types.InlineKeyboardButton(f"{job['name']} (Энергия: -{job['energy']})", callback_data=f"job_do_{jid}"))
    markup.add(types.InlineKeyboardButton("⬅️ Вернуться на базу", callback_data="nav_back"))
    return markup

def quests_kb(uid):
    p = players[str(uid)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for qid, quest in QUESTS.items():
        if qid in p["active_quests"]:
            has_qty = p["inventory"].count(quest["target_item"])
            markup.add(types.InlineKeyboardButton(f"✅ Сдать квест: {quest['giver']} ({has_qty}/{quest['amount']})", callback_data=f"quest_finish_{qid}"))
        else:
            markup.add(types.InlineKeyboardButton(f"➕ Взять квест: {quest['giver']}", callback_data=f"quest_take_{qid}"))
    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="nav_back"))
    return markup

def gamble_kb():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🥤 Напёрсток 1 (Ставка 20₽)", callback_data="gamble_cup_1"),
        types.InlineKeyboardButton("🥤 Напёрсток 2 (Ставка 20₽)", callback_data="gamble_cup_2")
    )
    markup.add(
        types.InlineKeyboardButton("🥤 Напёрсток 3 (Ставка 20₽)", callback_data="gamble_cup_3"),
        types.InlineKeyboardButton("🎲 Сыграть в Кости (Ставка 50₽)", callback_data="gamble_dice")
    )
    markup.add(types.InlineKeyboardButton("⬅️ Выйти из-за коробки", callback_data="nav_back"))
    return markup

# ==================== СЕРВЕР ОБРАБОТКИ СООБЩЕНИЙ ====================

@bot.message_handler(commands=['start'])
def handle_start(message):
    uid = str(message.from_user.id)
    load_game_data()

    if uid in players:
        bot.send_message(
            message.chat.id,
            f"👑 *Авиастроительный район помнит твоё имя, {players[uid]['name']}!*\nТы стоишь на Соцгороде у ДК Ленина. Все твои шмотки и форсы на месте. Что планируешь делать?",
            parse_mode="Markdown",
            reply_markup=main_menu_kb(uid)
        )
    else:
        PlayerSystem.create_new_character(uid, message.from_user.first_name)
        bot.send_message(
            message.chat.id,
            "🦅 *ДОБРО ПОЖАЛОВАТЬ НА АВИАСТРОЙ! (КАЗАНЬ RPG)*\n\nТы стоишь у выхода со станции метро 'Авиастроительная'. Из заброшенных гаражей Караваево тянет гарью, а вдали высятся трубы авиазавода. В твоем рюкзаке лежит заветная шаурма у КАТК, в кармане 80 рублей, а на ногах — твои кастомные форсы.\n\nТвоя задача — выжить на суровых улицах Авиастроя, накопить авторитет, проапгрейдить пушки и доказать всем, кто тут держит район. Удачи!",
            parse_mode="Markdown",
            reply_markup=main_menu_kb(uid)
        )

# ==================== ДВИЖОК ОБРАБОТКИ CALLBACK QUERY ====================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = str(call.from_user.id)
    load_game_data()

    if uid not in players:
        bot.answer_callback_query(call.id, "Напиши /start для регистрации!")
        return

    p = players[uid]

    # Защита от переходов во время боя
    if p["state"] == "FIGHT" and not call.data.startswith("fight_"):
        bot.answer_callback_query(call.id, "❌ Сначала закончи махач!", show_alert=True)
        return

    # --- НАВИГАЦИЯ ---
    if call.data == "nav_back":
        p["state"] = "IDLE"
        save_game_data()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Вы вернулись во дворик. Локация: *{LOCATIONS[p['current_location']]['name']}*.\nЧем займемся?",
            parse_mode="Markdown",
            reply_markup=make_main_keyboard(uid)
        )
        bot.answer_callback_query(call.id)

    elif call.data == "nav_hero":
        w_name = ITEMS[p["weapon"]]["name"] if p["weapon"] else "Кулаки 👊"
        a_name = ITEMS[p["armor"]]["name"] if p["armor"] else "Обычная одежда 👕"
        inv_list = [ITEMS[i]["name"] for i in p["inventory"]] if p["inventory"] else ["Пусто"]

        status_text = (
            f"👤 *Имя героя:* {p['name']}\n"
            f"👑 *Авторитет:* {p['respect']} ({p['level']} уровень)\n"
            f"❤️ *Здоровье:* {p['hp']}/{p['max_hp']}\n"
            f"⚡ *Энергия:* {p['energy']}/{p['max_energy']}\n"
            f"💰 *Кэш:* {p['cash']} ₽\n\n"
            f"⚔ *Оружие:* {w_name} (+{ITEMS[p['weapon']]['atk'] if p['weapon'] else 0} АТК)\n"
            f"🛡 *Броня:* {a_name} (+{ITEMS[p['armor']]['defense'] if p['armor'] else 0} ЗАЩ)\n\n"
            f"💼 *В твоем рюкзаке:* {', '.join(inv_list)}"
        )

        markup = types.InlineKeyboardMarkup()
        foods = [i for i in p["inventory"] if ITEMS[i]["type"] == "food"]
        if foods:
            unique_foods = set(foods)
            for fid in unique_foods:
                markup.add(types.InlineKeyboardButton(f"😋 Сьесть {ITEMS[fid]['name']}", callback_data=f"hero_eat_{fid}"))
        markup.add(types.InlineKeyboardButton("⬅️ Вернуться", callback_data="nav_back"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=status_text,
            parse_mode="Markdown",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("hero_eat_"):
        fid = call.data.replace("hero_eat_", "")
        if fid in p["inventory"]:
            p["inventory"].remove(fid)
            p["hp"] = min(p["max_hp"], p["hp"] + ITEMS[fid]["heal"])
            save_game_data()
            bot.answer_callback_query(call.id, f"Здоровье восстановлено на {ITEMS[fid]['heal']} ОЗ!")
            # Симулируем обновление статуса героя
            call.data = "nav_hero"
            handle_callback(call)
        else:
            bot.answer_callback_query(call.id, "Этого предмета больше нет в инвентаре!")

    elif call.data == "nav_map":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🗺️ *ВЫБОР НАПРАВЛЕНИЯ НА КАРТЕ*\n\nКуда поедем на трамвае №6?",
            parse_mode="Markdown",
            reply_markup=map_kb()
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("map_go_"):
        lid = call.data.replace("map_go_", "")
        loc = LOCATIONS[lid]

        if p["energy"] >= loc["energy_cost"]:
            p["energy"] -= loc["energy_cost"]
            p["current_location"] = lid
            p["state"] = "TRAVEL"
            save_game_data()

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"📍 *Вы приехали в локацию:* {loc['name']}\n\n{loc['desc']}\n\n🔋 Потрачено энергии: -{loc['energy_cost']}",
                parse_mode="Markdown",
                reply_markup=location_action_kb(lid)
            )
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает энергии! Иди подреми на лавке.", show_alert=True)

    elif call.data == "nav_sleep":
        if p["energy"] >= p["max_energy"]:
            bot.answer_callback_query(call.id, "Ты полон сил!")
        else:
            p["energy"] = p["max_energy"]
            p["hp"] = min(p["max_hp"], p["hp"] + 25)
            save_game_data()
            bot.answer_callback_query(call.id, "⚡ Ты отлично выспался!")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"Вы уснули на лавочке в тихом дворике Соцгорода. Здоровье и энергия восстановлены!",
                reply_markup=main_menu_kb(uid)
            )

    # --- СИСТЕМА ЛУТА И СЛУЧАЙНЫХ СОБЫТИЙ ---
    elif call.data.startswith("loc_loot_"):
        lid = call.data.replace("loc_loot_", "")
        loc = LOCATIONS[lid]

        roll = random.random()
        if roll < 0.45:
            # Махач
            mob_name = random.choice(loc["mobs"])
            p["state"] = "FIGHT"
            p["active_enemy"] = {
                "name": mob_name,
                "hp": 35 + (p["level"] * 12),
                "max_hp": 35 + (p["level"] * 12),
                "atk": 8 + (p["level"] * 3),
                "def": 2 + p["level"],
                "gold": random.randint(15, 45) + (p["level"] * 4),
                "respect": 25 + (p["level"] * 8)
            }
            save_game_data()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"⚠️ *РАМСЫ НА ДОРОГЕ!*\n\nПока вы обшаривали кусты, вас окружил *{p['active_enemy']['name']}*!\nОн требует пояснить за шмот.\n\n❤️ Здоровье оппонента: {p['active_enemy']['hp']}\n⚔️ Атака врага: {p['active_enemy']['atk']}",
                parse_mode="Markdown",
                reply_markup=combat_kb()
            )
            bot.answer_callback_query(call.id, "🚨 На тебя напали!")
        else:
            # Сбор хабара
            loot_item = random.choice(loc["loot"])
            p["inventory"].append(loot_item)
            cash_found = random.randint(5, 25)
            p["cash"] += cash_found
            save_game_data()

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🔍 *Результаты осмотра:* \n\nВам удалось успешно обыскать локацию.\n\n🎒 Получено в инвентарь: *{ITEMS[loot_item]['name']}*\n💰 Найдено мелочью в траве: *{cash_found} ₽*",
                parse_mode="Markdown",
                reply_markup=location_action_kb(lid)
            )
            bot.answer_callback_query(call.id, "📦 Найдено!")

    # --- СУПЕР БОЕВАЯ СИСТЕМА ---
    elif call.data.startswith("fight_"):
        if p["state"] != "FIGHT":
            bot.answer_callback_query(call.id, "Ты сейчас не в бою!")
            return

        enemy = p["active_enemy"]
        action = call.data.replace("fight_", "")
        log_combat = ""
        block_active = False

        # 1. ХОД ИГРОКА
        if action == "hit_normal":
            dmg = max(1, PlayerSystem.get_attack(uid) - enemy["def"] + random.randint(-3, 3))
            enemy["hp"] -= dmg
            log_combat += f"👊 Вы прописали жесткую двоечку в лицо. Нанесено *{dmg}* урона.\n"
        elif action == "hit_sneak":
            # Подлый удар (высокий крит, но шанс промахнуться)
            if random.random() < 0.7:
                dmg = max(1, int(PlayerSystem.get_attack(uid) * 1.6) - enemy["def"] + random.randint(-2, 4))
                enemy["hp"] -= dmg
                log_combat += f"🦶 Вы незаметно пнули соперника по голени. КРИТИЧЕСКИЙ УДАР: *{dmg}* урона!\n"
            else:
                log_combat += "💨 Вы попытались сделать подлый удар, но споткнулись и промахнулись!\n"
        elif action == "hit_block":
            block_active = True
            log_combat += "🛡️ Вы ушли в глухой оборонительный блок, прикрывая лицо руками.\n"
        elif action == "use_shaurma":
            if "shaurma_coupon" in p["inventory"]:
                p["inventory"].remove("shaurma_coupon")
                p["hp"] = min(p["max_hp"], p["hp"] + ITEMS["shaurma_coupon"]["heal"])
                log_combat += f"🌯 Вы быстро съели шаурму прямо во время драки! Восстановлено +{ITEMS['shaurma_coupon']['heal']} ОЗ!\n"
            else:
                bot.answer_callback_query(call.id, "❌ У тебя нет шаурмы в кармане!", show_alert=True)
                return
        elif action == "flee":
            if random.random() < 0.5:
                p["state"] = "IDLE"
                p["active_enemy"] = None
                save_game_data()
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="🏃 *УСПЕШНЫЙ ПОБЕГ!*\n\nТвои верные кастомные форсы не подвели. Вы ловко запрыгнули на подножку уходящего трамвая и скрылись во дворах Соцгорода.",
                    parse_mode="Markdown",
                    reply_markup=main_menu_kb(uid)
                )
                bot.answer_callback_query(call.id)
                return
            else:
                log_combat += "❌ Вы попытались побежать, но зацепились курткой за забор. Сбежать не удалось!\n"

        # Проверка смерти врага
        if enemy["hp"] <= 0:
            p["cash"] += enemy["gold"]
            p["respect"] += enemy["respect"]
            p["state"] = "IDLE"
            p["active_enemy"] = None

            lvl_up = PlayerSystem.check_level_up(uid)
            lvl_up_text = f"\n\n⚡ *АВТОРИТЕТ НА РАЙОНЕ ПОДНЯЛСЯ!* Поздравляем, ты достиг {p['level']} уровня! ОЗ и энергия восстановлены!" if lvl_up else ""

            save_game_data()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🏆 *ПОБЕДА НАД ОППОНЕНТОМ!*\n\nВраг повержен и бежал, скуля от боли.\n\n💰 Из его карманов выпало: *{enemy['gold']} ₽*\n👑 Авторитет повышен: *+{enemy['respect']}*{lvl_up_text}",
                parse_mode="Markdown",
                reply_markup=location_action_kb(p["current_location"])
            )
            bot.answer_callback_query(call.id, "Победа!")
            return

        # 2. ХОД ВРАГА (Если он выжил)
        enemy_dmg = max(1, enemy["atk"] - PlayerSystem.get_defense(uid) + random.randint(-2, 2))
        if block_active:
            enemy_dmg = max(1, int(enemy_dmg * 0.3)) # Урон снижен на 70% в блоке

        p["hp"] -= enemy_dmg
        if p["hp"] < 0: p["hp"] = 0

        log_combat += f"💥 *{enemy['name']}* взбесился и нанес вам ответный удар на *{enemy_dmg}* ОЗ."

        # Проверка твоей смерти
        if p["hp"] <= 0:
            lost_cash = int(p["cash"] * 0.3)
            p["cash"] -= lost_cash
            p["hp"] = int(p["max_hp"] * 0.4) # Респаун с 40% ХП
            p["state"] = "IDLE"
            p["active_enemy"] = None
            p["current_location"] = "sotsgorod"
            save_game_data()

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"💀 *ВАС ИЗБИЛИ И ОБОБРАЛИ!*\n\nВы потеряли сознание. Очнулись только утром на кушетке в приёмном покое Городской Больницы №12 на Соцгороде. Голова раскалывается.\n\n💸 Местные хулиганы вытащили у вас из кармана: *{lost_cash} ₽*",
                parse_mode="Markdown",
                reply_markup=main_menu_kb(uid)
            )
            bot.answer_callback_query(call.id, "Ты потерял сознание!")
            return

        # Если оба живы, обновляем экран боя
        save_game_data()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"👿 *ИДЕТ НАПРЯЖЕННЫЙ МАХАЧ!*\n\n*Враг:* {enemy['name']} (ОЗ: {enemy['hp']}/{enemy['max_hp']})\n*Твое здоровье:* {p['hp']}/{p['max_hp']}\n\n-----------------------------\n{log_combat}",
            parse_mode="Markdown",
            reply_markup=combat_kb()
        )
        bot.answer_callback_query(call.id)

    # --- ТОРГОВАЯ СИСТЕМА (РЫНОК ДЕМЕНТЬЕВА) ---
    elif call.data == "nav_shop":
        p["state"] = "SHOP"
        save_game_data()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🏪 *РЫНОК НА ДЕМЕНТЬЕВА*\nЗдесь стоят палатки местных торговцев. Пахнет специями, дешевой одеждой и пивом.\n\n💰 Твой кэш: *{p['cash']} ₽*",
            parse_mode="Markdown",
            reply_markup=shop_kb(uid)
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("shop_buy_"):
        item_id = call.data.replace("shop_buy_", "")
        item = ITEMS[item_id]

        if p["cash"] >= item["price"]:
            p["cash"] -= item["price"]

            if item["type"] == "weapon":
                p["weapon"] = item_id
                bot.send_message(call.message.chat.id, f"⚔️ Ты купил и экипировал новое оружие: *{item['name']}*", parse_mode="Markdown")
            elif item["type"] == "armor":
                p["armor"] = item_id
                bot.send_message(call.message.chat.id, f"🛡️ Ты купил и натянул на себя новую броню: *{item['name']}*", parse_mode="Markdown")
            else:
                p["inventory"].append(item_id)
                bot.send_message(call.message.chat.id, f"🌯 Вы положили в карман: *{item['name']}*", parse_mode="Markdown")

            save_game_data()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🏪 *РЫНОК НА ДЕМЕНТЬЕВА*\nПокупка успешна! Шмот у тебя.\n\n💰 Твой баланс: *{p['cash']} ₽*",
                parse_mode="Markdown",
                reply_markup=shop_kb(uid)
            )
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает кэша на кармане!", show_alert=True)

    elif call.data == "shop_sell_menu":
        if not p["inventory"]:
            bot.answer_callback_query(call.id, "🎒 Твой рюкзак абсолютно пуст!", show_alert=True)
            return
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"💰 *СДАЧА ХЛАМА И ЦВЕТМЕТА*\nСкупщик на рынке готов забрать твой хабар за 60% от реальной стоимости.",
            reply_markup=sell_kb(uid)
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("shop_sell_"):
        item_id = call.data.replace("shop_sell_", "")
        if item_id in p["inventory"]:
            p["inventory"].remove(item_id)
            pay = int(ITEMS[item_id]["price"] * 0.6)
            p["cash"] += pay
            save_game_data()
            bot.answer_callback_query(call.id, f"Продано! Получено {pay} ₽")

            if p["inventory"]:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="💰 *СДАЧА ХЛАМА И ЦВЕТМЕТА*\nСкупщик взвешивает твой товар на старых весах...",
                    reply_markup=sell_kb(uid)
                )
            else:
                call.data = "nav_shop"
                handle_callback(call)
        else:
            bot.answer_callback_query(call.id, "Этого предмета больше нет в инвентаре!")

    # --- СИСТЕМА КРАФТА (ВЕРСТАК) ---
    elif call.data == "nav_craft":
        p["state"] = "CRAFT"
        save_game_data()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🛠️ *ВЕРСТАК В ГАРАЖАХ*\nЗдесь из найденных ресурсов можно собрать убойное оружие, которое не купишь в обычном магазине.",
            parse_mode="Markdown",
            reply_markup=craft_kb(uid)
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("craft_build_"):
        rid = call.data.replace("craft_build_", "")
        recipe = CRAFT_RECIPES[rid]

        can_build = True
        for ing, count in recipe["ingredients"].items():
            if p["inventory"].count(ing) < count:
                can_build = False
                break

        if can_build:
            for ing, count in recipe["ingredients"].items():
                for _ in range(count):
                    p["inventory"].remove(ing)

            p["weapon"] = rid
            save_game_data()

            bot.send_message(
                call.message.chat.id,
                f"🎉 *УСПЕШНЫЙ КРАФТ!*\nВы собрали на верстаке: *{recipe['desc']}* и сразу экипировали его в руки!",
                parse_mode="Markdown"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🛠️ *ВЕРСТАК В ГАРАЖАХ*\nВы сдули стружку с верстака. Что соберем еще?",
                parse_mode="Markdown",
                reply_markup=craft_kb(uid)
            )
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает ресурсов для крафта!", show_alert=True)

    # --- СИСТЕМА ТРУДОУСТРОЙСТВА (РАБОТА) ---
    elif call.data == "nav_jobs":
        p["state"] = "JOBS"
        save_game_data()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🔨 *БИРЖА ТРУДА АВИАСТРОЯ*\n\nРабота — единственный честный способ заработать кэш, если гопники отожали всё. Требует много энергии.\n\n⚡ Твоя энергия: *{p['energy']}/{p['max_energy']}*",
            parse_mode="Markdown",
            reply_markup=jobs_kb()
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("job_do_"):
        jid = call.data.replace("job_do_", "")
        job = JOBS[jid]

        if p["energy"] >= job["energy"]:
            p["energy"] -= job["energy"]

            if random.random() < job["fail_chance"]:
                fine = int(job["pay"] * 0.4)
                final_pay = job["pay"] - fine
                p["cash"] += final_pay
                p["respect"] += int(job["respect"] / 2)
                save_game_data()

                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"⚠️ *ФОРС-МАЖОР НА РАБОТЕ!*\n\n{job['fail_msg']}\n\n💵 Получено урезанной зарплаты: *{final_pay} ₽*\n👑 Получено авторитета: *+{int(job['respect'] / 2)}*",
                    parse_mode="Markdown",
                    reply_markup=jobs_kb()
                )
            else:
                p["cash"] += job["pay"]
                p["respect"] += job["respect"]
                PlayerSystem.check_level_up(uid)
                save_game_data()

                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"✅ *РАБОТА ВЫПОЛНЕНА УСПЕШНО!*\n\nВы честно отпахали свою смену.\n\n💵 Заработано кэша: *{job['pay']} ₽*\n👑 Получено авторитета: *+{job['respect']}*",
                    parse_mode="Markdown",
                    reply_markup=jobs_kb()
                )
            bot.answer_callback_query(call.id, "Работа окончена!")
        else:
            bot.answer_callback_query(call.id, "❌ Слишком устал для этой работы! Нужно поспать.", show_alert=True)

    # --- ИНТЕРАКТИВНЫЕ КВЕСТЫ ---
    elif call.data == "nav_quests":
        p["state"] = "QUESTS"
        save_game_data()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="👵 *ПОРУЧЕНИЯ И КВЕСТЫ ОТ МЕСТНЫХ ЖИТЕЛЕЙ*\nПомогай местным решать их проблемы и получай топовые награды.",
            parse_mode="Markdown",
            reply_markup=quests_kb(uid)
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("quest_take_"):
        qid = call.data.replace("quest_take_", "")
        quest = QUESTS[qid]

        p["active_quests"].append(qid)
        save_game_data()

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📋 *ВЫ ПРИНЯЛИ ЗАДАНИЕ:*\n\nЗаказчик: {quest['giver']}\n\nСуть дела: {quest['desc']}\n\n🎁 Награда: *{quest['reward_cash']} ₽*, *{quest['reward_respect']}* авторитета и полезный предмет!",
            parse_mode="Markdown",
            reply_markup=quests_kb(uid)
        )
        bot.answer_callback_query(call.id, "Задание принято!")

    elif call.data.startswith("quest_finish_"):
        qid = call.data.replace("quest_finish_", "")
        quest = QUESTS[qid]

        has_items = p["inventory"].count(quest["target_item"])
        if has_items >= quest["amount"]:
            # Списываем квестовые предметы
            for _ in range(quest["amount"]):
                p["inventory"].remove(quest["target_item"])

            p["cash"] += quest["reward_cash"]
            p["respect"] += quest["reward_respect"]
            p["inventory"].append(quest["reward_item"])
            p["active_quests"].remove(qid)
            PlayerSystem.check_level_up(uid)
            save_game_data()

            bot.send_message(
                call.message.chat.id,
                f"🎉 *КВЕСТ ВЫПОЛНЕН!*\n\n{quest['giver']} благодарит вас!\n\n🎁 Получено: *{quest['reward_cash']} ₽* и *{quest['reward_respect']}* авторитета.\n📦 Выдан предмет: *{ITEMS[quest['reward_item']]['name']}*",
                parse_mode="Markdown"
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="👵 *ПОРУЧЕНИЯ И КВЕСТЫ ОТ МЕСТНЫХ ЖИТЕЛЕЙ*\nЗадание сдано!",
                parse_mode="Markdown",
                reply_markup=quests_kb(uid)
            )
        else:
            bot.answer_callback_query(call.id, "❌ Не хватает предметов для сдачи квеста!", show_alert=True)

    # --- АЗАРТНЫЕ ИГРЫ (ГЕЙМБЛИНГ С ГРИШЕЙ НАПЁРСТОЧНИКОМ) ---
    elif call.data == "gamble_menu":
        p["state"] = "GAMBLE"
        save_game_data()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🎲 *ГРИША НАПЁРСТОЧНИК*\n\nГриша крутит три пластиковых стаканчика на старой картонной коробке. Под одним из них лежит шарик.\n\n*Правила:* Угадай напёрсток и удвой свою ставку (20 ₽). Или рискни в Кости (ставка 50 ₽).\n\n💰 Твой кэш: *{p['cash']} ₽*",
            parse_mode="Markdown",
            reply_markup=gamble_kb()
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("gamble_cup_"):
        cup_chosen = int(call.data.replace("gamble_cup_", ""))

        if p["cash"] >= 20:
            p["cash"] -= 20
            winning_cup = random.randint(1, 3)

            if cup_chosen == winning_cup:
                p["cash"] += 40
                result_text = f"🎉 *ВЫ ВЫИГРАЛИ!*\n\nГриша поднимает стаканчик №{cup_chosen}... И там лежит шарик! Без обмана!\n\n💰 Забрано со стола: *+40 ₽*"
            else:
                result_text = f"❌ *ПРОИГРЫШ!*\n\nВы выбрали стаканчик №{cup_chosen}. Гриша ухмыляется и поднимает стаканчик №{winning_cup} — шарик был там. Твои 20 рублей улетают к Грише."

            save_game_data()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🎲 *ГРИША НАПЁРСТОЧНИК*\n\n{result_text}\n\n💰 Твой кэш: *{p['cash']} ₽*",
                parse_mode="Markdown",
                reply_markup=gamble_kb()
            )
        else:
            bot.answer_callback_query(call.id, "❌ Нет денег на ставку!", show_alert=True)

    elif call.data == "gamble_dice":
        if p["cash"] >= 50:
            p["cash"] -= 50

            your_roll = random.randint(1, 6)
            grisha_roll = random.randint(1, 6)

            if your_roll > grisha_roll:
                p["cash"] += 100
                res = f"🏆 *ПОБЕДА!*\nТвой кубик: *{your_roll}* | Кубик Гриши: *{grisha_roll}*\nВы выиграли и удвоили ставку! +100 ₽!"
            elif your_roll < grisha_roll:
                res = f"💀 *ПОРАЖЕНИЕ!*\nТвой кубик: *{your_roll}* | Кубик Гриши: *{grisha_roll}*\nГриша выкинул больше! Твои 50 ₽ сгорают."
            else:
                p["cash"] += 50
                res = f"🤝 *НИЧЬЯ!*\nТвой кубик: *{your_roll}* | Кубик Гриши: *{grisha_roll}*\nСтавки возвращены!"

            save_game_data()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"🎲 *ГРИША НАПЁРСТОЧНИК — КОСТИ*\n\n{res}\n\n💰 Твой кэш: *{p['cash']} ₽*",
                parse_mode="Markdown",
                reply_markup=gamble_kb()
            )
        else:
            bot.answer_callback_query(call.id, "❌ Нет денег на ставку!", show_alert=True)

# ==================== ОГРОМНЫЙ БЛОК ВСПОМОГАТЕЛЬНЫХ ФУНКЦИЙ ====================

def get_lore_about_sotsgorod():
    return """
    Соцгород — это уникальный памятник советского градостроительства 1930-1950-х годов.
    Район застраивался специально для работников Казанского авиационного завода №124 (впоследствии КАПО им. Горбунова)
    и моторостроительного завода №16. В парке 'Крылья Советов' установлены бюсты великих советских ученых и летчиков,
    а ДК им. Ленина долгое время являлся центром культурной жизни района. Сегодня район совмещает исторический уют и дерзкий молодежный вайб.
    """

def get_lore_about_zhilka():
    return """
    Жилплощадка — жилой массив на северо-западе Авиастроительного района Казани, возникший в 1950-х годах в связи с расширением промзоны.
    Район получил всемирную известность в 1970-1990-х годах как место зарождения легендарного казанского феномена и одноименной ОПГ 'Жилплощадка'.
    Это место ковалось в условиях суровой заводской закалки и жестких уличных правил, которые оставили неизгладимый след в истории города.
    """

def make_main_keyboard(uid):
    p = players[str(uid)]
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🗺️ Карта Авиастроя", callback_data="nav_map"),
        types.InlineKeyboardButton("🎒 Мой Герой & Рюкзак", callback_data="nav_hero")
    )
    markup.add(
        types.InlineKeyboardButton("🛠️ Верстак (Крафт)", callback_data="nav_craft"),
        types.InlineKeyboardButton("🔨 Биржа Труда (Работа)", callback_data="nav_jobs")
    )
    markup.add(
        types.InlineKeyboardButton("👵 Квесты района", callback_data="nav_quests"),
        types.InlineKeyboardButton("💤 Поспать в подъезде", callback_data="nav_sleep")
    )
    if p["current_location"] == "market":
        markup.add(types.InlineKeyboardButton("🎲 Сыграть в напёрстки с Гришей", callback_data="gamble_menu"))
    return markup

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    load_game_data()
    print("==================================================")
    print("=== БОТ АВИАСТРОЙ ULTIMATE RPG УСПЕШНО ЗАПУЩЕН ===")
    print("==================================================")
    bot.infinity_polling()
