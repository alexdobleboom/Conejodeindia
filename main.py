import pyrogram
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bs4 import BeautifulSoup
import requests
import re
import os
import logging
import time
import random
from typing import List, Dict, Tuple
import sqlite3

# Configura la salida del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Credenciales del bot (reemplaza los valores por los tuyos)
API_ID = 24288670
API_HASH = "81c58005802498656d6b689dae1edacc"
BOT_TOKEN = "7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q"

# Configuraciones del bot
MAX_SEARCH_RESULTS = 5 # Número máximo de resultados de búsqueda
DOWNLOAD_TIMEOUT = 120 # Tiempo máximo de espera para la descarga (en segundos)
RETRY_ATTEMPTS = 6 # Número de intentos de reintento en caso de error

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Crea la base de datos SQLite
database_path = "books.db"
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

# Crea la tabla de libros si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT,
        autor TEXT,
        año INTEGER,
        url TEXT,
        portada TEXT,
        tabla_de_contenido TEXT,
        fecha_descarga DATE,
        calificacion INTEGER
    )
''')

# Función para buscar libros en Google Books (mejorada)
def buscar_libros_google(titulo: str, autor: str = None, año: int = None, area: str = None) -> List[Dict]:
    """
    Busca libros en Google Books utilizando la API de búsqueda.

    Args:
        titulo: El título del libro a buscar.
        autor: El autor del libro (opcional).
        año: El año de publicación (opcional).
        area: El área científica o temática (opcional).

    Returns:
        Una lista de diccionarios con información sobre los libros encontrados.
        Cada diccionario contiene:
            - 'titulo': El título del libro.
            - 'autor': El autor del libro.
            - 'año': El año de publicación.
            - 'url': La URL del libro en Google Books.
            - 'descripcion': La descripción corta del libro.
            - 'portada': La URL de la portada del libro (opcional).
            - 'tabla_de_contenido': La tabla de contenido del libro (opcional).
    """
    try:
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            "q": f"{titulo}",
            "maxResults": MAX_SEARCH_RESULTS,
            "printType": "BOOKS",
        }
        if autor:
            params["q"] += f" +{autor}"
        if año:
            params["q"] += f" +{año}"
        if area:
            params["q"] += f" +{area}"

        response = requests.get(url, params=params)
        response.raise_for_status() # Lanza excepción si hay error HTTP

        data = response.json()
        items = data.get("items", [])
        resultados = []
        for item in items:
            volumen = item["volumeInfo"]
            resultados.append({
                "titulo": volumen.get("title", ""),
                "autor": ", ".join(volumen.get("authors", [])),
                "año": volumen.get("publishedDate", "").split("-")[0] if "-" in volumen.get("publishedDate", "") else None,
                "url": item["selfLink"],
                "descripcion": volumen.get("description", "")[:200],
                "portada": volumen.get("imageLinks", {}).get("thumbnail", None),
                "tabla_de_contenido": volumen.get("tableOfContents", None)
            })
        return resultados
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al buscar libros en Google Books: {e}")
        return []

# Función para buscar libros en Project Gutenberg
def buscar_libros_gutenberg(titulo: str, autor: str = None) -> List[Dict]:
    """
    Busca libros en Project Gutenberg.

    Args:
        titulo: El título del libro a buscar.
        autor: El autor del libro (opcional).

    Returns:
        Una lista de diccionarios con información sobre los libros encontrados.
        Cada diccionario contiene:
            - 'titulo': El título del libro.
            - 'autor': El autor del libro.
            - 'url': La URL del libro en Project Gutenberg.
    """
    try:
        url = "https://www.gutenberg.org/ebooks/search/?query="
        if titulo:
            url += titulo
        if autor:
            url += f"&author={autor}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        resultados = []
        links = soup.find_all("a", href=re.compile(r"/ebooks/.*"))
        for link in links:
            resultados.append({
                "titulo": link.text.strip(),
                "autor": link.get("title", "").replace("by ", "").strip(),
                "url": "https://www.gutenberg.org" + link["href"],
            })
        return resultados
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al buscar libros en Project Gutenberg: {e}")
        return []

# Función para buscar libros en Open Library
def buscar_libros_open_library(titulo: str, autor: str = None) -> List[Dict]:
    """
    Busca libros en Open Library.

    Args:
        titulo: El título del libro a buscar.
        autor: El autor del libro (opcional).

    Returns:
        Una lista de diccionarios con información sobre los libros encontrados.
        Cada diccionario contiene:
            - 'titulo': El título del libro.
            - 'autor': El autor del libro.
            - 'url': La URL del libro en Open Library.
    """
    try:
        url = "https://openlibrary.org/search.json"
        params = {"q": titulo}
        if autor:
            params["q"] += f" +{autor}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        resultados = []
        for doc in data.get("docs", []):
            resultados.append({
                "titulo": doc.get("title", ""),
                "autor": ", ".join(doc.get("author_name", [])),
                "url": f"https://openlibrary.org{doc.get('key', '')}",
            })
        return resultados
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al buscar libros en Open Library: {e}")
        return []

# Función para buscar libros en Internet Archive
def buscar_libros_internet_archive(titulo: str, autor: str = None) -> List[Dict]:
    """
    Busca libros en Internet Archive.

    Args:
        titulo: El título del libro a buscar.
        autor: El autor del libro (opcional).

    Returns:
        Una lista de diccionarios con información sobre los libros encontrados.
        Cada diccionario contiene:
            - 'titulo': El título del libro.
            - 'autor': El autor del libro.
            - 'url': La URL del libro en Internet Archive.
    """
    try:
        url = "https://archive.org/search.php"
        params = {"query": titulo}
        if autor:
            params["query"] += f" +{autor}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        resultados = []
        links = soup.find_all("a", href=re.compile(r"/details/.*"))
        for link in links:
            resultados.append({
                "titulo": link.text.strip(),
                "autor": link.get("title", "").replace("by ", "").strip(),
                "url": "https://archive.org" + link["href"],
            })
        return resultados
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al buscar libros en Internet Archive: {e}")
        return []

# Función para descargar un libro desde Google Books, Project Gutenberg o Internet Archive (mejorada)
def descargar_libro(url: str, nombre_archivo: str) -> Tuple[str, bool]:
    """
    Descarga un libro en formato PDF desde Google Books, Project Gutenberg o Internet Archive.

    Args:
        url: La URL del libro.
        nombre_archivo: El nombre del archivo para guardar el libro.

    Returns:
        Una tupla con:
            - El nombre del archivo descargado (o None si hubo un error).
            - Un valor booleano que indica si la descarga fue exitosa.
    """
    try:
        # Verifica si la URL es de Google Books, Project Gutenberg o Internet Archive
        if "books.google.com" in url:
            # Descarga desde Google Books
            return descargar_libro_google(url, nombre_archivo)
        elif "gutenberg.org" in url:
            # Descarga desde Project Gutenberg
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            enlace_descarga = soup.find("a", href=re.compile(r"/files/.*\.pdf"))
            if enlace_descarga:
                enlace_descarga = "https://www.gutenberg.org" + enlace_descarga["href"]
                response = requests.get(enlace_descarga, stream=True)
                response.raise_for_status()
                with open(nombre_archivo, "wb") as archivo:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        archivo.write(chunk)
                logger.info(f"Libro descargado correctamente: {nombre_archivo}")
                return nombre_archivo, True
            else:
                logger.error(f"No se encontró un enlace de descarga PDF para el libro: {url}")
                return None, False
        elif "archive.org" in url:
            # Descarga desde Internet Archive
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            enlace_descarga = soup.find("a", href=re.compile(r"/download/.*\.pdf"))
            if enlace_descarga:
                enlace_descarga = "https://archive.org" + enlace_descarga["href"]
                response = requests.get(enlace_descarga, stream=True)
                response.raise_for_status()
                with open(nombre_archivo, "wb") as archivo:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        archivo.write(chunk)
                logger.info(f"Libro descargado correctamente: {nombre_archivo}")
                return nombre_archivo, True
            else:
                logger.error(f"No se encontró un enlace de descarga PDF para el libro: {url}")
                return None, False
        elif "openlibrary.org" in url:
            # Descarga desde Open Library (necesita web scraping)
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            enlace_descarga = soup.find("a", href=re.compile(r"/works/OL[0-9]+/editions"))
            if enlace_descarga:
                enlace_descarga = "https://openlibrary.org" + enlace_descarga["href"]
                response = requests.get(enlace_descarga)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                enlace_descarga = soup.find("a", href=re.compile(r".*pdf"))
                if enlace_descarga:
                    enlace_descarga = "https://openlibrary.org" + enlace_descarga["href"]
                    response = requests.get(enlace_descarga, stream=True)
                    response.raise_for_status()
                    with open(nombre_archivo, "wb") as archivo:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            archivo.write(chunk)
                    logger.info(f"Libro descargado correctamente: {nombre_archivo}")
                    return nombre_archivo, True
                else:
                    logger.error(f"No se encontró un enlace de descarga PDF para el libro: {url}")
                    return None, False
            else:
                logger.error(f"No se encontró un enlace de descarga PDF para el libro: {url}")
                return None, False
        else:
            logger.error(f"La URL no es válida: {url}")
            return None, False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al descargar el libro: {e}")
        return None, False

# Función para generar un teclado inline
def generar_teclado_inline(libros: List[Dict]) -> InlineKeyboardMarkup:
    """
    Genera un teclado inline con botones para descargar los libros encontrados.

    Args:
        libros: Una lista de diccionarios con información sobre los libros.

    Returns:
        Un teclado inline con botones para descargar cada libro.
    """
    keyboard = []
    for libro in libros:
        keyboard.append(
            [InlineKeyboardButton(text=f"{libro['titulo']} ({libro['autor']})", callback_data=f"download_{libro['url']}")]
        )
    return InlineKeyboardMarkup(keyboard)

# Función para mostrar el menú principal
async def mostrar_menu_principal(client: Client, message: Message):
    """
    Muestra el menú principal del bot con botones para buscar libros, obtener ayuda y más.

    Args:
        client: El cliente de Telegram.
        message: El mensaje del usuario.
    """
    keyboard = [
        [InlineKeyboardButton(text="Buscar libro", callback_data="buscar_libro")],
        [InlineKeyboardButton(text="Mis libros", callback_data="mis_libros")],
        [InlineKeyboardButton(text="Ayuda", callback_data="ayuda")],
        [InlineKeyboardButton(text="Acerca del bot", callback_data="acerca_del_bot")],
    ]
    await message.reply_text(
        "Bienvenido al bot de búsqueda de libros! ¿Qué quieres hacer?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# Función para mostrar ayuda
async def mostrar_ayuda(client: Client, message: Message):
    """
    Muestra un mensaje de ayuda con instrucciones sobre cómo usar el bot.

    Args:
        client: El cliente de Telegram.
        message: El mensaje del usuario.
    """
    await message.reply_text(
        "Soy un bot que te ayuda a buscar y descargar libros en formato PDF.\n"
        "Para buscar un libro, escribe su título, autor (opcional), año (opcional) y área (opcional).\n"
        "Por ejemplo: \"El Hobbit J.R.R. Tolkien 1937 fantasía\"\n\n"
        "También puedes usar los botones del menú principal para navegar por las opciones.\n"
        "Puedes solicitar información adicional sobre el libro, como la portada o la tabla de contenido, una vez que haya encontrado los resultados de la búsqueda.\n"
        "Puedes acceder a la lista de tus libros descargados con el botón 'Mis libros'."
    )

# Función para mostrar información acerca del bot
async def mostrar_acerca_del_bot(client: Client, message: Message):
    """
    Muestra información sobre el bot, su creador y sus características.

    Args:
        client: El cliente de Telegram.
        message: El mensaje del usuario.
    """
    await message.reply_text(
        "Este bot fue creado para ayudarte a encontrar y descargar libros en formato PDF de forma rápida y fácil.\n"
        "Puedes buscar libros por título, autor, año y área.\n"
        "Si tienes algún problema o sugerencia, puedes contactar al desarrollador.\n\n"
        "¡Disfruta de la lectura!"
    )

# Función para manejar la búsqueda de libros
async def manejar_busqueda_libro(client: Client, query: Message):
    """
    Maneja la solicitud de búsqueda de libros del usuario.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        texto = query.text.strip()
        partes = texto.split()
        titulo = partes[0]
        autor = partes[1] if len(partes) > 1 else None
        año = int(partes[2]) if len(partes) > 2 and partes[2].isdigit() else None
        area = " ".join(partes[3:]) if len(partes) > 3 else None

        # Busca en Google Books
        libros_google = buscar_libros_google(titulo, autor, año, area)
        # Busca en Project Gutenberg (solo si no hay resultados en Google Books)
        if not libros_google:
            libros_gutenberg = buscar_libros_gutenberg(titulo, autor)
            libros = libros_gutenberg
        else:
            libros = libros_google

        if libros:
            await query.reply_text(
                "He encontrado algunos libros que podrían interesarte! ¿Cuál te gustaría descargar?",
                reply_markup=generar_teclado_inline(libros)
            )
        else:
            await query.reply_text("No encontré ningún libro con ese título. Intenta de nuevo con más información.")
    except Exception as e:
        logger.error(f"Error al buscar el libro: {e}")
        await query.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Función para manejar la descarga del libro
async def manejar_descarga_libro(client: Client, query: Message):
    """
    Maneja la solicitud de descarga de un libro del usuario.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        data = query.data
        if data.startswith("download_"):
            url = data[len("download_"):]
            nombre_archivo = url.split("/")[-1]
            archivo_descargado, exito = descargar_libro(url, nombre_archivo)
            if exito:
                # Guarda la información del libro en la base de datos
                cursor.execute(
                    "INSERT INTO books (titulo, autor, año, url, portada, tabla_de_contenido, fecha_descarga) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        libro.get("titulo", None),
                        libro.get("autor", None),
                        libro.get("año", None),
                        libro.get("url", None),
                        libro.get("portada", None),
                        libro.get("tabla_de_contenido", None),
                        time.strftime("%Y-%m-%d"),
                    ),
                )
                conn.commit()
                await query.message.reply_document(archivo_descargado)
                os.remove(archivo_descargado) # Eliminar el archivo temporal
                await query.answer("¡Libro descargado exitosamente!")
            else:
                await query.answer("Hubo un error al descargar el libro. Intenta de nuevo más tarde.")
        else:
            await query.answer("Opción no válida.")
    except Exception as e:
        logger.error(f"Error al descargar el libro: {e}")
        await query.message.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Función para mostrar la portada del libro
async def mostrar_portada(client: Client, query: Message):
    """
    Muestra la portada del libro seleccionado.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        data = query.data
        if data.startswith("portada_"):
            url = data[len("portada_"):]
            libro = next((libro for libro in query.message.reply_markup.inline_keyboard[0] if libro.callback_data == f"download_{url}"), None)
            if libro:
                portada = libro.get("portada", None)
                if portada:
                    await query.message.reply_photo(portada)
                    await query.answer(f"Portada de {libro['titulo']}")
                else:
                    await query.answer("No se pudo encontrar la portada del libro.")
            else:
                await query.answer("No se pudo encontrar la portada del libro.")
        else:
            await query.answer("Opción no válida.")
    except Exception as e:
        logger.error(f"Error al mostrar la portada: {e}")
        await query.message.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Función para mostrar la tabla de contenido del libro
async def mostrar_tabla_de_contenido(client: Client, query: Message):
    """
    Muestra la tabla de contenido del libro seleccionado.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        data = query.data
        if data.startswith("tabla_de_contenido_"):
            url = data[len("tabla_de_contenido_"):]
            libro = next((libro for libro in query.message.reply_markup.inline_keyboard[0] if libro.callback_data == f"download_{url}"), None)
            if libro:
                tabla_de_contenido = libro.get("tabla_de_contenido", None)
                if tabla_de_contenido:
                    await query.message.reply_text(f"Tabla de contenido de {libro['titulo']}:")
                    for entrada in tabla_de_contenido:
                        await query.message.reply_text(f"- {entrada.get('title', '')}")
                else:
                    await query.answer("No se pudo encontrar la tabla de contenido del libro.")
            else:
                await query.answer("No se pudo encontrar la tabla de contenido del libro.")
        else:
            await query.answer("Opción no válida.")
    except Exception as e:
        logger.error(f"Error al mostrar la tabla de contenido: {e}")
        await query.message.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Función para mostrar la lista de libros descargados
async def mostrar_mis_libros(client: Client, query: Message):
    """
    Muestra la lista de libros descargados por el usuario.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        cursor.execute("SELECT * FROM books")
        libros = cursor.fetchall()
        if libros:
            keyboard = []
            for libro in libros:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text=f"{libro[1]} ({libro[2]})",
                            callback_data=f"ver_libro_{libro[0]}",
                        ),
                        InlineKeyboardButton(
                            text="Calificar",
                            callback_data=f"calificar_libro_{libro[0]}",
                        ),
                    ]
                )
            await query.message.reply_text(
                "Tus libros descargados:", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.message.reply_text("No has descargado ningún libro aún.")
    except Exception as e:
        logger.error(f"Error al mostrar la lista de libros descargados: {e}")
        await query.message.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Función para mostrar la información de un libro descargado
async def ver_libro(client: Client, query: Message):
    """
    Muestra la información de un libro descargado.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        data = query.data
        if data.startswith("ver_libro_"):
            id_libro = int(data[len("ver_libro_"):])
            cursor.execute("SELECT * FROM books WHERE id = ?", (id_libro,))
            libro = cursor.fetchone()
            if libro:
                await query.message.reply_text(
                    f"**Título:** {libro[1]}\n"
                    f"**Autor:** {libro[2]}\n"
                    f"**Año:** {libro[3]}\n"
                    f"**URL:** {libro[4]}\n"
                    f"**Fecha de descarga:** {libro[7]}\n"
                    f"**Calificación:** {libro[8] if libro[8] is not None else 'Sin calificar'}"
                )
            else:
                await query.answer("No se pudo encontrar el libro.")
        else:
            await query.answer("Opción no válida.")
    except Exception as e:
        logger.error(f"Error al mostrar la información del libro: {e}")
        await query.message.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Función para calificar un libro descargado
async def calificar_libro(client: Client, query: Message):
    """
    Permite al usuario calificar un libro descargado.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        data = query.data
        if data.startswith("calificar_libro_"):
            id_libro = int(data[len("calificar_libro_"):])
            await query.message.reply_text(
                "Califica el libro del 1 al 5:", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="1", callback_data=f"calificacion_{id_libro}_1"),
                            InlineKeyboardButton(text="2", callback_data=f"calificacion_{id_libro}_2"),
                            InlineKeyboardButton(text="3", callback_data=f"calificacion_{id_libro}_3"),
                        ],
                        [
                            InlineKeyboardButton(text="4", callback_data=f"calificacion_{id_libro}_4"),
                            InlineKeyboardButton(text="5", callback_data=f"calificacion_{id_libro}_5"),
                        ],
                    ]
                )
            )
        else:
            await query.answer("Opción no válida.")
    except Exception as e:
        logger.error(f"Error al calificar el libro: {e}")
        await query.message.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Función para guardar la calificación del libro
async def guardar_calificacion(client: Client, query: Message):
    """
    Guarda la calificación del libro en la base de datos.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    try:
        data = query.data
        if data.startswith("calificacion_"):
            partes = data.split("_")
            id_libro = int(partes[1])
            calificacion = int(partes[2])
            cursor.execute(
                "UPDATE books SET calificacion = ? WHERE id = ?", (calificacion, id_libro)
            )
            conn.commit()
            await query.answer("¡Calificación guardada!")
        else:
            await query.answer("Opción no válida.")
    except Exception as e:
        logger.error(f"Error al guardar la calificación: {e}")
        await query.message.reply_text("Ups! Parece que hubo un error. Intenta de nuevo más tarde.")

# Manejador de inicio
@app.on_message(filters.command(["start", "inicio"]))
async def start(client: Client, message: Message):
    """
    Maneja el comando `/start` o `/inicio`, mostrando el menú principal.

    Args:
        client: El cliente de Telegram.
        message: El mensaje del usuario.
    """
    await mostrar_menu_principal(client, message)

# Manejador de texto (búsqueda de libro)
@app.on_message(filters.text)
async def buscar_libro_handler(client: Client, message: Message):
    """
    Maneja el mensaje de texto del usuario, buscando un libro.

    Args:
        client: El cliente de Telegram.
        message: El mensaje del usuario.
    """
    await manejar_busqueda_libro(client, message)

# Manejador de consultas de callback
@app.on_callback_query()
async def callback_query_handler(client: Client, query: Message):
    """
    Maneja las consultas de callback del usuario, procesando botones del teclado inline.

    Args:
        client: El cliente de Telegram.
        query: El mensaje del usuario.
    """
    if query.data == "buscar_libro":
        await query.message.reply_text("Escribe el título del libro que deseas buscar (puedes incluir autor, año y área).")
    elif query.data == "ayuda":
        await mostrar_ayuda(client, query.message)
    elif query.data == "acerca_del_bot":
        await mostrar_acerca_del_bot(client, query.message)
    elif query.data == "mis_libros":
        await mostrar_mis_libros(client, query)
    elif query.data.startswith("download_"):
        await manejar_descarga_libro(client, query)
    elif query.data.startswith("portada_"):
        await mostrar_portada(client, query)
    elif query.data.startswith("tabla_de_contenido_"):
        await mostrar_tabla_de_contenido(client, query)
    elif query.data.startswith("ver_libro_"):
        await ver_libro(client, query)
    elif query.data.startswith("calificar_libro_"):
        await calificar_libro(client, query)
    elif query.data.startswith("calificacion_"):
        await guardar_calificacion(client, query)
    else:
        await query.answer("Opción no válida.")

# Ejecución del bot
app.run()
