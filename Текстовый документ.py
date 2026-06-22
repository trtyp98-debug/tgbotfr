import os
import json
import random
import psycopg2
import time
from flask import Flask, request
import telebot
from telebot import types

TOKEN = '8620843237:AAHULubxLRh3spBcUJILIw-GFU8X2oAjU0'
WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST', '11111') 
WEBHOOK_PORT = int(os.environ.get('PORT', 5000))
ADMIN_ID = '11111' 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:11111')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id VARCHAR(50) PRIMARY KEY,
            data JSONB
        );
        CREATE TABLE IF NOT EXISTS inventory (
            user_id VARCHAR(50) REFERENCES players(user_id),
            item_id VARCHAR(50),
            quantity INTEGER,
            PRIMARY KEY (user_id, item_id)
        );
        CREATE TABLE IF NOT EXISTS quests (
            user_id VARCHAR(50) REFERENCES players(user_id),
            quest_id VARCHAR(50),
            status VARCHAR(20), -- 'active', 'completed', 'failed'
            progress JSONB, -- e.g., {"killed_mobs": {"gopnik": 3}}
            PRIMARY KEY (user_id, quest_id)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def load_player(user_id):
    """Loads player data from the database by user_id."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT data FROM players WHERE user_id = %s", (str(user_id),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return None

def save_player(user_id, data):
    """Saves or updates player data in the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO players (user_id, data) 
        VALUES (%s, %s)
        ON CONFLICT (user_id) 
        DO UPDATE SET data = EXCLUDED.data;
    """, (str(user_id), json.dumps(data)))
    conn.commit()
    cur.close()
    conn.close()

def load_inventory(user_id):
    """Loads player inventory from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT item_id, quantity FROM inventory WHERE user_id = %s", (str(user_id),))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return {item[0]: item[1] for item in items}

def save_inventory(user_id, inventory_data):
    """Saves player inventory to the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM inventory WHERE user_id = %s", (str(user_id),))
    for item_id, quantity in inventory_data.items():
        if quantity > 0:
            cur.execute("""
                INSERT INTO inventory (user_id, item_id, quantity) 
                VALUES (%s, %s, %s);
            """, (str(user_id), item_id, quantity))
    conn.commit()
    cur.close()
    conn.close()

def load_quests(user_id):
    """Loads active quests for a player."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT quest_id, status, progress FROM quests WHERE user_id = %s AND status = 'active'", (str(user_id),))
    quests_data = cur.fetchall()
    cur.close()
    conn.close()
    return [{"quest_id": q[0], "status": q[1], "progress": q[2]} for q in quests_data]

def save_quest(user_id, quest_id, status, progress=None):
    """Saves or updates a quest's status and progress."""
    conn = get_db_connection()
    cur = conn.cursor()
    if progress is None:
        progress = {}
    cur.execute("""
        INSERT INTO quests (user_id, quest_id, status, progress) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, quest_id) 
        DO UPDATE SET status = EXCLUDED.status, progress = EXCLUDED.progress;
    """, (str(user_id), quest_id, status, json.dumps(progress)))
    conn.commit()
    cur.close()
    conn.close()

PLAYER_DEFAULTS = {
    "hp": 100, "max_hp": 100, "energy": 50, "max_energy": 100,
    "cash": 80, "xp": 0, "level": 1, "state": "IDLE",
    "location": "sotsgorod", "weapon": "кулаки", "armor": "без_брони",
    "strength": 5, "agility": 5, "intellect": 5,
    "last_action_time": 0
}

