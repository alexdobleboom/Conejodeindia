import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
    ChatPermissions,
    User,
)
from pyrogram.errors import (
    PeerFloodError,
    UserPrivacyRestrictedError,
    FloodWait,
    Unauthorized,
    MessageNotModified,
)
from pyrogram.enums import ChatType
from moviepy.editor import VideoFileClip
from PIL import Image

logging.basicConfig(level=logging.INFO)

# Credenciales del Bot (No se recomienda guardarlas en el script principal)
api_id = 24288670 # Reemplaza con tu API ID
api_hash = "81c58005802498656d6b689dae1edacc" # Reemplaza con tu API HASH
bot_token = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q" # Reemplaza con tu Bot Token
# -------------------------------------------------------------------------------------------------------------------- #

# Variables globales
MAX_VIDEO_SIZE = 1024 * 1024 * 1024 # Límite de tamaño de video en bytes (1 GB)
DEFAULT_QUALITY = "resolution=640x480 crf=32 audio_bitrate=60k fps=18 preset=ultrafast codec=libx265"
USERS = []
ADMINS = []
SUPER_ADMINS = []
START_TIME = int(time.time())
CHANNEL_USERNAME = "@AnimalProjets" # Reemplaza con el nombre de usuario de tu canal
ADMIN_USERNAME = "@TheDemonsuprem" # Reemplaza con el nombre de usuario del administrador
THUMBNAIL_SIZE = (90, 90) # Tamaño de la miniatura (opcional)

# Crea una instancia del Bot
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Define las funciones de ayuda


def is_admin(chat_id, user_id):
    admin_list = app.get_chat_members(chat_id, filter="administrators")
    for member in admin_list:
        if member.user.id == user_id:
            return True
    return False


def is_super_admin(user_id):
    return user_id in SUPER_ADMINS


async def send_to_super_admin(message: Message, reason: str):
    for super_admin in SUPER_ADMINS:
        try:
            await app.send_message(
                chat_id=super_admin,
                text=f"**Alerta:**\n{reason}\n\n**Usuario:** @{message.from_user.username}\n**Mensaje:** {message.text}",
            )
        except (PeerFloodError, UserPrivacyRestrictedError):
            logging.info(
                f"No se pudo enviar alerta al administrador supremo {super_admin}."
            )


# Define los comandos
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    if message.from_user.id in USERS:
        await message.reply_text(
            f"¡Hola! 👋 Soy un bot que puede convertir videos. 🎬\n"
            f"¡Envíame un video y lo convertiré a la calidad por defecto!\n\n"
            f"Puedes usar los siguientes comandos para obtener más información:\n"
            f"• `/help`: Mostrar la ayuda.\n"
            f"• `/about`: Mostrar información sobre el bot.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Ir al canal 📣", url=f"https://t.me/{CHANNEL_USERNAME}"
                        ),
                        InlineKeyboardButton(
                            "Contactar al administrador 👨‍💼",
                            url=f"https://t.me/{ADMIN_USERNAME}",
                        ),
                    ]
                ]
            ),
        )
    else:
        await send_to_super_admin(
            message, f"**Alerta:** Usuario no autorizado intentó acceder al bot."
        )
        await message.reply_text(f"¡Lo siento, no estás autorizado para usar este bot! 🚫")


@app.on_message(filters.command("help"))
async def help(client: Client, message: Message):
    if message.from_user.id in USERS:
        await message.reply_text(
            f"**Comandos disponibles:**\n"
            f"• `/start`: Iniciar el bot.\n"
            f"• `/help`: Mostrar la ayuda.\n"
            f"• `/about`: Mostrar información sobre el bot.\n"
            f"• `/calidad`: Cambiar la calidad de conversión por defecto.\n"
            f"• `/listuser`: Ver la lista de usuarios (solo administradores).\n"
            f"• `/listadmin`: Ver la lista de administradores (solo administradores supremos).\n"
            f"**Comandos de administración (solo administradores o administradores supremos):**\n"
            f"• `/add`: Agregar un usuario al bot.\n"
            f"• `/ban`: Banear un usuario del bot.\n"
            f"• `/addadmin`: Otorgar permisos de administrador a un usuario.\n"
            f"• `/banadmin`: Retirar permisos de administrador a un usuario.\n"
            f"**Comandos de administrador supremo (solo administrador supremo):**\n"
            f"• `/info`: Enviar un mensaje a todos los usuarios del bot.\n"
            f"• `/max`: Cambiar el límite de tamaño de video.\n"
        )
    else:
        await send_to_super_admin(
            message,
            f"**Alerta:** Usuario no autorizado intentó usar un comando de administrador.",
        )
        await message.reply_text(
            f"¡Lo siento, no estás autorizado para usar este comando! 🚫"
        )


