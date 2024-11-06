import os
from docx import Document
from docx.shared import Inches, Pt
from pypdf import PdfMerger, PdfReader
from telethon import TelegramClient, events
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser, PeerChannel, InputPeerChat
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
import time
import random
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.messages import SendMessageRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser, PeerChannel, InputPeerChat
import sys
import configparser
import re
from io import BytesIO
from pypdf import PdfReader, PdfWriter

# -------------------------------------------------------------------------------------------------------------------- #
# Credenciales del Bot (No se recomienda guardarlas en el script principal)
# -------------------------------------------------------------------------------------------------------------------- #
api_id = "YOUR_API_ID" # Reemplaza con tu API ID
api_hash = "YOUR_API_HASH" # Reemplaza con tu API HASH
bot_token = "YOUR_BOT_TOKEN" # Reemplaza con tu Bot Token
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# Iniciamos el Bot
# -------------------------------------------------------------------------------------------------------------------- #
client = TelegramClient('session_name', api_id, api_hash)
client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Ingresa el código: '))
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# Variables Globales
# -------------------------------------------------------------------------------------------------------------------- #
documents = []
current_file_type = None
customization_options = {
    "nombre_archivo": "archivo_combinado",
    "formato": "pdf",
    "tamaño_fuente": 12,
}
# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# Funciones para el Manejo de Archivos
# -------------------------------------------------------------------------------------------------------------------- #
def leer_pdf(archivo_pdf):
    """Lee un archivo PDF y devuelve su contenido como texto."""
    with open(archivo_pdf, 'rb') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        content = ''
        for page in document.get_pages():
            content += PDFPageContent.create_content(page).get_text()
    return content

def combinar_archivos(archivos, formato_salida, nombre_salida, opciones):
    """Combina archivos en el formato de salida especificado."""
    if formato_salida == 'pdf':
        merger = PdfMerger()
        for archivo in archivos:
            merger.append(archivo)
        merger.write(f"{nombre_salida}.pdf")
        merger.close()

    elif formato_salida == 'word':
        doc = Document()
        for archivo in archivos:
            if archivo.endswith('.docx') or archivo.endswith('.doc'):
                doc_temp = Document(archivo)
                for parrafo in doc_temp.paragraphs:
                    doc.add_paragraph(parrafo.text)
            elif archivo.endswith('.txt'):
                with open(archivo, 'r') as f:
                    doc.add_paragraph(f.read())

        # Ajusta tamaño de fuente (opcional)
        if 'tamaño_fuente' in opciones:
            for parrafo in doc.paragraphs:
                parrafo.style.font.size = Pt(opciones['tamaño_fuente'])

        doc.save(f"{nombre_salida}.docx")

def convertir_pdf_a_word(archivo_pdf, nombre_salida, tamaño_fuente):
    """Convierte un archivo PDF a Word."""
    reader = PdfReader(archivo_pdf)
    num_pages = len(reader.pages)
    doc = Document()
    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text = page.extract_text()
        doc.add_paragraph(text)

    # Ajusta tamaño de fuente (opcional)
    if tamaño_fuente:
        for parrafo in doc.paragraphs:
            parrafo.style.font.size = Pt(tamaño_fuente)

    doc.save(f"{nombre_salida}.docx")

def convertir_word_a_pdf(archivo_word, nombre_salida):
    """Convierte un archivo Word a PDF."""
    doc = Document(archivo_word)
    output_pdf = BytesIO()
    doc.save(output_pdf)
    output_pdf.seek(0)
    writer = PdfWriter()
    writer.add_page(PdfReader(output_pdf).pages[0])
    with open(f"{nombre_salida}.pdf", "wb") as f:
        writer.write(f)

# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------------------------------------------------------------------------------------- #
# Funciones para la Interacción con Telegram
# -------------------------------------------------------------------------------------------------------------------- #
@client.on(events.NewMessage(pattern='/start'))
async def handler(event):
    await event.respond(
        f"¡Hola! 👋 Soy un bot que puede combinar archivos PDF, Word y de texto.\n\n"
        f"¡Usa los siguientes comandos para interactuar conmigo!\n"
        f"• `/start`: Iniciar el bot.\n"
        f"• `/help`: Mostrar la ayuda.\n"
        f"• `/enviar`: Enviar archivos para combinar.",
        buttons=[
            [Button.inline("Enviar Archivo 📁", data="enviar_archivo"), Button.inline("Personalizar ⚙️", data="personalizar")]
        ]
    )

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    await event.respond(
        f"Comandos disponibles:\n"
        f"• `/start`: Iniciar el bot.\n"
        f"• `/help`: Mostrar la ayuda.\n"
        f"• `/enviar`: Enviar archivos para combinar.",
        buttons=[
            [Button.inline("Enviar Archivo 📁", data="enviar_archivo"), Button.inline("Personalizar ⚙️", data="personalizar")]
        ]
    )

@client.on(events.NewMessage(pattern='/enviar'))
async def enviar_archivo(event):
    global documents, current_file_type # Declara las variables como globales aquí
    await event.respond("¡Envíame un documento o texto! 📝")
    @client.on(events.NewMessage(incoming=True, from_users=event.sender_id))
    async def process_document(event):
        try:
            if event.message.media:
                # Obtener el archivo
                file_info = await client.download_media(event.message.media, file=f"{event.message.media.document.id}.{event.message.media.document.mime_type.split('/')[1]}")

                # Determinar el tipo de archivo
                if file_info.lower().endswith(('.pdf', '.docx', '.doc', '.txt')):
                    current_file_type = file_info.lower().split('.')[-1]
                    documents.append(file_info)
                    await event.respond(f"¡Archivo {file_info} recibido! 🎉 ¿Deseas agregar más archivos del mismo tipo?", buttons=[
                        [Button.inline("Sí 👍", data="agregar_mas"), Button.inline("No 👎", data="generar_archivo")]
                    ])
                else:
                    await event.respond("¡Solo se aceptan archivos PDF, Word, TXT o texto! ⛔")
                    await event.respond("¿Deseas enviar otro archivo?", buttons=[
                        [Button.inline("Sí 👍", data="enviar_archivo"), Button.inline("No 👎", data="cancelar")]
                    ])

            elif event.message.text:
                documents.append(event.message.text)
                current_file_type = 'text'
                await event.respond("¿Deseas agregar más archivos o textos?", buttons=[
                    [Button.inline("Sí 👍", data="agregar_mas"), Button.inline("No 👎", data="generar_archivo")]
                ])
        except Exception as e:
            print(f"Error al procesar el archivo: {e}")
            await event.respond(f"¡Ups! 😨 Hubo un error al procesar el archivo. Intenta de nuevo.")

@client.on(events.CallbackQuery(data='agregar_mas'))
async def agregar_mas_archivos(event):
    global current_file_type
    if current_file_type:
        await event.respond(f"¡Envíame otro archivo de tipo {current_file_type}! 📂")
    else:
        await event.respond("¡Primero debes enviar un archivo o texto! 📝")

@client.on(events.CallbackQuery(data='generar_archivo'))
async def generar_archivo(event):
    global documents, current_file_type

    if current_file_type:
        await event.respond("¡Elige el formato para el archivo combinado! 🎨", buttons=[
            [Button.inline("PDF 📄", data="pdf"), Button.inline("Word 📑", data="word")],
            [Button.inline("Cambiar Formato 🔁", data="cambiar_formato")]
        ])
    else:
        await event.respond("¡Primero debes enviar un archivo o texto! 📝")