# 3.2. LOCATIONS
LOCATIONS = {
    "sotsgorod": {
        "name": "🌳 Соцгород (Парк Крылья Советов)",
        "desc": "Район сталинской застройки, ДК имени Ленина и Казанский авиационно-технический колледж (КАТК). Относительно тихий и спокойный район. По аллеям гуляют мамы с колясками, студенты КАТК спешат на пары. Здесь можно найти легкую добычу и встретить неагрессивных мобов.",
        "energy_cost": 10,
        "danger_level": "Низкий",
        "drop_items": ["медная_проволока", "стеклянная_бутылка", "купон_на_шаурму"],
        "mobs": [
            {"id": "student_katk", "name": "Студент-прогульщик КАТК 🎒", "hp": 20, "atk": 5, "xp": 10, "drop": {"cash": 5, "медная_проволока": 1}},
            {"id": "stray_dog", "name": "Бродячая собака 🐕", "hp": 15, "atk": 3, "xp": 8, "drop": {"стеклянная_бутылка": 1}}
        ],
        "events": ["encounter", "find_item", "rest_spot", "shop_visit"]
    },
    "karavaevo": {
        "name": "🏭 Караваево (промзона)",
        "desc": "Индустриальная зона, окруженная заборами авиастроительного завода КАПО им. Горбунова. Пахнет мазутом, керосином и тяжелым трудом. Вдоль гаражей и заброшенных складов можно встретить рабочих или тех, кто ищет приключения. Опасность средняя, но и добыча ценнее.",
        "energy_cost": 20,
        "danger_level": "Средний",
        "drop_items": ["медная_проволока", "железная_труба", "синяя_лента", "старый_аккумулятор"],
        "mobs": [
            {"id": "old_watchman", "name": "Сторож Михалыч с берданкой 👴", "hp": 40, "atk": 10, "xp": 25, "drop": {"cash": 15, "железная_труба": 1}},
            {"id": "tired_welder", "name": "Уставший сварщик третьего разряда 👷", "hp": 30, "atk": 7, "xp": 20, "drop": {"cash": 10, "синяя_лента": 1}},
            {"id": "garage_dog", "name": "Злая гаражная собака 🐶", "hp": 25, "atk": 6, "xp": 15, "drop": {"старый_аккумулятор": 1}}
        ],
        "events": ["encounter", "find_item", "craft_station", "work_opportunity"]
    },
    "zhilka": {
        "name": "🧱 Жилплощадка (Жилка)",
        "desc": "Легендарный и самый опасный микрорайон Авиастроя с суровой историей. Здесь не любят глупых вопросов и понтов. Чужаков видят за версту. Но именно на Жилке можно раздобыть самый ценный хабар и пройти настоящую проверку на прочность. Будь осторожен, здесь даже воздух тяжелый от былых разборок.",
        "energy_cost": 30,
        "danger_level": "ОЧЕНЬ ВЫСОКИЙ 💀",
        "drop_items": ["железная_труба", "синяя_лента", "старый_аккумулятор", "золотая_цепочка", "потрёпанная_зипка"],
        "mobs": [
            {"id": "gopnik_zhilka", "name": "Гопник с Жилки 🚸", "hp": 60, "atk": 15, "xp": 40, "drop": {"cash": 25, "золотая_цепочка": 1}},
            {"id": "local_authority", "name": "Местный авторитетный пацан Вахит 👑", "hp": 100, "atk": 25, "xp": 100, "drop": {"cash": 100, "потрёпанная_зипка": 1, "купон_на_шаурму": 3}},
            {"id": "sneaker_hunter", "name": "Охотник за кастомными кроссовками 👟", "hp": 70, "atk": 18, "xp": 50, "drop": {"cash": 30, "синяя_лента": 2, "потрёпанная_зипка": 1}}
        ],
        "events": ["encounter", "raid_base", "secret_shop", "gang_challenge"]
    }
}

# (Предметы)
ITEMS = {
    # Weapons
    "кулаки": {"name": "✊ Кулаки", "type": "weapon", "atk": 5, "price": 0, "desc": "Стартовое оружие. Всегда при тебе."},
    "медная_проволока": {"name": "🔗 Медная проволока", "type": "resource", "price": 10, "desc": "Можно продать или использовать в крафте."},
    "стеклянная_бутылка": {"name": "🍾 Стеклянная бутылка", "type": "resource", "price": 8, "desc": "Отлично подойдет для крафта метательного оружия."},
    "железная_труба": {"name": "🔨 Железная труба", "type": "weapon", "atk": 20, "price": 50, "desc": "Надежное оружие ближнего боя."},
    "синяя_лента": {"name": "🎗️ Синяя лента", "type": "resource", "price": 12, "desc": "Можно продать или использовать для крафта более мощной брони."},
    "старый_аккумулятор": {"name": "🔋 Старый аккумулятор", "type": "resource", "price": 20, "desc": "Ценный ресурс для продвинутого крафта."},
    "золотая_цепочка": {"name": "⚜️ Золотая цепочка", "type": "loot", "price": 75, "desc": "Дорогой трофей. Можно продать или подарить."},
    "потрёпанная_зипка": {"name": "🧥 Потрёпанная зипка", "type": "armor", "defense": 10, "price": 45, "desc": "Старая, но еще крепкая зипка. +10 к защите."},
    
    # Consumables
    "купон_на_шаурму": {"name": "🌯 Купон на шаурму", "type": "consumable", "heal": 50, "energy_regen": 20, "price": 30, "desc": "Быстрый способ восстановить здоровье и силы."},
    "энергетик": {"name": "⚡ Энергетик", "type": "consumable", "heal": 10, "energy_regen": 50, "price": 25, "desc": "Больше энергии для исследований."},

    # Crafted items
    "заточенная_труба": {"name": "🔪 Заточенная труба", "type": "weapon", "atk": 30, "price": 80, "desc": "Железная труба с заточенным концом. Урон повышен."},
    "импровизированный_щит": {"name": "🛡️ Импровизированный щит", "type": "armor", "defense": 20, "price": 70, "desc": "Сделан из подручных материалов. +20 к защите."}
}

