import os
import time
import asyncio
import ffmpeg
import av
import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import PeerIdInvalid

API_ID = 24288670 # Reemplázalo con tu API_ID
API_HASH = "81c58005802498656d6b689dae1edacc" # Reemplázalo con tu API_HASH
BOT_TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q" # Reemplázalo con tu token de bot

# Configuraciones del bot
DEFAULT_COMPRESSION_SETTINGS = {
    "resolution": "640x480",
    "crf": "32",
    "audio_bitrate": "60k",
    "fps": "18",
    "preset": "veryfast",
    "codec": "libx264"
}
ALLOWED_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"]

app = Client("compress_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("𝑪𝑨𝑵𝑨𝑳 𝑶𝑭𝑰𝑪𝑰𝑨𝑳 💬", url="https://t.me/ZonaFreeCanal")],
            [InlineKeyboardButton("𝑷𝒓𝒐𝒈𝒓𝒂𝒎𝒂𝒅𝒐𝒓 👨‍💻", url="t.me/TheDemonsuprem")]
        ]
    )
    await app.send_message(chat_id=message.chat.id, text="¡👋 𝑩𝒊𝒆𝒏𝒗𝒆𝒏𝒊𝒅𝒐𝒔 𝒂 𝑨𝒓𝒎𝒂𝒅𝒊𝒍𝒍𝒐 𝑪𝒐𝒎𝒑𝒓𝒆𝒔𝒔 📚!. Qué deseas hacer❓", reply_markup=keyboard)