@app.on_message(filters.command("about"))
async def about(client: Client, message: Message):
    if message.from_user.id in USERS:
        uptime_sec = int(time.time() - START_TIME)
        uptime = time.strftime("%H:%M:%S", time.gmtime(uptime_sec))
        await message.reply_text(
            f"**Información del bot:**\n"
            f"• Fecha de creación: {time.strftime('%Y-%m-%d', time.gmtime(START_TIME))}\n"
            f"• Hora de creación: {time.strftime('%H:%M:%S', time.gmtime(START_TIME))}\n"
            f"• Tiempo de actividad: {uptime}\n"
            f"• Desarrollador: [Nombre del desarrollador]\n"
            f"• Versión: 1.0\n"
        )
    else:
        await send_to_super_admin(
            message,
            f"**Alerta:** Usuario no autorizado intentó acceder al bot.",
        )
        await message.reply_text(
            f"¡Lo siento, no estás autorizado para usar este bot! 🚫"
        )


@app.on_message(filters.command("add") & filters.user(ADMINS + SUPER_ADMINS))
async def add(client: Client, message: Message):
    if len(message.command) == 2:
        user = message.text.split(" ")[1]
        if user.startswith("@"):
            try:
                user_id = await app.get_users(user)
                user_id = user_id.id
                if user_id not in USERS:
                    USERS.append(user_id)
                    await message.reply_text(
                        f"¡Usuario @{user} agregado correctamente! ✅"
                    )
                else:
                    await message.reply_text(
                        f"¡El usuario @{user} ya está en la lista! 🤔"
                    )
            except Unauthorized:
                await message.reply_text("¡No tengo acceso a este usuario! 🚫")
        else:
            await message.reply_text(
                "¡Por favor, ingresa un usuario válido con el formato @username! ✍️"
            )
    else:
        await message.reply_text("¡Comando inválido! ❌")


@app.on_message(filters.command("ban") & filters.user(ADMINS + SUPER_ADMINS))
async def ban(client: Client, message: Message):
    if len(message.command) == 2:
        user = message.text.split(" ")[1]
        if user.startswith("@"):
            try:
                user_id = await app.get_users(user)
                user_id = user_id.id
                if user_id in USERS:
                    USERS.remove(user_id)
                    await message.reply_text(
                        f"¡Usuario @{user} baneado correctamente! 🚫"
                    )
                else:
                    await message.reply_text(
                        f"¡El usuario @{user} no está en la lista! 🤔"
                    )
            except Unauthorized:
                await message.reply_text("¡No tengo acceso a este usuario! 🚫")
        else:
            await message.reply_text(
                "¡Por favor, ingresa un usuario válido con el formato @username! ✍️"
            )
    else:
        await message.reply_text("¡Comando inválido! ❌")


@app.on_message(filters.command("addadmin") & filters.user(ADMINS + SUPER_ADMINS))
async def addadmin(client: Client, message: Message):
    if len(message.command) == 2:
        user = message.text.split(" ")[1]
        if user.startswith("@"):
            try:
                user_id = await app.get_users(user)
                user_id = user_id.id
                if user_id not in ADMINS:
                    ADMINS.append(user_id)
                    await message.reply_text(
                        f"¡Administrador @{user} agregado correctamente! ✅"
                    )
                else:
                    await message.reply_text(
                        f"¡El administrador @{user} ya está en la lista! 🤔"
                    )
            except Unauthorized:
                await message.reply_text("¡No tengo acceso a este usuario! 🚫")
        else:
            await message.reply_text(
                "¡Por favor, ingresa un usuario válido con el formato @username! ✍️"
            )
    else:
        await message.reply_text("¡Comando inválido! ❌")


@app.on_message(filters.command("banadmin") & filters.user(SUPER_ADMINS))
async def banadmin(client: Client, message: Message):
    if len(message.command) == 2:
        user = message.text.split(" ")[1]
        if user.startswith("@"):
            try:
                user_id = await app.get_users(user)
                user_id = user_id.id
                if user_id in ADMINS:
                    ADMINS.remove(user_id)
                    await message.reply_text(
                        f"¡Administrador @{user} baneado correctamente! 🚫"
                    )
                else:
                    await message.reply_text(
                        f"¡El administrador @{user} no está en la lista! 🤔"
                    )
            except Unauthorized:
                await message.reply_text("¡No tengo acceso a este usuario! 🚫")
        else:
            await message.reply_text(
                "¡Por favor, ingresa un usuario válido con el formato @username! ✍️"
            )
    else:
        await message.reply_text("¡Comando inválido! ❌")


