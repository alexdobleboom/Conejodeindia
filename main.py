import telebot
import time
import random

# Reemplaza con tu token de bot
TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q"

# Lista de canales (ID) y sus emojis de reacción
canales = {}

# Inicializar el bot
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Hola! Este bot reaccionará a publicaciones de canales seleccionados.\nUsa estos comandos:\n/addcanal <ID del canal> <emoji1> <emoji2> ...\n/delcanal <ID del canal>\n/like\n/comment <canal_id> <texto del comentario>\n/ayuda\n/version")

@bot.message_handler(commands=['addcanal'])
def add_canal(message):
    try:
        args = message.text.split()
        channel_id = int(args[1])
        emojis = args[2:]
        canales[channel_id] = emojis
        bot.reply_to(message, f"Canal {channel_id} agregado con éxito!")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['delcanal'])
def del_canal(message):
    try:
        args = message.text.split()
        channel_id = int(args[1])
        del canales[channel_id]
        bot.reply_to(message, f"Canal {channel_id} eliminado!")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(commands=['like'])
def like_post(message):
    """Función para dar like a la última publicación de un canal"""
    for channel_id, emojis in canales.items():
        try:
            # Obtener el ID del último mensaje del canal
            last_message_id = bot.get_updates(offset=-1, limit=1)[0].message.message_id

            # Seleccionar un emoji aleatorio para reaccionar
            emoji = emojis[random.randint(0, len(emojis) - 1)]

            # Reaccionar al último mensaje
            bot.send_message(chat_id=channel_id, text=emoji, reply_to_message_id=last_message_id)

            # Mostrar mensaje de éxito
            bot.send_message(chat_id=message.chat.id, text=f"Reacción enviada con éxito a {channel_id}!")
        except Exception as e:
            # Manejar errores
            bot.send_message(chat_id=message.chat.id, text=f"Error: {e}")

@bot.message_handler(commands=['comment'])
def comment_post(message):
    """Función para comentar en la última publicación de un canal"""
    try:
        args = message.text.split()
        channel_id = int(args[1])
        comment = " ".join(args[2:])

        # Obtener el ID del último mensaje del canal
        last_message_id = bot.get_updates(offset=-1, limit=1)[0].message.message_id

        # Comentar en la última publicación
        bot.send_message(chat_id=channel_id, text=comment, reply_to_message_id=last_message_id)

        # Mostrar mensaje de éxito
        bot.send_message(chat_id=message.chat.id, text=f"Comentario enviado con éxito a {channel_id}!")
    except Exception as e:
        # Manejar errores
        bot.send_message(chat_id=message.chat.id, text=f"Error: {e}")

@bot.message_handler(commands=['ayuda'])
def ayuda(message):
    bot.reply_to(message, "Comandos disponibles:\n/addcanal <ID del canal> <emoji1> <emoji2> ...: Agrega un canal.\n/delcanal <ID del canal>: Elimina un canal.\n/like: Reacciona a la última publicación de los canales.\n/comment <canal_id> <texto del comentario>: Comenta en la última publicación.\n/ayuda: Muestra esta ayuda.\n/version: Muestra la versión actual.")

@bot.message_handler(commands=['version'])
def version(message):
    bot.reply_to(message, "Versión 1.0")

# Ejecutar el bot
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        # Manejar errores de conexión
        print(f"Error: {e}")
        time.sleep(10)