@app.on_message(filters.command("compress"))
async def compress_video(client, message: Message):
    global original_video_path
    if message.reply_to_message and message.reply_to_message.video:
        # Verificar que el video esté en los formatos permitidos
        if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
            original_video_path = await app.download_media(message.reply_to_message.video)
            original_size = os.path.getsize(original_video_path)

            # Preguntar al usuario qué calidad quiere
            keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Alta Calidad", callback_data="alta")],
                    [InlineKeyboardButton("Media Calidad", callback_data="media")],
                    [InlineKeyboardButton("Baja Calidad", callback_data="baja")],
                    [InlineKeyboardButton("Por Defecto", callback_data="default")]
                ]
            )
            await app.send_message(chat_id=message.chat.id, text="Elige la calidad de compresión deseada:", reply_markup=keyboard)

        else:
            await app.send_message(chat_id=message.chat.id, text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.")
    else:
        await app.send_message(chat_id=message.chat.id, text="Responde a un video para comprimirlo.")

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    global original_video_path

    if callback_query.data == "alta":
        compression_settings = {
            "resolution": "1920x1080",
            "crf": "20", # Valor más bajo para mayor calidad
            "audio_bitrate": "128k",
            "fps": "24",
            "preset": "medium", # Balance entre calidad y velocidad
            "codec": "libx265"
        }
    elif callback_query.data == "media":
        compression_settings = {
            "resolution": "1280x720",
            "crf": "23",
            "audio_bitrate": "96k",
            "fps": "24",
            "preset": "medium",
            "codec": "libx265"
        }
    elif callback_query.data == "baja":
        compression_settings = {
            "resolution": "740x480",
            "crf": "28",
            "audio_bitrate": "60k",
            "fps": "24",
            "preset": "fast", # Prioriza velocidad sobre calidad
            "codec": "libx264"
        }
    elif callback_query.data == "default":
        compression_settings = DEFAULT_COMPRESSION_SETTINGS
    else:
        await callback_query.answer("Opción inválida.", show_alert=True)
        return

    await callback_query.message.edit_text("Proceso iniciado. Espere a que termine.")
    compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"

    # Iniciar la compresión en segundo plano
    asyncio.create_task(compress_video_async(client, callback_query.message, original_video_path, compressed_video_path, compression_settings))

async def compress_video_async(client, message, original_video_path, compressed_video_path, compression_settings):
    try:
        start_time = datetime.datetime.now()
        input_video = ffmpeg.input(original_video_path)
        output_video = (
            input_video
            .output(
                compressed_video_path,
                **compression_settings
            )
            .overwrite_output()
        )
        process = (
            output_video
            .run_async(capture_stderr=True, capture_stdout=True) # Iniciar la compresión en segundo plano
        )

        while True:
            if process.poll() is not None: # Verificar si el proceso ha finalizado
                break

            # Obtener la salida de error y actualizar la barra de progreso
            stderr = process.stderr.read().decode('utf-8')
            progress_info = stderr.split('\n')[-2] # Obtener la última línea de información de progreso
            try:
                progress_percentage = float(progress_info.split(' ')[-2].strip('%')) # Extraer el porcentaje de progreso
            except:
                progress_percentage = 0.0

            # Actualizar la barra de progreso
            await message.edit_text(
                text=f"Proceso iniciado. Espere a que termine... {progress_percentage:.0f}%"
            )

            await asyncio.sleep(1) # Esperar 1 segundo antes de actualizar nuevamente

        # Proceso finalizado
        await process.wait()
        compressed_size = os.path.getsize(compressed_video_path)
        duration = av.open(compressed_video_path).duration
        duration_str = str(datetime.timedelta(seconds=duration))
        processing_time = datetime.datetime.now() - start_time
        processing_time_str = str(processing_time).split('.')[0]

        description = (
            f"Proceso finalizado.\n"
            f"Peso original: {original_size // (1024 * 1024)} MB\n"
            f"Peso procesado: {compressed_size // (1024 * 1024)} MB\n"
            f"Tiempo de procesamiento: {processing_time_str}\n"
            f"Tiempo del video: {duration_str}\n"
            f"¡Que lo disfrute!"
        )

        await client.send_document(chat_id=message.chat.id, document=compressed_video_path, caption=description)

    except Exception as e:
        await client.send_message(chat_id=message.chat.id, text=f"Ocurrió un error en el video: {e}\n\nSalida de error de ffmpeg:\n{ffmpeg.stderr}")
    finally:
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(compressed_video_path):
            os.remove(compressed_video_path)

@app.on_message(filters.command("picarvideo"))
async def picar_video(client, message: Message):
    global original_video_path
    if message.reply_to_message and message.reply_to_message.video:
        if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
            original_video_path = await client.download_media(message.reply_to_message.video)
            original_size = os.path.getsize(original_video_path)

            await client.send_message(chat_id=message.chat.id, text="Ingresa el tiempo en segundos para dividir el video (p.ej., 30 para dividir cada 30 segundos).")
            try:
                interval = int((await client.ask(message.chat.id, timeout=30)).text)
            except PeerIdInvalid:
                await client.send_message(chat_id=message.chat.id, text="No se recibió ningún tiempo de división. Intenta de nuevo.")
            except ValueError:
                await client.send_message(chat_id=message.chat.id, text="Por favor, ingresa un tiempo válido en segundos.")
            else:
                await client.send_message(chat_id=message.chat.id, text="Dividiendo el video... Espere.")

                # Obtener información del video
                video_info = ffmpeg.probe(original_video_path)
                duration = float(video_info['format']['duration'])

                # Dividir el video
                i = 1
                start_time = 0
                while start_time < duration:
                    end_time = min(start_time + interval, duration)
                    output_path = f"{os.path.splitext(original_video_path)[0]}_parte_{i}.mkv"
                    input_video = ffmpeg.input(original_video_path, ss=start_time, to=end_time)
                    output_video = (
                        input_video
                        .output(output_path)
                        .overwrite_output()
                    )
                    ffmpeg.run(output_video)

                    await client.send_document(chat_id=message.chat.id, document=output_path, caption=f"Parte {i} del video.")

                    start_time = end_time
                    i += 1

                await client.send_message(chat_id=message.chat.id, text="Video dividido correctamente!")

        else:
            await client.send_message(chat_id=message.chat.id, text="El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.")
    else:
        await client.send_message(chat_id=message.chat.id, text="Responde a un video para dividirlo.")


app.run()  
