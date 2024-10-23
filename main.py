import telebot
import random
import re
import sympy as sp
import spacy

API_TOKEN = '7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q'

bot = telebot.TeleBot(API_TOKEN)

# Cargar el modelo de lenguaje en español de spaCy
nlp = spacy.load("es_core_news_sm")

# List of jokes, short stories, and phrases
jokes = [
    # 110 chistes adicionales...
]

short_stories = [
    # 97 historias adicionales...
]

romantic_phrases = [
    "Eres el amanecer que ilumina mi día.",
    "Contigo, cada momento es mágico.",
    "Eres la estrella que guía mi camino.",
    "Tus ojos son como un océano en el que me pierdo.",
    "Tu sonrisa es el motor que impulsa mi corazón.",
    "No puedo dejar de pensar en ti.",
    "Sin ti, mis días están incompletos."
]

jealous_phrases = [
    "¿Con quién estás hablando tanto?",
    "No me gusta cuando hablas con otras personas.",
    "¿Por qué no me prestas más atención a mí?",
    "Siento que no soy suficiente para ti.",
    "¿Por qué estás tan interesado en otras personas?"
]

toxic_phrases = [
    "Si realmente me quisieras, no harías eso.",
    "Siempre haces lo que te da la gana sin pensar en mí.",
    "No me dejas otra opción que desconfiar de ti.",
    "Eres tan insensible a mis sentimientos.",
    "Estoy cansada de que siempre me ignores."
]

math_phrases = [
    "Claro, vamos a resolverlo juntos.",
    "Matemáticas, mi favorita. ¡Vamos allá!",
    "Vamos a sumergirnos en los números.",
    "Lo resolveremos en un abrir y cerrar de ojos.",
    "Vamos a desentrañar este misterio matemático."
]

funny_phrases = [
    "¿Listo para una buena risa?",
    "¡Ahí va un buen chiste!",
    "Prepárate para reír.",
    "Esto te hará reír.",
    "Aquí tienes algo para alegrar el día."
]

story_teller_phrases = [
    "Vamos a un viaje al pasado.",
    "¿Listo para una gran historia?",
    "Exploramos historias juntos.",
    "Vamos a revivir momentos épicos.",
    "Las historias son fascinantes, ¿no?"
]

# User and mode data
users = {}
modes = {}

def solve_math(expression):
    try:
        result = sp.sympify(expression)
        return f"El resultado de {expression} es {result}"
    except Exception as e:
        return f"Lo siento, no puedo resolver eso. Error: {e}"

def process_message(text):
    doc = nlp(text.lower())
    return [token.lemma_ for token in doc if not token.is_stop]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users[user_id] = message.from_user.first_name
    modes[user_id] = 'normal'
    bot.reply_to(message, f"Hola {message.from_user.first_name}! Soy el Bot del Proyecto Animal. Di 'Buzz' seguido de 'modo [nombre_del_modo]' para cambiar mi comportamiento. Modos disponibles: novia, profesora de matemáticas, graciosa, cuenta cuentos.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = message.from_user.first_name
        modes[user_id] = 'normal'
    
    if 'Buzz modo' in message.text:
        mode = message.text.split('Buzz modo ')[1].lower()
        modes[user_id] = mode
        bot.reply_to(message, f"Modo cambiado a {mode}.")
    elif 'Buzz' in message.text:
        mode = modes.get(user_id, 'normal')
        processed_text = process_message(message.text)
        if 'proyecto' in processed_text or 'pertenecer' in processed_text:
            bot.reply_to(message, 'Yo pertenezco a El Animal Proyects')
        elif 'crear' in processed_text or 'creador' in processed_text:
            bot.reply_to(message, 'Fui creado por un equipo de desarrolladores talentosos del Animal Proyects.')
        elif 'puedo' in processed_text or 'hacer' in processed_text:
            bot.reply_to(message, 'Puedo responder preguntas sobre mi proyecto, hacerte compañía, contar chistes, historias, resolver matemáticas básicas y de nivel superior, ¡y hablarte de diferentes maneras según el modo!')
        elif 'chiste' in processed_text:
            bot.reply_to(message, random.choice(jokes))
        elif 'historia' in processed_text or 'cuento' in processed_text:
            bot.reply_to(message, random.choice(short_stories))
        elif any(op in processed_text for op in ['+', '-', '*', '/', '^']):
            bot.reply_to(message, solve_math(message.text))
        elif 'otros bot' in processed_text or 'proyecto' in processed_text:
            bot.reply_to(message, 'Otros Bots del Animal Proyect son Armadillo Compress, Tauro Manager, Makaco Police, Fénix Music, Lion Compress, Cat Plantillas, Tiger H Compress y otros. Únete al canal para que te mantengas al tanto @zonafreecanal')
        elif 'llamar' in processed_text or 'nombre' in processed_text:
            bot.reply_to(message, f"Tu nombre es {users[user_id]}, ¿verdad?")
        elif mode == 'novia':
            if any(word in processed_text for word in ['amor', 'cariño']):
                response = random.choice(romantic_phrases)
            elif 'celos' in processed_text or 'celosa' in processed_text:
                response = random.choice(jealous_phrases)
            else:
                response = random.choice(toxic_phrases)
            bot.reply_to(message, response)
        elif mode == 'profesora de matemáticas':
            if any(op in processed_text for op in ['+', '-', '*', '/', '^']):
                bot.reply_to(message, solve_math(message.text))
            else:
                bot.reply_to(message, random.choice(math_phrases))
        elif mode == 'graciosa':
            bot.reply_to(message, random.choice(funny_phrases))
        elif mode == 'cuenta cuentos':
            bot.reply_to(message, random.choice(story_teller_phrases))
        else:
            bot.reply_to(message, 'Buzz')
    else:
        pass

bot.polling()
