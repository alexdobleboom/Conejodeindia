import telebot
import os
import ffmpeg
import av
import datetime
import time
from telebot import types

API_TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q" # Reemplázalo con tu token de bot

bot = telebot.TeleBot(API_TOKEN)

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

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "¡Hola! 👋 Usa el comando /compress para comprimir un video o /picarvideo para dividir un video en partes.")

@bot.message_handler(commands=['compress'])
def compress(message):
    global original_video_path
    if message.reply_to_message and message.reply_to_message.video:
        if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
            original_video_path = bot.download_file(message.reply_to_message.video.file_id)
            original_size = os.path.getsize(original_video_path)

            keyboard = types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton("Alta Calidad", callback_data="alta"),
                        types.InlineKeyboardButton("Media Calidad", callback_data="media"),
                        types.InlineKeyboardButton("Baja Calidad", callback_data="baja")
                    ]
                ]
            )

            bot.reply_to(message, "Elige la calidad de compresión deseada:", reply_markup=keyboard)

        else:
            bot.reply_to(message, "El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.")
    else:
        bot.reply_to(message, "Responde a un video para comprimirlo.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    global original_video_path

    if call.data == "alta":
        compression_settings = {
            "resolution": "1920x1080",
            "crf": "20",
            "audio_bitrate": "128k",
            "fps": "24",
            "preset": "medium",
            "codec": "libx265"
        }
    elif call.data == "media":
        compression_settings = {
            "resolution": "1280x720",
            "crf": "23",
            "audio_bitrate": "96k",
            "fps": "24",
            "preset": "medium",
            "codec": "libx265"
        }
    elif call.data == "baja":
        compression_settings = {
            "resolution": "740x480",
            "crf": "28",
            "audio_bitrate": "60k",
            "fps": "24",
            "preset": "fast",
            "codec": "libx264"
        }
    else:
        bot.answer_callback_query(callback_query_id=call.id, text="Opción inválida.", show_alert=True)
        return

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Proceso iniciado. Espere a que termine.")
    compressed_video_path = f"{os.path.splitext(original_video_path)[0]}_compressed.mkv"

    # Iniciar la compresión en segundo plano con barra de progreso
    compress_video_async(call.message, original_video_path, compressed_video_path, compression_settings)

def compress_video_async(message, original_video_path, compressed_video_path, compression_settings):
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
        process = ffmpeg.run_async(output_video, capture_stderr=True, capture_stdout=True) # Iniciar la compresión en segundo plano

        while True:
            if process.poll() is not None: # Verificar si el proceso ha finalizado
                break

            # Obtener la salida de error y actualizar la barra de progreso
            stderr = process.stderr.read().decode('utf-8')
            progress_info = stderr.split('\n')[-2] # Obtener la última línea de información de progreso
            progress_percentage = float(progress_info.split(' ')[-2].strip('%')) # Extraer el porcentaje de progreso

            # Actualizar la barra de progreso
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=f"Proceso iniciado. Espere a que termine... {progress_percentage:.0f}%"
            )

            time.sleep(1) # Esperar 1 segundo antes de actualizar nuevamente

        # Proceso finalizado
        process.wait()
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

        bot.send_document(chat_id=message.chat.id, document=open(compressed_video_path, 'rb'), caption=description)

    except Exception as e:
        bot.send_message(chat_id=message.chat.id, text=f"Ocurrió un error en el video: {e}\n\nSalida de error de ffmpeg:\n{ffmpeg.stderr}")
    finally:
        if os.path.exists(original_video_path):
            os.remove(original_video_path)
        if os.path.exists(compressed_video_path):
            os.remove(compressed_video_path)

@bot.message_handler(commands=['picarvideo'])
def picar_video(message):
    global original_video_path
    if message.reply_to_message and message.reply_to_message.video:
        if message.reply_to_message.video.mime_type.split('/')[1] in ALLOWED_FORMATS:
            original_video_path = bot.download_file(message.reply_to_message.video.file_id)
            original_size = os.path.getsize(original_video_path)

            bot.reply_to(message, "Ingresa el tiempo en segundos para dividir el video (p.ej., 30 para dividir cada 30 segundos).")
            bot.register_next_step_handler(message, dividir_video)

        else:
            bot.reply_to(message, "El formato de video no es válido. Por favor, envía un video en uno de los siguientes formatos: MP4, MKV, AVI, MOV o WEBM.")
    else:
        bot.reply_to(message, "Responde a un video para dividirlo.")

def dividir_video(message):
    global original_video_path
    try:
        interval = int(message.text)
        if interval > 0:
            bot.reply_to(message, "Dividiendo el video... Espere.")

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

                bot.send_document(chat_id=message.chat.id, document=open(output_path, 'rb'), caption=f"Parte {i} del video.")

                start_time = end_time
                i += 1

            bot.reply_to(message, "Video dividido correctamente!")

        else:
            bot.reply_to(message, "El tiempo de división debe ser un número positivo.")
    except ValueError:
        bot.reply_to(message, "Por favor, ingresa un tiempo válido en segundos.")
    finally:
        if os.path.exists(original_video_path):
            os.remove(original_video_path)

bot.polling()