@client.on(events.CallbackQuery(data='pdf'))
async def generar_pdf(event):
    global documents, customization_options
    await event.respond("¡Procesando tu archivo! ⏳")
    if documents:
        try:
            # Combinar archivos PDF
            if current_file_type == 'pdf':
                output_pdf = BytesIO()
                merger = PdfMerger()
                for archivo in documents:
                    merger.append(archivo)
                merger.write(output_pdf)
                merger.close()

                # Enviar el archivo PDF
                await client.send_file(event.message.chat_id, output_pdf, filename=f"{customization_options['nombre_archivo']}.pdf", caption="¡Tu archivo combinado está listo! 🎉")

            # Convertir archivos Word a PDF y combinar
            elif current_file_type == 'docx' or current_file_type == 'doc':
                output_pdf = BytesIO()
                merger = PdfMerger()
                for archivo in documents:
                    convertir_word_a_pdf(archivo, customization_options['nombre_archivo'])
                    merger.append(f"{customization_options['nombre_archivo']}.pdf")
                merger.write(output_pdf)
                merger.close()
                # Borrar archivo temporal
                os.remove(f"{customization_options['nombre_archivo']}.pdf")

                # Enviar el archivo PDF
                await client.send_file(event.message.chat_id, output_pdf, filename=f"{customization_options['nombre_archivo']}.pdf", caption="¡Tu archivo combinado está listo! 🎉")

            # Combinar archivos de texto
            elif current_file_type == 'text':
                output_pdf = BytesIO()
                merger = PdfMerger()
                for archivo in documents:
                    merger.append(archivo)
                merger.write(output_pdf)
                merger.close()

                # Enviar el archivo PDF
                await client.send_file(event.message.chat_id, output_pdf, filename=f"{customization_options['nombre_archivo']}.pdf", caption="¡Tu archivo combinado está listo! 🎉")

            # Limpiar la lista de documentos
            documents.clear()
            current_file_type = None
        except Exception as e:
            print(f"Error al generar el archivo: {e}")
            await event.respond(f"¡Ups! 😨 Hubo un error al generar el archivo. Intenta de nuevo.")
    else:
        await event.respond("¡No se han enviado archivos aún! 😕")

@client.on(events.CallbackQuery(data='word'))
async def generar_word(event):
    global documents, customization_options
    await event.respond("¡Procesando tu archivo! ⏳")
    if documents:
        try:
            # Combinar archivos Word
            if current_file_type == 'docx' or current_file_type == 'doc':
                doc = Document()
                for archivo in documents:
                    doc_temp = Document(archivo)
                    for parrafo in doc_temp.paragraphs:
                        doc.add_paragraph(parrafo.text)
                    # Ajusta tamaño de fuente (opcional)
                    if 'tamaño_fuente' in customization_options:
                        for parrafo in doc.paragraphs:
                            parrafo.style.font.size = Pt(customization_options['tamaño_fuente'])
                output_word = BytesIO()
                doc.save(output_word)
                await client.send_file(event.message.chat_id, output_word, filename=f"{customization_options['nombre_archivo']}.docx", caption="¡Tu archivo combinado está listo! 🎉")

            # Convertir archivos PDF a Word y combinar
            elif current_file_type == 'pdf':
                doc = Document()
                for archivo in documents:
                    convertir_pdf_a_word(archivo, customization_options['nombre_archivo'], customization_options['tamaño_fuente'])
                    doc_temp = Document(f"{customization_options['nombre_archivo']}.docx")
                    for parrafo in doc_temp.paragraphs:
                        doc.add_paragraph(parrafo.text)
                    # Borrar archivo temporal
                    os.remove(f"{customization_options['nombre_archivo']}.docx")

                output_word = BytesIO()
                doc.save(output_word)
                await client.send_file(event.message.chat_id, output_word, filename=f"{customization_options['nombre_archivo']}.docx", caption="¡Tu archivo combinado está listo! 🎉")

            # Combinar archivos de texto
            elif current_file_type == 'text':
                doc = Document()
                for archivo in documents:
                    doc.add_paragraph(archivo)
                    # Ajusta tamaño de fuente (opcional)
                    if 'tamaño_fuente' in customization_options:
                        for parrafo in doc.paragraphs:
                            parrafo.style.font.size = Pt(customization_options['tamaño_fuente'])
                output_word = BytesIO()
                doc.save(output_word)
                await client.send_file(event.message.chat_id, output_word, filename=f"{customization_options['nombre_archivo']}.docx", caption="¡Tu archivo combinado está listo! 🎉")

            # Limpiar la lista de documentos
            documents.clear()
            current_file_type = None
        except Exception as e:
            print(f"Error al generar el archivo: {e}")
            await event.respond(f"¡Ups! 😨 Hubo un error al generar el archivo. Intenta de nuevo.")
    else:
        await event.respond("¡No se han enviado archivos aún! 😕")