# (Рецепты крафта)
CRAFTING_RECIPES = {
    "заточенная_труба": {
        "name": "Заточенная труба",
        "materials": {"железная_труба": 1, "медная_проволока": 2},
        "desc": "Из железной трубы и медной проволоки можно сделать более острое оружие."
    },
    "импровизированный_щит": {
        "name": "Импровизированный щит",
        "materials": {"стеклянная_бутылка": 3, "синяя_лента": 1},
        "desc": "Из бутылок и синей ленты можно собрать неплохую защиту."
    }
}

# (Ассортимент магазина)
SHOP_ITEMS = {
    "купон_на_шаурму": {"price": 30, "stock": 5},
    "энергетик": {"price": 25, "stock": 5},
    "железная_труба": {"price": 50, "stock": 3},
    "потрёпанная_зипка": {"price": 45, "stock": 2}
}

# (Квесты)
QUESTS_LIST = {
    "start_quest_katk": {
        "name": "Пропавший студент",
        "desc": "Говорят, в Соцгороде пропал студент КАТК. Найди его и узнай, что случилось. Возможно, он просто прогуливает пары.",
        "type": "kill_mob",
        "target": "student_katk",
        "count": 3,
        "reward": {"cash": 50, "xp": 30, "купон_на_шаурму": 1},
        "start_loc": "sotsgorod"
    },
    "find_resource_karavaevo": {
        "name": "Сбор ресурсов в промзоне",
        "desc": "На Караваево много заброшенных складов. Собери 5 кусков медной проволоки для крафта.",
        "type": "collect_item",
        "target": "медная_проволока",
        "count": 5,
        "reward": {"cash": 70, "xp": 40, "синяя_лента": 2},
        "start_loc": "karavaevo"
    },
    "zhilka_challenge": {
        "name": "Проверка на Жилки",
        "desc": "На Жилплощадке появился новый пацан, который охотится за кастомными кроссовками. Разберись с ним.",
        "type": "kill_mob",
        "target": "sneaker_hunter",
        "count": 1,
        "reward": {"cash": 100, "xp": 80, "золотая_цепочка": 1},
        "start_loc": "zhilka"
    }
}



def generate_player_markup(player_data):
    """Generates the main inline keyboard for player actions."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🗺️ Карта", callback_data="open_map"),
               types.InlineKeyboardButton("🎒 Инвентарь", callback_data="open_inv"))
    markup.add(types.InlineKeyboardButton("⚔️ В бой", callback_data="start_combat"),
               types.InlineKeyboardButton("💰 Магазин", callback_data="open_shop"))
    markup.add(types.InlineKeyboardButton("🔨 Крафт", callback_data="open_craft"),
               types.InlineKeyboardButton("📜 Задания", callback_data="open_quests"))
    return markup

def get_player_status_text(player_data):
    """Returns a formatted string of player's current status."""
    location_name = LOCATIONS.get(player_data["location"], {"name": "Неизвестно"})["name"]
    weapon_name = ITEMS.get(player_data["weapon"], {"name": "Кулаки"})["name"]
    armor_name = ITEMS.get(player_data["armor"], {"name": "Без брони"})["name"]
    
    status_text = (
        f"📊 **СТАТУС ПЕРСОНАЖА:**\n"
        f"👤 Имя: {player_data['name']}\n"
        f"🌟 Уровень: {player_data['level']} (XP: {player_data['xp']})\n"
        f"❤️ Здоровье: {player_data['hp']}/{player_data['max_hp']}\n"
        f"⚡ Энергия: {player_data['energy']}/{player_data['max_energy']}\n"
        f"💰 Кэш: {player_data['cash']}\n"
        f"🗺️ Локация: {location_name}\n"
        f"✊ Оружие: {weapon_name} (ATK: {ITEMS.get(player_data['weapon'], {'atk': 5})['atk']})\n"
        f"🛡️ Броня: {armor_name} (DEF: {ITEMS.get(player_data['armor'], {'defense': 0})['defense']})\n"
    )
    return status_text

def calculate_attack_damage(player_data):
    """Calculates player's total attack damage."""
    weapon_atk = ITEMS.get(player_data["weapon"], {"atk": 5})["atk"]
    strength_bonus = player_data["strength"] * 0.5 # Example strength bonus
    return weapon_atk + strength_bonus + random.randint(-2, 5) # Random variance

def calculate_defense_rating(player_data):
    """Calculates player's total defense rating."""
    armor_def = ITEMS.get(player_data["armor"], {"defense": 0})["defense"]
    agility_bonus = player_data["agility"] * 0.3 # Example agility bonus
    return armor_def + agility_bonus

