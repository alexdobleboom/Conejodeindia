from pyrogram import Client, filters
import requests
from bs4 import BeautifulSoup
import os
from tqdm import tqdm  # Importar la barra de progreso

# Reemplaza 'YOUR_API_ID', 'YOUR_API_HASH' y 'YOUR_BOT_TOKEN' con los datos de tu bot
api_id = '24288670'
api_hash = '81c58005802498656d6b689dae1edacc'
bot_token = '7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q'

app = Client("mediafire_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
download_tasks = {}  # Almacenar las tareas de descarga

@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply_text("¡Hola! Soy un bot que puede descargar archivos desde enlaces directos de MediaFire. Usa el comando /mediafire seguido del enlace para comenzar. Ejemplo: /mediafire https://www.mediafire.com/file/ejemplo")

@app.on_message(filters.command("mediafire"))
def download_mediafire(client, message):
    try:
        url = message.text.split()[1]
        if not url.startswith("https://www.mediafire.com/"):
            message.reply_text("Por favor, proporciona un enlace válido de MediaFire.")
            return

        message.reply_text("Obteniendo el enlace de descarga directa...")
        direct_link = get_direct_link(url)
        if direct_link:
            message.reply_text("Descargando el archivo...")
            download_tasks[message.chat.id] = True  # Marcar tarea como activa
            file_path = download_file(direct_link, message)
            if file_path:
                message.reply_text("Enviando el archivo...")
                message.reply_document(document=file_path)
                os.remove(file_path)  # Eliminar el archivo después de enviarlo
                message.reply_text("Archivo enviado con éxito.")
            else:
                message.reply_text("No se pudo descargar el archivo.")
            download_tasks.pop(message.chat.id, None)  # Marcar tarea como inactiva
        else:
            message.reply_text("No se pudo obtener el enlace de descarga directa.")
    except IndexError:
        message.reply_text("Por favor, proporciona un enlace de MediaFire después del comando.")
    except Exception as e:
        message.reply_text(f"Ocurrió un error: {e}")

@app.on_message(filters.command("ls"))
def list_files(client, message):
    files = os.listdir()
    if files:
        message.reply_text("Archivos almacenados:\n" + "\n".join(files))
    else:
        message.reply_text("No hay archivos almacenados.")

@app.on_message(filters.command("rm"))
def remove_files(client, message):
    files = os.listdir()
    if files:
        for file in files:
            os.remove(file)
        message.reply_text("Todos los archivos han sido eliminados.")
    else:
        message.reply_text("No hay archivos para eliminar.")

@app.on_message(filters.command("cancel"))
def cancel_download(client, message):
    if download_tasks.get(message.chat.id):
        download_tasks[message.chat.id] = False
        message.reply_text("Descarga cancelada.")
    else:
        message.reply_text("No hay descargas en curso para cancelar.")

def get_direct_link(mediafire_url):
    try:
        response = requests.get(mediafire_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        download_button = soup.find('a', {'id': 'downloadButton'})
        if download_button:
            return download_button['href']
    except requests.RequestException as e:
        print(f"Error al obtener el enlace directo: {e}")
    return None

def download_file(url, message):
    local_filename = url.split('/')[-1]
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(local_filename, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=local_filename) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if not download_tasks.get(message.chat.id):
                        return None  # Cancelar descarga
                    f.write(chunk)
                    pbar.update(len(chunk))
        return local_filename
    except requests.RequestException as e:
        print(f"Error al descargar el archivo: {e}")
    return None

app.run()