@client.on(events.CallbackQuery(data='cambiar_formato'))
async def cambiar_formato(event):
    global documents, current_file_type, customization_options

    if current_file_type == 'pdf':
        customization_options['formato'] = 'word'
        await event.respond("¡El formato se cambiará a Word! 📑")
        await generar_archivo(event)
    elif current_file_type == 'docx' or current_file_type == 'doc':
        customization_options['formato'] = 'pdf'
        await event.respond("¡El formato se cambiará a PDF! 📄")
        await generar_archivo(event)
    else:
        await event.respond("¡No se ha seleccionado ningún archivo para cambiar el formato! 😕")

@client.on(events.CallbackQuery(data='personalizar'))
async def handle_personalization(event):
    global customization_options
    await event.respond("¡Elige una opción para personalizar tu archivo combinado! 🎨", buttons=[
        [Button.inline("Nombre del Archivo 📝", data="nombre_archivo"), Button.inline("Tamaño de Fuente 📏", data="tamaño_fuente")],
        [Button.inline("Regresar 🔙", data="regresar")]
    ])

@client.on(events.CallbackQuery(data='nombre_archivo'))
async def set_file_name(event):
    global customization_options
    await event.respond("¡Ingresa el nombre que quieres para tu archivo! ✍️")
    @client.on(events.NewMessage(incoming=True, from_users=event.sender_id))
    async def set_file_name_input(event):
        customization_options['nombre_archivo'] = event.message.text
        await event.respond(f"¡Nombre del archivo actualizado a: {customization_options['nombre_archivo']}! ✅")
        await handle_personalization(event)

@client.on(events.CallbackQuery(data='tamaño_fuente'))
async def set_font_size(event):
    global customization_options
    await event.respond("¡Ingresa el tamaño de fuente que quieres (número entero)! 🔢")
    @client.on(events.NewMessage(incoming=True, from_users=event.sender_id))
    async def set_font_size_input(event):
        try:
            font_size = int(event.message.text)
            customization_options['tamaño_fuente'] = font_size
            await event.respond(f"¡Tamaño de fuente actualizado a: {customization_options['tamaño_fuente']}! ✅")
            await handle_personalization(event)
        except ValueError:
            await event.respond("¡Por favor, ingresa un número entero válido! ⛔")

@client.on(events.CallbackQuery(data='regresar'))
async def regresar_al_inicio(event):
    await event.respond("¡Regresando al menú principal! 🔙")
    await handler(event)

@client.on(events.CallbackQuery(data='cancelar'))
async def cancelar_proceso(event):
    global documents, current_file_type
    documents.clear()
    current_file_type = None
    await event.respond("¡Proceso cancelado! 🚫")
    await handler(event)

# Función para leer un archivo PDF
def leer_pdf(archivo_pdf):
    """Lee un archivo PDF y devuelve su contenido como texto."""
    with open(archivo_pdf, 'rb') as f:
        parser = PDFParser(f)
        document = PDFDocument(parser)
        content = ''
        for page in document.get_pages():
            content += PDFPageContent.create_content(page).get_text()
    return content

print("Bot iniciado...")
client.run_until_disconnected()