def gain_xp(player_data, amount, bot_instance, chat_id):
    """Adds XP to player and handles leveling up."""
    player_data['xp'] += amount
    level_up_xp = player_data['level'] * 100 # XP needed for next level
    if player_data['xp'] >= level_up_xp:
        player_data['level'] += 1
        player_data['max_hp'] += 10
        player_data['hp'] = player_data['max_hp']
        player_data['max_energy'] += 5
        player_data['energy'] = player_data['max_energy']
        player_data['strength'] += 1
        player_data['agility'] += 1
        player_data['intellect'] += 1
        player_data['xp'] = 0 # Reset XP for new level
        bot_instance.send_message(chat_id, f"🎉 **ПОЗДРАВЛЯЕМ!** Вы достигли {player_data['level']} уровня!\nВаши характеристики улучшились!")
    return player_data

def restore_energy(player_data, amount):
    """Restores player's energy."""
    player_data['energy'] = min(player_data['max_energy'], player_data['energy'] + amount)
    return player_data

def restore_hp(player_data, amount):
    """Restores player's HP."""
    player_data['hp'] = min(player_data['max_hp'], player_data['hp'] + amount)
    return player_data



@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    """Webhook endpoint for receiving updates from Telegram."""
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/backup', methods=['GET'])
def send_backup():
    """Endpoint to trigger a database backup and send it to ADMIN_ID."""
    try:
        # Construct DATABASE_URL for pg_dump
        db_parts = DATABASE_URL.split('://')[1].split('@')
        user_pass = db_parts[0].split(':')
        host_port_db = db_parts[1].split('/')
        host_port = host_port_db[0].split(':')
        db_name = host_port_db[1]

        pg_dump_cmd = (
            f"PGUSER={user_pass[0]} PGPASSWORD={user_pass[1]} "
            f"pg_dump -h {host_port[0]} -p {host_port[1]} -d {db_name} > backup.sql"
        )
        os.system(pg_dump_cmd)

        with open("backup.sql", "rb") as f:
            bot.send_document(ADMIN_ID, f, caption="📂 Автоматический бэкап базы данных Postgres!")
        return "Backup sent!", 200
    except Exception as e:
        # Log error for debugging
        print(f"Backup failed: {e}")
        return str(e), 500



@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    """Handles /start and /help commands."""
    user_id = str(message.from_user.id)
    player_data = load_player(user_id)

    if not player_data:
        player_data = PLAYER_DEFAULTS.copy()
        player_data["name"] = message.from_user.first_name if message.from_user.first_name else "Неизвестный"
        player_data["user_id"] = user_id # Ensure user_id is saved
        save_player(user_id, player_data)
        save_inventory(user_id, {"кулаки": 1}) # Start with fists
        bot.send_message(
            message.chat.id,
            f"Привет, {player_data['name']}! Добро пожаловать в Авиастрой RPG.\n"
            f"Здесь выживает сильнейший. Для начала осмотритесь на карте.",
            reply_markup=generate_player_markup(player_data)
        )
    else:
        bot.send_message(
            message.chat.id,
            f"С возвращением, {player_data['name']}!\n"
            f"Чем займемся сегодня?\n" + get_player_status_text(player_data),
            reply_markup=generate_player_markup(player_data),
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['reset_player'])
def handle_reset_player(message):
    """ADMIN COMMAND: Resets player data to default (for testing)."""
    user_id = str(message.from_user.id)
    if user_id == ADMIN_ID:
        player_data = PLAYER_DEFAULTS.copy()
        player_data["name"] = message.from_user.first_name if message.from_user.first_name else "Админ"
        player_data["user_id"] = user_id
        save_player(user_id, player_data)
        save_inventory(user_id, {"кулаки": 1})
        save_quest(user_id, "start_quest_katk", "active", {}) # Assign a default quest
        bot.send_message(message.chat.id, "Ваш персонаж был сброшен до начальных настроек.", reply_markup=generate_player_markup(player_data))
    else:
        bot.send_message(message.chat.id, "У вас нет прав для этой команды.")



