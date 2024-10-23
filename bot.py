import telebot
from telebot import types
from telebot.apihelper import ApiException

BOT_TOKEN = 'YOUR_BOT_TOKEN' # Reemplaza con tu token de bot
bot = telebot.TeleBot(BOT_TOKEN)

# Diccionario para almacenar información de los grupos
groups = {}

# Función para obtener información del grupo
def get_group_info(chat_id):
    if chat_id in groups:
        return groups[chat_id]
    else:
        return None

# Función para agregar un grupo al diccionario
def add_group(chat_id, group_name):
    groups[chat_id] = {
        "name": group_name,
        "members": [],
        "admins": [],
        "muted": [],
        "kicked": [],
        "banned": [],
        "rules": [],
        "welcome_message": "Bienvenido a este grupo!",
        "goodbye_message": "Hasta pronto!",
    }

# Función para agregar un miembro al grupo
def add_member(chat_id, member_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if member_id not in group_info["members"]:
            group_info["members"].append(member_id)
            groups[chat_id] = group_info

# Función para agregar un administrador al grupo
def add_admin(chat_id, admin_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if admin_id not in group_info["admins"]:
            group_info["admins"].append(admin_id)
            groups[chat_id] = group_info

# Función para silenciar a un miembro
def mute_member(chat_id, member_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if member_id not in group_info["muted"]:
            group_info["muted"].append(member_id)
            groups[chat_id] = group_info

# Función para desmutear a un miembro
def unmute_member(chat_id, member_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if member_id in group_info["muted"]:
            group_info["muted"].remove(member_id)
            groups[chat_id] = group_info

# Función para expulsar a un miembro
def kick_member(chat_id, member_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if member_id in group_info["members"]:
            group_info["members"].remove(member_id)
            group_info["kicked"].append(member_id)
            groups[chat_id] = group_info

# Función para eliminar un miembro (eliminar de la lista de expulsados)
def remove_member_from_kicked(chat_id, member_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if member_id in group_info["kicked"]:
            group_info["kicked"].remove(member_id)
            groups[chat_id] = group_info

# Función para banear a un miembro
def ban_member(chat_id, member_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if member_id not in group_info["banned"]:
            group_info["banned"].append(member_id)
            groups[chat_id] = group_info

# Función para desbanear a un miembro
def unban_member(chat_id, member_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if member_id in group_info["banned"]:
            group_info["banned"].remove(member_id)
            groups[chat_id] = group_info

# Función para agregar una regla
def add_rule(chat_id, rule):
    group_info = get_group_info(chat_id)
    if group_info:
        if rule not in group_info["rules"]:
            group_info["rules"].append(rule)
            groups[chat_id] = group_info

# Función para eliminar una regla
def remove_rule(chat_id, rule):
    group_info = get_group_info(chat_id)
    if group_info:
        if rule in group_info["rules"]:
            group_info["rules"].remove(rule)
            groups[chat_id] = group_info

# Función para listar miembros del grupo
def list_members(chat_id):
    group_info = get_group_info(chat_id)
    if group_info:
        members = ", ".join(
            [f"@{member_id}" for member_id in group_info["members"]]
        )
        return f"Miembros del grupo {group_info['name']}: {members}"
    else:
        return "No se encontró información del grupo."

# Función para listar administradores del grupo
def list_admins(chat_id):
    group_info = get_group_info(chat_id)
    if group_info:
        admins = ", ".join(
            [f"@{admin_id}" for admin_id in group_info["admins"]]
        )
        return f"Administradores del grupo {group_info['name']}: {admins}"
    else:
        return "No se encontró información del grupo."

# Función para listar miembros silenciados
def list_muted(chat_id):
    group_info = get_group_info(chat_id)
    if group_info:
        muted = ", ".join(
            [f"@{member_id}" for member_id in group_info["muted"]]
        )
        return f"Miembros silenciados en {group_info['name']}: {muted}"
    else:
        return "No se encontró información del grupo."

# Función para listar miembros expulsados
def list_kicked(chat_id):
    group_info = get_group_info(chat_id)
    if group_info:
        kicked = ", ".join(
            [f"@{member_id}" for member_id in group_info["kicked"]]
        )
        return f"Miembros expulsados de {group_info['name']}: {kicked}"
    else:
        return "No se encontró información del grupo."

# Función para listar miembros baneados
def list_banned(chat_id):
    group_info = get_group_info(chat_id)
    if group_info:
        banned = ", ".join(
            [f"@{member_id}" for member_id in group_info["banned"]]
        )
        return f"Miembros baneados de {group_info['name']}: {banned}"
    else:
        return "No se encontró información del grupo."

# Función para listar reglas del grupo
def list_rules(chat_id):
    group_info = get_group_info(chat_id)
    if group_info:
        if group_info["rules"]:
            rules = "\n".join(group_info["rules"])
            return f"Reglas de {group_info['name']}: \n{rules}"
        else:
            return f"No hay reglas establecidas para {group_info['name']}"
    else:
        return "No se encontró información del grupo."

# Función para obtener la información de un usuario
def get_user_info(user_id):
    try:
        user = bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else "Sin usuario"
        groups_count = 0 # Inicializa la cantidad de grupos a 0
        for chat in bot.get_updates():
            if user_id in chat.message.chat.members:
                groups_count += 1
        return f"Nombre: {user.first_name} {user.last_name}\nUsuario: {username}\nID: {user_id}\nGrupos: {groups_count}"
    except ApiException as e:
        return f"Error al obtener la información del usuario: {e}"

# Función para establecer el mensaje de bienvenida
def set_welcome_message(chat_id, message):
    group_info = get_group_info(chat_id)
    if group_info:
        group_info["welcome_message"] = message
        groups[chat_id] = group_info
        bot.send_message(chat_id, f"Se estableció el mensaje de bienvenida a: {message}")
    else:
        bot.send_message(chat_id, "No se encontró información del grupo.")

# Función para establecer el mensaje de despedida
def set_goodbye_message(chat_id, message):
    group_info = get_group_info(chat_id)
    if group_info:
        group_info["goodbye_message"] = message
        groups[chat_id] = group_info
        bot.send_message(chat_id, f"Se estableció el mensaje de despedida a: {message}")
    else:
        bot.send_message(chat_id, "No se encontró información del grupo.")

# Función para manejar comandos de grupo
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    chat_id = message.chat.id
    if message.chat.type == "group" or message.chat.type == "supergroup":
        group_name = message.chat.title
        add_group(chat_id, group_name)
        bot.send_message(
            chat_id,
            f"¡Hola! 👋 Este bot se encargará de la gestión de este grupo. Puedes usar los siguientes comandos:\n\n"
            f"/addmember @[usuario] - Agregar un miembro al grupo\n"
            f"/addadmin @[usuario] - Agregar un administrador al grupo\n"
            f"/removemember @[usuario] - Eliminar un miembro del grupo\n"
            f"/removeadmin @[usuario] - Eliminar un administrador del grupo\n"
            f"/mute @[usuario] - Silenciar a un miembro\n"
            f"/unmute @[usuario] - Desmutear a un miembro\n"
            f"/kick @[usuario] - Expulsar a un miembro\n"
            f"/unban @[usuario] - Desbanear a un miembro\n"
            f"/ban @[usuario] - Banear a un miembro\n"
            f"/listmembers - Listar los miembros del grupo\n"
            f"/listadmins - Listar los administradores del grupo\n"
            f"/listmuted - Listar los miembros silenciados\n"
            f"/listkicked - Listar los miembros expulsados\n"
            f"/listbanned - Listar los miembros baneados\n"
            f"/addrule [regla] - Agregar una regla al grupo\n"
            f"/removerule [regla] - Eliminar una regla del grupo\n"
            f"/listrules - Listar las reglas del grupo\n"
            f"/info - Mostrar información del grupo\n"
            f"/infouser @[usuario] - Mostrar información de un usuario\n"
            f"/welcome [mensaje] - Establecer el mensaje de bienvenida\n"
            f"/goodbye [mensaje] - Establecer el mensaje de despedida\n"
        )
    else:
        bot.send_message(
            chat_id,
            "Este bot solo funciona en grupos o supergrupos. ¡Agrega el bot a un grupo!",
        )

# Manejador para comandos con @usuario
@bot.message_handler(
    commands=[
        "addmember",
        "addadmin",
        "removemember",
        "removeadmin",
        "mute",
        "unmute",
        "kick",
        "unban",
        "ban",
        "infouser",
    ]
)
def handle_user_commands(message):
    chat_id = message.chat.id
    args = message.text.split()[1:]
    if args:
        username = args[0]
        if username.startswith("@"):
            username = username[1:]
        # Obtener el ID del usuario por su nombre de usuario
        try:
            user = bot.get_chat_member(chat_id, username).user
            user_id = user.id
            if message.text.startswith("/addmember"):
                add_member(chat_id, user_id)
                bot.send_message(chat_id, f"Se agregó {username} al grupo.")
            elif message.text.startswith("/addadmin"):
                add_admin(chat_id, user_id)
                bot.send_message(chat_id, f"Se agregó {username} como administrador.")
            elif message.text.startswith("/removemember"):
                remove_member(chat_id, user_id)
                bot.send_message(chat_id, f"Se eliminó {username} del grupo.")
            elif message.text.startswith("/removeadmin"):
                remove_admin(chat_id, user_id)
                bot.send_message(chat_id, f"Se eliminó {username} de la lista de administradores.")
            elif message.text.startswith("/mute"):
                mute_member(chat_id, user_id)
                bot.send_message(chat_id, f"Se silenciò a {username} en el grupo.")
            elif message.text.startswith("/unmute"):
                unmute_member(chat_id, user_id)
                bot.send_message(chat_id, f"Se desmuteó a {username} en el grupo.")
            elif message.text.startswith("/kick"):
                kick_member(chat_id, user_id)
                bot.send_message(chat_id, f"Se expulsó a {username} del grupo.")
            elif message.text.startswith("/unban"):
                unban_member(chat_id, user_id)
                bot.send_message(chat_id, f"Se desbanearon a {username} en el grupo.")
            elif message.text.startswith("/ban"):
                ban_member(chat_id, user_id)
                bot.send_message(chat_id, f"Se banearon a {username} en el grupo.")
            elif message.text.startswith("/infouser"):
                user_info = get_user_info(user_id)
                bot.send_message(chat_id, user_info)
        except telebot.apihelper.ApiException as e:
            bot.send_message(
                chat_id, f"Error al encontrar al usuario {username}: {e}"
            )
    else:
        bot.send_message(chat_id, "Por favor, introduce el nombre de usuario del miembro (@username).")

# Manejador para comandos de lista
@bot.message_handler(
    commands=[
        "listmembers",
        "listadmins",
        "listmuted",
        "listkicked",
        "listbanned",
        "listrules",
    ]
)
def handle_list_commands(message):
    chat_id = message.chat.id
    if message.text.startswith("/listmembers"):
        members_list = list_members(chat_id)
        bot.send_message(chat_id, members_list)
    elif message.text.startswith("/listadmins"):
        admins_list = list_admins(chat_id)
        bot.send_message(chat_id, admins_list)
    elif message.text.startswith("/listmuted"):
        muted_list = list_muted(chat_id)
        bot.send_message(chat_id, muted_list)
    elif message.text.startswith("/listkicked"):
        kicked_list = list_kicked(chat_id)
        bot.send_message(chat_id, kicked_list)
    elif message.text.startswith("/listbanned"):
        banned_list = list_banned(chat_id)
        bot.send_message(chat_id, banned_list)
    elif message.text.startswith("/listrules"):
        rules_list = list_rules(chat_id)
        bot.send_message(chat_id, rules_list)

# Manejador para comandos de reglas
@bot.message_handler(commands=["addrule", "removerule"])
def handle_rule_commands(message):
    chat_id = message.chat.id
    args = message.text.split()[1:]
    if args:
        rule = " ".join(args)
        if message.text.startswith("/addrule"):
            add_rule(chat_id, rule)
            bot.send_message(chat_id, f"Se agregó la regla: {rule}")
        elif message.text.startswith("/removerule"):
            remove_rule(chat_id, rule)
            bot.send_message(chat_id, f"Se eliminó la regla: {rule}")
    else:
        bot.send_message(chat_id, "Por favor, introduce la regla.")

# Manejador para el comando /info
@bot.message_handler(commands=["info"])
def info_command(message):
    chat_id = message.chat.id
    group_info = get_group_info(chat_id)
    if group_info:
        bot.send_message(
            chat_id,
            f"Información del grupo:\n\n"
            f"Nombre: {group_info['name']}\n"
            f"Miembros: {len(group_info['members'])}\n"
            f"Administradores: {len(group_info['admins'])}\n"
            f"Silenciados: {len(group_info['muted'])}\n"
            f"Expulsados: {len(group_info['kicked'])}\n"
            f"Baneados: {len(group_info['banned'])}\n"
        )
    else:
        bot.send_message(chat_id, "No se encontró información del grupo.")

# Manejador para comandos de bienvenida y despedida
@bot.message_handler(commands=["welcome", "goodbye"])
def handle_welcome_goodbye(message):
    chat_id = message.chat.id
    args = message.text.split()[1:]
    if args:
        new_message = " ".join(args)
        if message.text.startswith("/welcome"):
            set_welcome_message(chat_id, new_message)
        elif message.text.startswith("/goodbye"):
            set_goodbye_message(chat_id, new_message)
    else:
        bot.send_message(chat_id, "Por favor, introduce el mensaje.")

# Manejador de nuevos miembros
@bot.message_handler(content_types=["new_chat_members"])
def handle_new_member(message):
    chat_id = message.chat.id
    group_info = get_group_info(chat_id)
    if group_info:
        for member in message.new_chat_members:
            bot.send_message(chat_id, group_info["welcome_message"], reply_to_message_id=message.message_id)

# Manejador de miembros que se van
@bot.message_handler(content_types=["left_chat_member"])
def handle_left_member(message):
    chat_id = message.chat.id
    group_info = get_group_info(chat_id)
    if group_info:
        left_member = message.left_chat_member.user.username
        if left_member:
            bot.send_message(chat_id, f"{left_member} {group_info['goodbye_message']}")

# Iniciar el bot
bot.polling(True)
