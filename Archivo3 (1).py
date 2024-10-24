import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import re
from datetime import datetime, timedelta

# Variables
api_id = '24288670'  # Reemplaza con tu API ID
api_hash = '81c58005802498656d6b689dae1edacc'  # Reemplaza con tu API Hash
bot_token = '7720485529:AAHEQX7edaOEjqgm4lbw-au4RbwdWWy25HM'  # Reemplaza con tu token del bot

admins = list(map(int, "7551486576,1155063846,1622367515".split(',')))
tempadmins = []
notas = {}  # Notas individuales por usuario
pausados = {}
usuarios = admins + tempadmins  # Agrupando usuarios permitidos

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def parse_time(time_str):
    days = hours = minutes = 0
    if 'd' in time_str:
        days = int(re.search(r"(\d+)d", time_str).group(1))
    if 'h' in time_str:
        hours = int(re.search(r"(\d+)h", time_str).group(1))
    if 'm' in time_str:
        minutes = int(re.search(r"(\d+)m", time_str).group(1))
    return timedelta(days=days, hours=hours, minutes=minutes)

async def start(client, message):
    await message.reply('Funcionando')

async def add_vip(client, message):
    parts = message.text.split(' ', 1)
    if len(parts) == 2:
        note, time_str = parts[1].split('/')
        expire_time = datetime.now() + parse_time(time_str)
        if message.from_user.id not in notas:
            notas[message.from_user.id] = {}
        notas[message.from_user.id][note] = expire_time
        await message.reply(f'Usuario "{note}" añadido como VIP por {time_str}.')

async def ver_vip(client, message):
    if pausados:
        await message.reply('Tiempo pausado para todos los usuarios.')
    elif message.from_user.id in notas and notas[message.from_user.id]:
        notas_list = '\n'.join([
            f'{note} {((exp - datetime.now()).days)}dias:{((exp - datetime.now()).seconds // 3600)}hrs:{(((exp - datetime.now()).seconds // 60) % 60)}min'
            for note, exp in notas[message.from_user.id].items()
        ])
        await message.reply(f'Usuarios VIPs:\n{notas_list}')
    else:
        await message.reply('No hay VIPs.')

async def rem_vip(client, message):
    parts = message.text.split(' ', 1)
    if len(parts) == 2:
        note = parts[1]
        if message.from_user.id in notas and note in notas[message.from_user.id]:
            del notas[message.from_user.id][note]
            await message.reply(f'VIP de "{note}" eliminado.')
        else:
            await message.reply(f'"{note}" no es VIP.')

async def add_admin(client, message):
    if message.from_user.id in admins:
        new_user_id = int(message.text.split()[1])
        tempadmins.append(new_user_id)
        usuarios.append(new_user_id)
        if new_user_id not in notas:
            notas[new_user_id] = {}
        await message.reply(f"Usuario {new_user_id} añadido como admin temporalmente.")
    else:
        await message.reply(f"Usted no puede añadir admins.")

async def rem_admin(client, message):
    if message.from_user.id in admins:
        rem_user_id = int(message.text.split()[1])
        if rem_user_id in tempadmins:
            tempadmins.remove(rem_user_id)
            usuarios.remove(rem_user_id)
            if rem_user_id in notas:
                del notas[rem_user_id]
            await message.reply(f"Usuario {rem_user_id} eliminado como admin temporalmente.")
        else:
            await message.reply(f"{rem_user_id} no es admin")

async def max_time(client, message):
    parts = message.text.split(' ', 1)
    if len(parts) == 2:
        time_str = parts[1]
        add_time = parse_time(time_str)
        for admin_notas in notas.values():
            for note in admin_notas:
                admin_notas[note] += add_time
        await message.reply(f'Se ha añadido {time_str} a todos los usuarios VIP.')

async def time_user(client, message):
    parts = message.text.split(' ', 2)
    if len(parts) == 3:
        note = parts[1]
        time_str = parts[2]
        add_time = parse_time(time_str)
        for admin, admin_notas in notas.items():
            if note in admin_notas:
                admin_notas[note] += add_time
                await message.reply(f'Se ha añadido {time_str} a "{note}".')
                break
        else:
            await message.reply(f'"{note}" no es VIP.')

async def pause(client, message):
    for admin, admin_notas in notas.items():
        for note in list(admin_notas.keys()):
            expire_time = admin_notas.pop(note)
            pausados[note] = expire_time
    await message.reply('Tiempo de todos los VIPs pausado.')

async def continuar(client, message):
    for note, expire_time in list(pausados.items()):
        for admin, admin_notas in notas.items():
            admin_notas[note] = expire_time
        pausados.pop(note)
    await message.reply('Tiempo de todos los VIPs continuado.')

async def pause_user(client, message):
    parts = message.text.split(' ', 1)
    if len(parts) == 2:
        note = parts[1]
        for admin, admin_notas in notas.items():
            if note in admin_notas:
                expire_time = admin_notas.pop(note)
                pausados[note] = expire_time
                await message.reply(f'Tiempo de "{note}" pausado.')
                break
        else:
            await message.reply(f'"{note}" no es VIP.')

async def continue_user(client, message):
    parts = message.text.split(' ', 1)
    if len(parts) == 2:
        note = parts[1]
        if note in pausados:
            expire_time = pausados.pop(note)
            for admin, admin_notas in notas.items():
                admin_notas[note] = expire_time
            await message.reply(f'Tiempo de "{note}" continuado.')
        else:
            await message.reply(f'"{note}" no está pausado.')

@app.on_message(filters.text)
async def handle_message(client, message):
    text = message.text
    user_id = message.from_user.id
    if user_id not in usuarios:
        return
    if text.startswith('/start'):
        await start(client, message)
    elif text.startswith('/addvip'):
        await add_vip(client, message)
    elif text.startswith('/vervip'):
        await ver_vip(client, message)
    elif text.startswith('/remvip'):
        await rem_vip(client, message)
    elif text.startswith('/addadmin'):
        await add_admin(client, message)
    elif text.startswith('/remadmin'):
        await rem_admin(client, message)
    elif text.startswith('/maxtime'):
        await max_time(client, message)
    elif text.startswith('/timeuser'):
        await time_user(client, message)
    elif text.startswith('/pause'):
        await pause(client, message)
    elif text.startswith('/continue'):
        await continuar(client, message)
    elif text.startswith('/pauseuser'):
        await pause_user(client, message)
    elif text.startswith('/continueuser'):
        await continue_user(client, message)

async def check_expiry():
    while True:
        now = datetime.now()
        for admin, admin_notas in list(notas.items()):
            for note, expire_time in list(admin_notas.items()):
                if expire_time <= now:
                    await app.send_message(admin, f'"{note}" terminó su tiempo como VIP.')
                    del admin_notas[note]
        await asyncio.sleep(60)  # Revisa cada minuto

app.start()
app.loop.run_until_complete(check_expiry())
app.idle()
