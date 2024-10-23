import telebot
from telebot import types
import time
import http.server
import socketserver
import threading

bot = telebot.TeleBot("7256076065:AAFmAQ3xpfwA-ZqvYIuiclHfa36YMrUIxyI")

# Inicialización de conjuntos y variables
users = set()
groups = set()
admins = ['7372906088', '6181692448', '5702506445']
welcome_messages = {}  # Diccionario para almacenar mensajes de bienvenida por grupo

def get_user_id(identifier, chat_id):
    """Obtiene el ID de usuario a partir del ID o username."""
    if identifier.isdigit():
        return int(identifier)  # Si es un ID, lo devuelve como entero
    else:
        try:
            username = identifier.lstrip('@')  # Elimina el '@' si está presente
            user = bot.get_chat_member(chat_id, username)
            return user.user.id
        except Exception as e:
            print(f"Error al obtener ID de usuario para {identifier}: {e}")
            return None

@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        users.add(message.from_user.id)
        bot.send_message(message.chat.id, "👋 ¡Hola! Soy tu asistente de grupo. Usa /help para ver los comandos disponibles.")

        keyboard = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="«BuzzWire Project»", url="https://t.me/BuzzWireProject")
        keyboard.add(url_button)
        bot.send_message(message.chat.id, "*¡No olvides unirte al canal para estar al tanto de los últimos proyectos! ♥️🙏🏻*", parse_mode='Markdown', reply_markup=keyboard)
    except Exception as e:
        print(f"Error en /start: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def new_chat_member(message):
    try:
        for new_member in message.new_chat_members:
            if new_member.id == bot.get_me().id:
                groups.add(message.chat.id)  # Registrar el ID del grupo
                bot.send_message(message.chat.id, "✅ ¡El bot ha sido agregado a este grupo! Estoy aquí para ayudarte.")
            else:
                # Enviar mensaje de bienvenida personalizado
                welcome_text = welcome_messages.get(message.chat.id, "¡Bienvenido al grupo, {name}!")
                name = new_member.first_name
                username = new_member.username if new_member.username else "sin_username"
                welcome_text = welcome_text.format(name=name, username=username)
                bot.send_message(message.chat.id, welcome_text)
    except Exception as e:
        print(f"Error en new_chat_member: {e}")

@bot.message_handler(commands=['welcome'])
def set_welcome_message(message):
    try:
        if str(message.from_user.id) in admins:
            new_message = ' '.join(message.text.split()[1:])
            welcome_messages[message.chat.id] = new_message if new_message else "¡Bienvenido al grupo, {name}! (@{username})"
            bot.send_message(message.chat.id, "✅ ¡El mensaje de bienvenida se ha actualizado exitosamente!")
        else:
            bot.send_message(message.chat.id, "🚫 Lo siento, no tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /welcome: {e}")

# Comandos abreviados
@bot.message_handler(commands=['w'])
def short_welcome(message):
    set_welcome_message(message)

@bot.message_handler(commands=['help'])
def help_command(message):
    try:
        help_text = (
            "🆘 **Comandos disponibles:**\n\n"
            "/start - Inicia el bot y recibe un saludo.\n"
            "/help - Muestra esta ayuda.\n"
            "/info - Muestra información del usuario.\n"
            "/kick [user_id/@username] - Expulsa a un usuario.\n"
            "/ban [user_id/@username] [razón] - Banea a un usuario.\n"
            "/unban [user_id/@username] - Desbanea a un usuario.\n"
            "/delete - Elimina el mensaje al que respondes.\n"
            "/mute [user_id/@username] [duración] - Silencia a un usuario.\n"
            "/unmute [user_id/@username] - Quita el silencio a un usuario.\n"
            "/promote [user_id/@username] - Promueve a un usuario a administrador.\n"
            "/demote [user_id/@username] - Degrada a un administrador.\n"
            "/warn [user_id/@username] [razón] - Advierte a un usuario.\n"
            "/welcome [mensaje] - Establece un mensaje de bienvenida.\n"
            "/w [mensaje] - Abreviación para establecer el mensaje de bienvenida."
        )
        bot.send_message(message.chat.id, help_text)
    except Exception as e:
        print(f"Error en /help: {e}")

@bot.message_handler(commands=['h'])
def short_help(message):
    help_command(message)

@bot.message_handler(commands=['info'])
def info_command(message):
    try:
        user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        user_id = user.id
        user_name = user.username or "No tiene un nombre de usuario"
        info_text = (
            f"🆔 **Información del usuario:**\n"
            f"ID: `{user_id}`\n"
            f"Nombre de usuario: `{user_name}`\n"
            f"Nombre: `{user.first_name}` {user.last_name if user.last_name else ''}\n"
            "🔍 ¡Si necesitas más ayuda, no dudes en preguntar!"
        )
        bot.send_message(message.chat.id, info_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error en /info: {e}")

@bot.message_handler(commands=['i'])
def short_info(message):
    info_command(message)

@bot.message_handler(commands=['delete'])
def delete_message(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                message_id = message.reply_to_message.message_id
                bot.delete_message(message.chat.id, message_id)
                bot.send_message(message.chat.id, "✅ ¡Mensaje eliminado con éxito!")
            except (IndexError, ValueError, AttributeError):
                bot.send_message(message.chat.id, "⚠️ Por favor, responde al mensaje que deseas eliminar.")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /delete: {e}")

@bot.message_handler(commands=['d'])
def short_delete(message):
    delete_message(message)

@bot.message_handler(commands=['mute'])
def mute_user(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                identifier = message.text.split()[1]
                user_id = get_user_id(identifier, message.chat.id)
                duration = int(message.text.split()[2]) if len(message.text.split()) > 2 else 60

                if user_id is None:
                    bot.send_message(message.chat.id, "⚠️ Usuario no encontrado.")
                    return

                target_chat_member = bot.get_chat_member(message.chat.id, user_id)  
                if target_chat_member.status in ['administrator', 'creator']:  
                    bot.send_message(message.chat.id, "🚫 No puedes silenciar a otros administradores.")  
                    return  
                
                bot.restrict_chat_member(message.chat.id, user_id, can_send_messages=False, until_date=time.time() + duration * 60)
                bot.send_message(message.chat.id, f"🔇 Usuario con ID `{user_id}` ha sido silenciado por {duration} minutos.")
            except (IndexError, ValueError):
                bot.send_message(message.chat.id, "⚠️ Por favor, proporciona un ID de usuario válido y una duración en minutos (opcional).")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /mute: {e}")

@bot.message_handler(commands=['u'])
def short_mute(message):
    mute_user(message)

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                identifier = message.text.split()[1]
                user_id = get_user_id(identifier, message.chat.id)

                if user_id is None:
                    bot.send_message(message.chat.id, "⚠️ Usuario no encontrado.")
                    return

                target_chat_member = bot.get_chat_member(message.chat.id, user_id)

                if target_chat_member.status in ['administrator', 'creator']:
                    bot.send_message(message.chat.id, "🚫 No puedes desilenciar a otros administradores.")
                    return
                
                bot.restrict_chat_member(message.chat.id, user_id, can_send_messages=True)
                bot.send_message(message.chat.id, f"🔊 Usuario con ID `{user_id}` ha sido desilenciado.")
            except (IndexError, ValueError):
                bot.send_message(message.chat.id, "⚠️ Por favor, proporciona un ID de usuario válido.")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /unmute: {e}")

@bot.message_handler(commands=['un'])
def short_unmute(message):
    unmute_user(message)

@bot.message_handler(commands=['kick'])
def kick_user(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                identifier = message.text.split()[1]
                user_id = get_user_id(identifier, message.chat.id)

                if user_id is None:
                    bot.send_message(message.chat.id, "⚠️ Usuario no encontrado.")
                    return

                target_chat_member = bot.get_chat_member(message.chat.id, user_id)

                if target_chat_member.status in ['administrator', 'creator']:  
                    bot.send_message(message.chat.id, "🚫 No puedes expulsar a otros administradores.")  
                    return  
                
                bot.kick_chat_member(message.chat.id, user_id)
                bot.send_message(message.chat.id, f"🚫 Usuario con ID `{user_id}` ha sido expulsado.")
            except (IndexError, ValueError):
                bot.send_message(message.chat.id, "⚠️ Por favor, proporciona un ID de usuario válido.")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /kick: {e}")

@bot.message_handler(commands=['k'])
def short_kick(message):
    kick_user(message)

@bot.message_handler(commands=['ban'])
def ban_user(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                identifier = message.text.split()[1]
                user_id = get_user_id(identifier, message.chat.id)
                reason = ' '.join(message.text.split()[2:]) if len(message.text.split()) > 2 else None

                if user_id is None:
                    bot.send_message(message.chat.id, "⚠️ Usuario no encontrado.")
                    return

                target_chat_member = bot.get_chat_member(message.chat.id, user_id)  
                if target_chat_member.status in ['administrator', 'creator']:  
                    bot.send_message(message.chat.id, "🚫 No puedes banear a otros administradores.")  
                    return  

                bot.kick_chat_member(message.chat.id, user_id)
                bot.ban_chat_member(message.chat.id, user_id)
                bot.send_message(message.chat.id, f"🚫 Usuario con ID `{user_id}` ha sido baneado por: {reason}" if reason else f"🚫 Usuario con ID `{user_id}` ha sido baneado.")
            except (IndexError, ValueError):
                bot.send_message(message.chat.id, "⚠️ Por favor, proporciona un ID de usuario válido.")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /ban: {e}")

@bot.message_handler(commands=['b'])
def short_ban(message):
    ban_user(message)

@bot.message_handler(commands=['unban'])
def unban_user(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                identifier = message.text.split()[1]
                user_id = get_user_id(identifier, message.chat.id)

                if user_id is None:
                    bot.send_message(message.chat.id, "⚠️ Usuario no encontrado.")
                    return

                bot.unban_chat_member(message.chat.id, user_id)
                bot.send_message(message.chat.id, f"🔓 Usuario con ID `{user_id}` ha sido desbaneado.")
            except (IndexError, ValueError):
                bot.send_message(message.chat.id, "⚠️ Por favor, proporciona un ID de usuario válido.")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /unban: {e}")

@bot.message_handler(commands=['ub'])
def short_unban(message):
    unban_user(message)

@bot.message_handler(commands=['promote'])
def promote_user(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                identifier = message.text.split()[1]
                user_id = get_user_id(identifier, message.chat.id)

                if user_id is None:
                    bot.send_message(message.chat.id, "⚠️ Usuario no encontrado.")
                    return

                bot.promote_chat_member(message.chat.id, user_id)
                bot.send_message(message.chat.id, f"✅ Usuario con ID `{user_id}` ha sido promovido a administrador.")
            except (IndexError, ValueError):
                bot.send_message(message.chat.id, "⚠️ Por favor, proporciona un ID de usuario válido.")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /promote: {e}")

@bot.message_handler(commands=['demote'])
def demote_user(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status in ['administrator', 'creator']:
            try:
                identifier = message.text.split()[1]
                user_id = get_user_id(identifier, message.chat.id)

                if user_id is None:
                    bot.send_message(message.chat.id, "⚠️ Usuario no encontrado.")
                    return

                bot.promote_chat_member(message.chat.id, user_id, can_change_info=False, can_post_messages=False, can_edit_messages=False, can_delete_messages=False, can_invite_users=False, can_restrict_members=False, can_pin_messages=False, can_promote_members=False)
                bot.send_message(message.chat.id, f"⚠️ Usuario con ID `{user_id}` ha sido degradado de administrador.")
            except (IndexError, ValueError):
                bot.send_message(message.chat.id, "⚠️ Por favor, proporciona un ID de usuario válido.")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /demote: {e}")

# ADMINS
@bot.message_handler(commands=['send'])
def send_message_to_all(message):
    try:
        if str(message.from_user.id) in admins:
            try:
                msg_text = ' '.join(message.text.split()[1:])
                for user_id in users:
                    try:
                        bot.send_message(user_id, msg_text)
                    except Exception as e:
                        print(f"Error enviando mensaje a {user_id}: {e}")
                bot.send_message(message.chat.id, "✅ ¡Mensaje enviado a todos los usuarios!")
            except Exception as e:
                print(f"Error en /send: {e}")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /send: {e}")

@bot.message_handler(commands=['s'])
def short_send(message):
    send_message_to_all(message)

@bot.message_handler(commands=['subs'])
def show_subs_count(message):
    try:
        if str(message.from_user.id) in admins:
            bot.send_message(message.chat.id, f"👥 Cantidad de usuarios: {len(users)}")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /subs: {e}")

@bot.message_handler(commands=['sc'])
def short_subs_count(message):
    show_subs_count(message)

@bot.message_handler(commands=['groups'])
def show_groups_count(message):
    try:
        if str(message.from_user.id) in admins:
            bot.send_message(message.chat.id, f"📊 Cantidad de grupos: {len(groups)}")
        else:
            bot.send_message(message.chat.id, "🚫 No tienes permiso para usar este comando.")
    except Exception as e:
        print(f"Error en /groups: {e}")

@bot.message_handler(commands=['gc'])
def short_groups_count(message):
    show_groups_count(message)

def run_server():
    try:
        PORT = 9000
        Handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Servidor corriendo en el puerto {PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error en el servidor: {e}")

# Inicia el bot
if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("Saliendo...")
    except Exception as e:
        print(f"Error en el bot: {e}")