@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    """Handles all inline keyboard callback queries."""
    user_id = str(call.from_user.id)
    player_data = load_player(user_id)
    if not player_data:
        bot.answer_callback_query(call.id, "Ваш персонаж не найден. Напишите /start")
        return

    action = call.data

    if action == "open_map":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for loc_id, loc_info in LOCATIONS.items():
            markup.add(types.InlineKeyboardButton(f"{loc_info['name']} (Стоимость: {loc_info['energy_cost']}⚡)", callback_data=f"go_loc_{loc_id}"))
        bot.edit_message_text(
            f"🗺️ **Карта Авиастроя**\n"
            f"Ваша текущая энергия: {player_data['energy']}/{player_data['max_energy']}⚡\n"
            f"Выберите локацию для перемещения:",
            call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
    elif action.startswith("go_loc_"):
        loc_id = action.replace("go_loc_", "")
        location_info = LOCATIONS.get(loc_id)
        if location_info:
            if player_data['energy'] >= location_info['energy_cost']:
                player_data['location'] = loc_id
                player_data['energy'] -= location_info['energy_cost']
                save_player(user_id, player_data)
                bot.edit_message_text(
                    f"✅ Вы прибыли в: {location_info['name']}!\n"
                    f"{location_info['desc']}\n"
                    f"Оставшаяся энергия: {player_data['energy']}⚡",
                    call.message.chat.id, call.message.message_id, reply_markup=generate_player_markup(player_data), parse_mode="Markdown"
                )
                # Trigger location event
                trigger_location_event(user_id, player_data, loc_id, call)
            else:
                bot.answer_callback_query(call.id, "Недостаточно энергии для перемещения!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "Неизвестная локация.")

    elif action == "open_inv":
        inventory = load_inventory(user_id)
        inv_text = "🎒 **ВАШ ИНВЕНТАРЬ:**\n"
        if not inventory or all(qty == 0 for qty in inventory.values()):
            inv_text += "Инвентарь пуст.\n"
        else:
            for item_id, qty in inventory.items():
                if qty > 0:
                    item_info = ITEMS.get(item_id, {"name": item_id})
                    inv_text += f"- {item_info['name']}: {qty} шт.\n"
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        # Add buttons to equip weapon/armor or use consumable
        equip_buttons = []
        for item_id, qty in inventory.items():
            if qty > 0:
                item_info = ITEMS.get(item_id, {})
                if item_info.get("type") == "weapon" and item_id != player_data["weapon"]:
                    equip_buttons.append(types.InlineKeyboardButton(f"✊ Экипировать {item_info['name']}", callback_data=f"equip_{item_id}"))
                elif item_info.get("type") == "armor" and item_id != player_data["armor"]:
                    equip_buttons.append(types.InlineKeyboardButton(f"🛡️ Надеть {item_info['name']}", callback_data=f"equip_{item_id}"))
                elif item_info.get("type") == "consumable":
                    equip_buttons.append(types.InlineKeyboardButton(f"💊 Использовать {item_info['name']}", callback_data=f"use_{item_id}"))
        if equip_buttons:
            markup.add(*equip_buttons)
        markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu"))
        bot.edit_message_text(inv_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif action.startswith("equip_"):
        item_id = action.replace("equip_", "")
        inventory = load_inventory(user_id)
        item_info = ITEMS.get(item_id)
        if item_info and inventory.get(item_id, 0) > 0:
            if item_info["type"] == "weapon":
                player_data["weapon"] = item_id
                save_player(user_id, player_data)
                bot.answer_callback_query(call.id, f"Вы экипировали {item_info['name']}.")
            elif item_info["type"] == "armor":
                player_data["armor"] = item_id
                save_player(user_id, player_data)
                bot.answer_callback_query(call.id, f"Вы надели {item_info['name']}.")
            else:
                bot.answer_callback_query(call.id, "Это нельзя экипировать.")
        else:
            bot.answer_callback_query(call.id, "У вас нет такого предмета.")
        # Refresh inventory display
        handle_callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, data="open_inv"))

    elif action.startswith("use_"):
        item_id = action.replace("use_", "")
        inventory = load_inventory(user_id)
        item_info = ITEMS.get(item_id)
        if item_info and item_info.get("type") == "consumable" and inventory.get(item_id, 0) > 0:
            inventory[item_id] -= 1
            if inventory[item_id] == 0:
                del inventory[item_id]
            save_inventory(user_id, inventory)

            player_data = restore_hp(player_data, item_info.get("heal", 0))
            player_data = restore_energy(player_data, item_info.get("energy_regen", 0))
            save_player(user_id, player_data)
            bot.answer_callback_query(call.id, f"Вы использовали {item_info['name']}!")
            bot.edit_message_text(
                f"Вы использовали {item_info['name']}.\n" + get_player_status_text(player_data),
                call.message.chat.id, call.message.message_id, reply_markup=generate_player_markup(player_data), parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "Нельзя использовать или предмета нет.")
        # Refresh inventory display
        handle_callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, data="open_inv"))

    elif action == "start_combat":
        # Check if player is already in combat (simple state management)
        if player_data.get("state") == "COMBAT":
            bot.answer_callback_query(call.id, "Вы уже в бою!")
            return
        
        location_info = LOCATIONS.get(player_data['location'])
        if not location_info or not location_info['mobs']:
            bot.answer_callback_query(call.id, "В этой локации нет противников.")
            return

        mob_info = random.choice(location_info['mobs'])
        player_data["state"] = "COMBAT"
        player_data["current_mob"] = mob_info['id']
        player_data["mob_hp"] = mob_info['hp']
        save_player(user_id, player_data)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(f"⚔️ Атаковать {mob_info['name']}", callback_data="attack_mob"))
        bot.edit_message_text(
            f"Вы встретили {mob_info['name']}! У него {mob_info['hp']} HP.\n"
            f"Ваше HP: {player_data['hp']}/{player_data['max_hp']}",
            call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
    
    elif action == "attack_mob":
        if player_data.get("state") != "COMBAT":
            bot.answer_callback_query(call.id, "Вы не в бою.")
            return

        mob_id = player_data["current_mob"]
        location_info = LOCATIONS.get(player_data['location'])
        mob_info = next((m for m in location_info['mobs'] if m['id'] == mob_id), None)

        if not mob_info:
            bot.answer_callback_query(call.id, "Противник не найден.")
            player_data["state"] = "IDLE"
            save_player(user_id, player_data)
            return

        player_atk = calculate_attack_damage(player_data)
        mob_def = random.randint(0, mob_info['atk'] // 2) # Simple mob defense
        
        # Player attacks mob
        damage_to_mob = max(1, player_atk - mob_def)
        player_data["mob_hp"] -= damage_to_mob
        combat_log = f"Вы атаковали {mob_info['name']} на {damage_to_mob} урона. "

        if player_data["mob_hp"] <= 0:
            # Mob defeated
            xp_gain = mob_info['xp']
            cash_drop = mob_info['drop'].get('cash', 0)
            item_drops = {k:v for k,v in mob_info['drop'].items() if k != 'cash'}
            
            player_data = gain_xp(player_data, xp_gain, bot, call.message.chat.id)
            player_data['cash'] += cash_drop
            save_player(user_id, player_data)
            
            inventory = load_inventory(user_id)
            drop_text = ""
            for item_id, qty in item_drops.items():
                inventory[item_id] = inventory.get(item_id, 0) + qty
                item_name = ITEMS.get(item_id, {"name": item_id})["name"]
                drop_text += f", получили {qty} {item_name}"
            save_inventory(user_id, inventory)

            combat_log += f"{mob_info['name']} повержен! Вы получили {xp_gain} XP, {cash_drop} кэша{drop_text}."
            player_data["state"] = "IDLE"
            player_data.pop("current_mob", None)
            player_data.pop("mob_hp", None)
            save_player(user_id, player_data)
            bot.edit_message_text(
                combat_log + "\n" + get_player_status_text(player_data),
                call.message.chat.id, call.message.message_id, reply_markup=generate_player_markup(player_data), parse_mode="Markdown"
            )
            # Check quest progress
            check_quest_progress(user_id, "kill_mob", mob_id, 1, bot, call.message.chat.id)
            return
        
        mob_atk = mob_info['atk']
        player_def = calculate_defense_rating(player_data)
        damage_to_player = max(1, mob_atk - player_def - random.randint(-3, 3)) # Add variance

        player_data['hp'] -= damage_to_player
        combat_log += f"{mob_info['name']} атаковал вас на {damage_to_player} урона.\n"

        if player_data['hp'] <= 0:
            # Player defeated
            player_data['hp'] = player_data['max_hp'] // 2 # Respawn with half HP
            player_data['cash'] = max(0, player_data['cash'] - 20) # Lose some cash
            player_data["state"] = "IDLE"
            player_data.pop("current_mob", None)
            player_data.pop("mob_hp", None)
            save_player(user_id, player_data)
            bot.edit_message_text(
                combat_log + "Вы были повержены! Потеряли 20 кэша и возродились с половиной HP.\n" + get_player_status_text(player_data),
                call.message.chat.id, call.message.message_id, reply_markup=generate_player_markup(player_data), parse_mode="Markdown"
            )
            return

        save_player(user_id, player_data)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(f"⚔️ Атаковать {mob_info['name']}", callback_data="attack_mob"))
        bot.edit_message_text(
            f"{combat_log}\n"
            f"Ваше HP: {player_data['hp']}/{player_data['max_hp']} | HP {mob_info['name']}: {player_data['mob_hp']}",
            call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
    
    elif action == "open_shop":
        markup = types.InlineKeyboardMarkup(row_width=1)
        shop_text = "💰 **МАГАЗИН:**\n"
        for item_id, item_info in SHOP_ITEMS.items():
            shop_text += f"- {ITEMS[item_id]['name']}: {item_info['price']} 💰 (В наличии: {item_info['stock']} шт.)\n"
            markup.add(types.InlineKeyboardButton(f"Купить {ITEMS[item_id]['name']}", callback_data=f"buy_{item_id}"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu"))
        bot.edit_message_text(shop_text + f"\nВаш кэш: {player_data['cash']} 💰", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif action.startswith("buy_"):
        item_id = action.replace("buy_", "")
        item_in_shop = SHOP_ITEMS.get(item_id)
        item_info = ITEMS.get(item_id)
        if item_in_shop and item_info:
            if player_data['cash'] >= item_in_shop['price']:
                if item_in_shop['stock'] > 0:
                    player_data['cash'] -= item_in_shop['price']
                    save_player(user_id, player_data)
                    inventory = load_inventory(user_id)
                    inventory[item_id] = inventory.get(item_id, 0) + 1
                    save_inventory(user_id, inventory)
                    SHOP_ITEMS[item_id]['stock'] -= 1 # Decrease stock (for this session, won't persist after bot restart)
                    bot.answer_callback_query(call.id, f"Вы купили {item_info['name']} за {item_in_shop['price']} кэша.")
                else:
                    bot.answer_callback_query(call.id, f"{item_info['name']} закончился!")
            else:
                bot.answer_callback_query(call.id, "Недостаточно кэша!")
        else:
            bot.answer_callback_query(call.id, "Такого предмета нет в магазине.")
        # Refresh shop display
        handle_callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, data="open_shop"))

    elif action == "open_craft":
        markup = types.InlineKeyboardMarkup(row_width=1)
        craft_text = "🔨 **СТАНЦИЯ КРАФТА:**\n"
        inventory = load_inventory(user_id)
        
        for recipe_id, recipe_info in CRAFTING_RECIPES.items():
            can_craft = True
            materials_needed_text = []
            for mat_id, mat_qty in recipe_info['materials'].items():
                if inventory.get(mat_id, 0) < mat_qty:
                    can_craft = False
                materials_needed_text.append(f"{ITEMS[mat_id]['name']}: {inventory.get(mat_id, 0)}/{mat_qty}")
            
            craft_text += f"\n- {recipe_info['name']}:\n  Материалы: {', '.join(materials_needed_text)}\n"
            if can_craft:
                markup.add(types.InlineKeyboardButton(f"Создать {recipe_info['name']}", callback_data=f"craft_{recipe_id}"))
            else:
                markup.add(types.InlineKeyboardButton(f"⚠️ Не хватает материалов для {recipe_info['name']}", callback_data="ignore_button"))
        
        markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu"))
        bot.edit_message_text(craft_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif action.startswith("craft_"):
        recipe_id = action.replace("craft_", "")
        recipe_info = CRAFTING_RECIPES.get(recipe_id)
        if recipe_info:
            inventory = load_inventory(user_id)
            can_craft = True
            for mat_id, mat_qty in recipe_info['materials'].items():
                if inventory.get(mat_id, 0) < mat_qty:
                    can_craft = False
                    break
            
            if can_craft:
                for mat_id, mat_qty in recipe_info['materials'].items():
                    inventory[mat_id] -= mat_qty
                    if inventory[mat_id] == 0:
                        del inventory[mat_id]
                
                # Add crafted item
                inventory[recipe_id] = inventory.get(recipe_id, 0) + 1
                save_inventory(user_id, inventory)
                bot.answer_callback_query(call.id, f"Вы успешно создали {recipe_info['name']}!")
            else:
                bot.answer_callback_query(call.id, "Недостаточно материалов для крафта.")
        else:
            bot.answer_callback_query(call.id, "Неизвестный рецепт.")
        
        # Refresh craft display
        handle_callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, data="open_craft"))

    elif action == "open_quests":
        active_quests = load_quests(user_id)
        quests_text = "📜 **ВАШИ ЗАДАНИЯ:**\n"
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        if not active_quests:
            quests_text += "У вас нет активных заданий.\n"
            # Offer new quests
            for q_id, q_info in QUESTS_LIST.items():
                if q_info.get("start_loc") == player_data["location"]:
                    markup.add(types.InlineKeyboardButton(f"Принять '{q_info['name']}'", callback_data=f"accept_quest_{q_id}"))
        else:
            for quest in active_quests:
                quest_info = QUESTS_LIST.get(quest['quest_id'])
                if quest_info:
                    quests_text += f"**- '{quest_info['name']}':** {quest_info['desc']}\n  _Прогресс:_ {format_quest_progress(quest['progress'], quest_info)}\n"
                    # Add buttons for quest actions if any
        
        markup.add(types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="main_menu"))
        bot.edit_message_text(quests_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif action.startswith("accept_quest_"):
        quest_id = action.replace("accept_quest_", "")
        quest_info = QUESTS_LIST.get(quest_id)
        if quest_info:
            active_quests = load_quests(user_id)
            if not any(q['quest_id'] == quest_id for q in active_quests):
                save_quest(user_id, quest_id, "active", {})
                bot.answer_callback_query(call.id, f"Вы приняли задание '{quest_info['name']}'!")
            else:
                bot.answer_callback_query(call.id, "Вы уже выполняете это задание.")
        else:
            bot.answer_callback_query(call.id, "Неизвестное задание.")
        handle_callbacks(types.CallbackQuery(id=call.id, from_user=call.from_user, message=call.message, data="open_quests"))

    elif action == "main_menu":
        bot.edit_message_text(
            f"Что дальше, {player_data['name']}?\n" + get_player_status_text(player_data),
            call.message.chat.id, call.message.message_id, reply_markup=generate_player_markup(player_data), parse_mode="Markdown"
        )
    elif action == "ignore_button":
        bot.answer_callback_query(call.id, "Это просто информационная кнопка.")


# --- 8. QUEST SYSTEM UTILITIES ---

def format_quest_progress(progress, quest_info):
    """Formats quest progress for display."""
    if quest_info['type'] == "kill_mob":
        killed = progress.get("killed_mobs", {}).get(quest_info['target'], 0)
        return f"{killed}/{quest_info['count']} {QUESTS_LIST[quest_info['quest_id']]['mobs'][0]['name']} убито"
    elif quest_info['type'] == "collect_item":
        collected = progress.get("collected_items", {}).get(quest_info['target'], 0)
        return f"{collected}/{quest_info['count']} {ITEMS[quest_info['target']]['name']} собрано"
    return "Неизвестный прогресс"

def check_quest_progress(user_id, event_type, target_id, count, bot_instance, chat_id):
    """Checks and updates player's active quests based on game events."""
    active_quests = load_quests(user_id)
    player_data = load_player(user_id)

    for quest in active_quests:
        quest_info = QUESTS_LIST.get(quest['quest_id'])
        if not quest_info or quest['status'] != 'active':
            continue

        progress = quest.get('progress', {})
        
        if quest_info['type'] == event_type and quest_info['target'] == target_id:
            if event_type == "kill_mob":
                progress_key = "killed_mobs"
            elif event_type == "collect_item":
                progress_key = "collected_items"
            else:
                continue

            current_count = progress.get(progress_key, {}).get(target_id, 0)
            progress.setdefault(progress_key, {})[target_id] = current_count + count

            if progress[progress_key][target_id] >= quest_info['count']:
                # Quest completed!
                reward = quest_info['reward']
                player_data['cash'] += reward.get('cash', 0)
                player_data = gain_xp(player_data, reward.get('xp', 0), bot_instance, chat_id)
                save_player(user_id, player_data)

                inventory = load_inventory(user_id)
                reward_item_text = ""
                for item_id, qty in reward.items():
                    if item_id != 'cash' and item_id != 'xp':
                        inventory[item_id] = inventory.get(item_id, 0) + qty
                        reward_item_text += f", {qty} {ITEMS[item_id]['name']}"
                save_inventory(user_id, inventory)

                save_quest(user_id, quest['quest_id'], "completed", progress)
                bot_instance.send_message(
                    chat_id,
                    f"🎉 **Задание '{quest_info['name']}' выполнено!**\n"
                    f"Вы получили {reward.get('cash', 0)} кэша, {reward.get('xp', 0)} XP{reward_item_text}."
                    f"\n" + get_player_status_text(player_data),
                    parse_mode="Markdown"
                )
            else:
                save_quest(user_id, quest['quest_id'], "active", progress)



def trigger_location_event(user_id, player_data, location_id, call):
    """Triggers a random event when player enters a location."""
    location_info = LOCATIONS[location_id]
    event_type = random.choice(location_info['events']) # Choose a random event type
    
    if event_type == "find_item":
        if location_info['drop_items'] and random.random() < 0.3: # 30% chance to find
            found_item_id = random.choice(location_info['drop_items'])
            item_info = ITEMS.get(found_item_id)
            if item_info:
                inventory = load_inventory(user_id)
                inventory[found_item_id] = inventory.get(found_item_id, 0) + 1
                save_inventory(user_id, inventory)
                bot.send_message(call.message.chat.id, f"Вы нашли {item_info['name']}!")
                check_quest_progress(user_id, "collect_item", found_item_id, 1, bot, call.message.chat.id)
    elif event_type == "rest_spot":
        if random.random() < 0.5: # 50% chance to find a rest spot
            hp_gain = random.randint(10, 30)
            energy_gain = random.randint(10, 20)
            player_data = restore_hp(player_data, hp_gain)
            player_data = restore_energy(player_data, energy_gain)
            save_player(user_id, player_data)
            bot.send_message(call.message.chat.id, f"Вы нашли укромное место для отдыха. Восстановлено {hp_gain} HP и {energy_gain} энергии.")
    elif event_type == "work_opportunity":
        if random.random() < 0.4 and player_data['location'] == "karavaevo": # Only in Karavaevo
            cash_gain = random.randint(30, 80)
            xp_gain = random.randint(10, 20)
            player_data['cash'] += cash_gain
            player_data = gain_xp(player_data, xp_gain, bot, call.message.chat.id)
            save_player(user_id, player_data)
            bot.send_message(call.message.chat.id, f"Нашлась халтурка! Вы заработали {cash_gain} кэша и {xp_gain} XP.")


# --- 10. MAIN BOT POLLING/WEBHOOK START ---
if __name__ == "__main__":
    init_db() # Ensure DB is initialized before starting bot
    bot.remove_webhook() # Always remove previous webhook for safety
    bot.set_webhook(url=f"https://{WEBHOOK_HOST}/{TOKEN}") # Set new webhook
    # Flask app will run and listen for incoming webhook requests
    app.run(host="0.0.0.0", port=WEBHOOK_PORT)