@app.on_message(filters.command("info") & filters.user(SUPER_ADMINS))
async def info(client: Client, message: Message):
    if len(message.command) > 1:
        text = message.text.split(" ", 1)[1]
        for user_id in USERS:
            try:
                await app.send_message(chat_id=user_id, text=text)
            except (PeerFloodError, UserPrivacyRestrictedError, MessageNotModified):
                await message.reply_text(
                    "¡Error al enviar el mensaje al usuario! ❌ ¡Intenta de nuevo más tarde!"
                )
        await message.reply_text("¡Mensaje enviado correctamente! ✅")
    else:
        await message.reply_text(
            "¡Comando inválido! ❌ ¡Ingresa un mensaje después del comando /info!"
        )


@app.on_message(filters.command("max") & filters.user(SUPER_ADMINS))
async def max(client: Client, message: Message):
    global MAX_VIDEO_SIZE
    if len(message.command) == 2:
        try:
            size = int(message.text.split(" ")[1])
            if size > 0:
                MAX_VIDEO_SIZE = size * 1024 * 1024
                await message.reply_text(
                    f"¡Límite de tamaño de video actualizado a {size} MB! ✅"
                )
            else:
                await message.reply_text("¡Ingresa un tamaño válido! ✍️")
        except ValueError:
            await message.reply_text("¡Ingresa un tamaño válido! ✍️")
    else:
        await message.reply_text("¡Comando inválido! ❌")


@app.on_message(filters.command("calidad"))
async def calidad(client: Client, message: Message):
    global DEFAULT_QUALITY
    if message.from_user.id in USERS:
        if len(message.command) == 2:
            new_quality = message.text.split(" ")[1]
            DEFAULT_QUALITY = new_quality
            await message.reply_text(
                f"¡Calidad de conversión por defecto actualizada a: {DEFAULT_QUALITY}! ✅"
            )
        else:
            await message.reply_text(
                "¡Comando inválido! ❌ ¡Ingresa la calidad después del comando /calidad!"
            )
    else:
        await send_to_super_admin(
            message,
            f"**Alerta:** Usuario no autorizado intentó usar un comando de administrador.",
        )
        await message.reply_text(
            f"¡Lo siento, no estás autorizado para usar este comando! 🚫"
        )


@app.on_message(filters.command("listuser") & filters.user(ADMINS + SUPER_ADMINS))
async def listuser(client: Client, message: Message):
    if USERS:
        user_list = ", ".join(
            [f"@{await app.get_users(user_id).username}" for user_id in USERS]
        )
        await message.reply_text(f"**Lista de usuarios:**\n{user_list}")
    else:
        await message.reply_text("¡La lista de usuarios está vacía! 🚫")


@app.on_message(filters.command("listadmin") & filters.user(SUPER_ADMINS))
async def listadmin(client: Client, message: Message):
    if ADMINS:
        admin_list = ", ".join(
            [f"@{await app.get_users(admin_id).username}" for admin_id in ADMINS]
        )
        await message.reply_text(f"**Lista de administradores:**\n{admin_list}")
    else:
        await message.reply_text("¡La lista de administradores está vacía! 🚫")


# Función para convertir un video
def convert_video(video_path, output_path, thumbnail_path=None):
    if thumbnail_path:
        cmd = f'ffmpeg -i "{video_path}" -i "{thumbnail_path}" -map 0 -c:v libx265 -preset ultrafast -crf 23 -c:a aac -b:a 128k -map 0 -movflags faststart -map 1 -c:v copy -disposition:v 0 -y "{output_path}"'
    else:
        cmd = f'ffmpeg -i "{video_path}" -map 0 -c:v libx265 -preset ultrafast -crf 23 -c:a aac -b:a 128k -map 0 -movflags faststart -y "{output_path}"'
    os.system(cmd)


