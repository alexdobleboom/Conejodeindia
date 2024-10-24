import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import re
from datetime import datetime, timedelta

# Variables
api_id = '24288670'  # Reemplaza con tu API ID
api_hash = '81c58005802498656d6b689dae1edacc'  # Reemplaza con tu API Hash
bot_token = '7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q'  # Reemplaza con tu token del bot
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

@app.on_message(filters.text)
async def handle_message(client, message):
    text = message.text
    user_id = message.from_user.id

    if user_id not in usuarios:
        return

    if text.startswith(('/start')):
        await message.reply(f'Funcionando')
    elif text.startswith(('/addvip')):
        parts = message.text.split(' ', 1)
        if len(parts) == 2:
            note, time_str = parts[1].split('/')
            expire_time = datetime.now() + parse_time(time_str)
            if user_id not in notas:
                notas[user_id] = {}
            notas[user_id][note] = expire_time
            await message.reply(f'Usuario "{note}" añadido como VIP por {time_str}.')
    elif text.startswith(('/vervip')):
        if user_id in notas and notas[user_id]:
            notas_list = '\n'.join([
                f'{note} {((exp - datetime.now()).days)}dias:{((exp - datetime.now()).seconds // 3600)}hrs:{(((exp - datetime.now()).seconds // 60) % 60)}min'
                for note, exp in notas[user_id].items()
            ])
            await message.reply(f'Usuarios VIPs:\n{notas_list}')
        else:
            await message.reply('No hay VIPs.')
    elif text.startswith(('/remvip')):
        parts = message.text.split(' ', 1)
        if len(parts) == 2:
            note = parts[1]
            if user_id in notas and note in notas[user_id]:
                del notas[user_id][note]
                await message.reply(f'VIP de "{note}" eliminado.')
            else:
                await message.reply(f'"{note}" no es VIP.')
    elif text.startswith(('/addadmin')):
        if user_id in admins:
            new_user_id = int(message.text.split()[1])
            tempadmins.append(new_user_id)
            usuarios.append(new_user_id)
            if new_user_id not in notas:
                notas[new_user_id] = {}
            await message.reply(f"Usuario {new_user_id} añadido como admin temporalmente.")
        else:
            await message.reply(f"Usted no puede añadir admins.")
    elif text.startswith(('/remadmin')):
        if user_id in admins:
            rem_user_id = int(message.text.split()[1])
            if rem_user_id in tempadmins:
                tempadmins.remove(rem_user_id)
                usuarios.remove(rem_user_id)
                if rem_user_id in notas:
                    del notas[rem_user_id]
                await message.reply(f"Usuario {rem_user_id} eliminado como admin temporalmente.")
            else:
                await message.reply(f"{rem_user_id} no es admin")
    elif text.startswith(('/maxtime')):
        parts = message.text.split(' ', 1)
        if len(parts) == 2:
            time_str = parts[1]
            add_time = parse_time(time_str)
            for admin_notas in notas.values():
                for note in admin_notas:
                    admin_notas[note] += add_time
            await message.reply(f'Se ha añadido {time_str} a todos los usuarios VIP.')
    elif text.startswith(('/timeuser')):
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
    elif text.startswith(('/pause')):
        now = datetime.now()
        for admin, admin_notas in notas.items():
            if admin not in pausados:
                pausados[admin] = {}
            for note, expire_time in admin_notas.items():
                pausados[admin][note] = (expire_time - now).total_seconds()
                admin_notas[note] = now  # Set expire time to now to pause
        await message.reply(f'Tiempo pausado para todos los usuarios VIP.')
    elif text.startswith(('/pauseuser')):
        parts = message.text.split(' ', 1)
        if len(parts) == 2:
            note = parts[1]
            for admin, admin_notas in notas.items():
                if note in admin_notas:
                    expire_time = admin_notas[note]
                    if admin not in pausados:
                        pausados[admin] = {}
                    pausados[admin][note] = (expire_time - datetime.now()).total_seconds()
                    admin_notas[note] = datetime.now()  # Set expire time to now to pause
                    await message.reply(f'Tiempo pausado para "{note}".')
                    break
            else:
                await message.reply(f'"{note}" no es VIP.')
    elif text.startswith(('/continue')):
        now = datetime.now()
        for admin, admin_notas in notas.items():
            if admin in pausados:
                for note, remaining_time in pausados[admin].items():
                    admin_notas[note] = now + timedelta(seconds=remaining_time)
                del pausados[admin]
        await message.reply(f'Tiempo continuado para todos los usuarios VIP.')
    elif text.startswith(('/cantiuser')):
        parts = message.text.split(' ', 1)
        if len(parts) == 2:
            note = parts[1]
            for admin, admin_notas in notas.items():
                if note in pausados.get(admin, {}):
                    remaining_time = pausados[admin][note]
                    admin_notas[note] = datetime.now() + timedelta(seconds=remaining_time)
                    del pausados[admin][note]
                    await message.reply(f'Tiempo continuado para "{note}".')
                    break
            else:
                await message.reply(f'"{note}" no es VIP.')

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