async def handle_video(client: Client, message: Message, thumbnail_path=None):
    if message.video.file_size > MAX_VIDEO_SIZE:
        await message.reply_text(
            f"¡El tamaño del video excede el límite permitido de {MAX_VIDEO_SIZE // (1024 * 1024)} MB! ❌"
        )
        return

    try:
        start_time = time.time()
        new_video = await app.download_media(
            message,
            file_name=f"{message.video.file_name.replace('.mp4', '')}_converted.mp4",
            progress=lambda _, downloaded, total: app.send_message(
                message.chat.id,
                f"Convirtiendo... {round(downloaded / total * 100)}%",
            ),
        )

        # Convertir video usando el hilo
        with ThreadPoolExecutor() as executor:
            executor.submit(
                convert_video,
                new_video,
                new_video.replace(".mp4", "_converted.mp4"),
                thumbnail_path,
            )

        end_time = time.time()
        conversion_time = end_time - start_time
        conversion_time_formatted = time.strftime(
            "%H:%M:%S", time.gmtime(conversion_time)
        )
        video_duration = time.strftime("%H:%M:%S", time.gmtime(message.video.duration))

        # Envíar el video convertido
        await app.send_video(
            chat_id=message.chat.id,
            video=f"{new_video.replace('.mp4', '')}_converted.mp4",
            caption=f"꧁༺ 𝑭𝒊𝒏𝒂𝒍𝒊𝒛𝒂𝒅𝒐 ༻꧂\n"
            f"✮𝑵𝒐𝒎𝒃𝒓𝒆 𝒅𝒆𝒍 𝒗𝒊𝒅𝒆𝒐 {message.video.file_name}\n"
            f"×͡×𝑷𝒆𝒔𝒐 𝑶𝒓𝒊𝒈𝒊𝒏𝒂𝒍: {message.video.file_size // (1024 * 1024)} MB\n"
            f"×͜×𝑷𝒆𝒔𝒐 𝑷𝒓𝒐𝒄𝒆𝒔𝒂𝒅𝒐: {os.path.getsize(new_video.replace('.mp4', '_converted.mp4')) // (1024 * 1024)} MB\n"
            f"𖤍𝑻𝒊𝒆𝒎𝒑𝒐 𝒅𝒆 𝑷𝒓𝒐𝒄𝒆𝒔𝒂𝒎𝒊𝒆𝒏𝒕𝒐: {conversion_time_formatted}\n"
            f"✧𝑻𝒊𝒆𝒎𝒑𝒐 𝒅𝒆𝒍 𝑽𝒊𝒅𝒆𝒐: {video_duration}\n"
            f"♣¡𝑸𝒖𝒆 𝒍𝒐 𝒅𝒊𝒔𝒇𝒓𝒖𝒕𝒆𝒔 ✨",
        )

        # Eliminar el video original y el convertido
        os.remove(new_video)
        os.remove(f"{new_video.replace('.mp4', '')}_converted.mp4")

    except Exception as e:
        print(f"Error al convertir el video: {e}")
        await message.reply_text(
            f"¡Ups! 😨 Hubo un error al convertir el video. Intenta de nuevo."
        )


@app.on_message(filters.video & filters.user(USERS) & ~filters.group)
async def handle_video_private(client: Client, message: Message):
    await handle_video(client, message)


@app.on_message(filters.photo & filters.video & filters.user(USERS) & ~filters.group)
async def handle_video_thumbnail_private(client: Client, message: Message):
    try:
        # Descarga la imagen y el video
        thumbnail = await app.download_media(message.photo)
        await handle_video(client, message, thumbnail)
    except Exception as e:
        print(f"Error al convertir el video: {e}")
        await message.reply_text(
            f"¡Ups! 😨 Hubo un error al convertir el video. Intenta de nuevo."
        )


@app.on_message(filters.video & filters.user(USERS) & filters.group)
async def handle_video_group(client: Client, message: Message):
    if message.video.file_size > MAX_VIDEO_SIZE:
        await message.reply_text(
            f"¡El tamaño del video excede el límite permitido de {MAX_VIDEO_SIZE // (1024 * 1024)} MB! ❌"
        )
        return

    # Verifica si el bot es administrador en el grupo
    if not is_admin(message.chat.id, client.me.id):
        await message.reply_text(
            "¡Necesito ser administrador en este grupo para poder convertir videos! 🚫"
        )
        return

    await handle_video(client, message)


@app.on_message(filters.photo & filters.video & filters.user(USERS) & filters.group)
async def handle_video_thumbnail_group(client: Client, message: Message):
    if message.video.file_size > MAX_VIDEO_SIZE:
        await message.reply_text(
            f"¡El tamaño del video excede el límite permitido de {MAX_VIDEO_SIZE // (1024 * 1024)} MB! ❌"
        )
        return

    # Verifica si el bot es administrador en el grupo
    if not is_admin(message.chat.id, client.me.id):
        await message.reply_text(
            "¡Necesito ser administrador en este grupo para poder convertir videos! 🚫"
        )
        return

    try:
        # Descarga la imagen y el video
        thumbnail = await app.download_media(message.photo)
        await handle_video(client, message, thumbnail)
    except Exception as e:
        print(f"Error al convertir el video: {e}")
        await message.reply_text(
            f"¡Ups! 😨 Hubo un error al convertir el video. Intenta de nuevo."
        )


# Define los administradores y administradores supremos
SUPER_ADMINS = [7551486576] # Reemplaza con tu ID de usuario
ADMINS = [7551486576] # Reemplaza con las IDs de usuario de los administradores

print("Bot iniciado...")
app.run()
