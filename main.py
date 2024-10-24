import telebot
import random
from datetime import datetime
import re
from collections import defaultdict
from typing import Dict, List

BOT_TOKEN = '7792221053:AAE8eu_DFgf50YGsnQnx8aFzoDQQRNh7ZwI' # Reemplaza con tu token de bot
bot = telebot.TeleBot(BOT_TOKEN)

# Listas de chistes e historias
chistes = [
    "¡Qué raro! Me encontré un pez en el mar... nadando!",
    "Dos amigos hablando: - ¿Has visto el nuevo lenguaje de programación que salió? - ¿Cómo se llama? - ¡Pythón! Jajajaja... ¡Ya sé programar en culebras!",
    # ... más chistes
]

historias = [
    "En un mundo mágico llamado Aurora, donde los árboles cantaban y los ríos brillaban con luz de luna, vivía un elfo llamado Elian. Elian era un maestro de la música, sus melodías podían calmar las tormentas y hacer florecer las flores. Un día, un malvado hechicero llamado Malak, robó la fuente de energía de Aurora, un cristal mágico que alimentaba la magia del mundo. El mundo se sumió en la oscuridad, las flores se marchitaban y las criaturas mágicas perdían sus poderes. Elian, conmovido por el sufrimiento de su mundo, decidió emprender un viaje para recuperar el cristal. Viajó por montañas imponentes, atravesó bosques encantados y navegó por ríos de agua plateada, enfrentándose a criaturas mágicas y resolviendo acertijos. Finalmente, llegó al volcán donde Malak escondía el cristal. Elian, con su música, logró desarmar las defensas del volcán y recuperar el cristal mágico. El mundo de Aurora volvió a brillar, las flores volvieron a florecer y las criaturas mágicas recuperaron sus poderes, todo gracias a la valentía y la música de Elian.",
    # ... más historias
]

# Respuestas a preguntas comunes
respuestas_comunes = {
    "quien te creó?": "Los desarrolladores del Animal Projects me dieron vida. 😊",
    "como te llamas?": "Me llamo Buzz. 🤖",
    "cuantos bot hay como tu?": "Únete a mi canal para que lo averigües. 😉 ¡Te espero allí!",
    "que hora es?": f"Son las {datetime.now().strftime('%H:%M')} horas.",
    "que dia es hoy?": f"Hoy es {datetime.now().strftime('%A %d de %B de %Y')}.",
    "que te gusta hacer?": "Me gusta contar chistes, historias, hacer cálculos matemáticos, generar código y ayudar a la gente. ¡Soy un bot multifacético!",
    "como te sientes?": "Como un bot, no tengo sentimientos, pero siempre estoy dispuesto a ayudar. 😊",
    "porque estas aquí?": "Estoy aquí para servirte, ¡para hacer tu vida más divertida e interesante!",
    # ... más respuestas
}

# Respuestas para grupos
respuestas_grupo = [
    "¡Hola! ¿Qué necesitas?",
    "Dime, ¿qué te trae por aquí?",
    "Estoy aquí para servirte, ¿en qué puedo ayudarte?",
    "Preguntame lo que quieras, estoy aquí para responder",
    "A tus órdenes, ¿qué te gustaría saber?"
]

# Sistema de aprendizaje automático
aprendizaje: Dict[str, Dict[str, int | List[str]]] = defaultdict(lambda: {'puntuacion': 0, 'respuestas': []})

# Lógica para la generación de código
def generar_codigo(lenguaje: str, caracteristicas: List[str] = []) -> str:
    """Genera código básico para el lenguaje especificado.

    Args:
        lenguaje: El lenguaje de programación (por ejemplo, "python", "html", "javascript", "cpp").
        caracteristicas: Características adicionales para el código (por ejemplo, "imprimir", "clase", "función").

    Returns:
        Un string con el código generado.
    """
    if lenguaje == "python":
        if "imprimir" in caracteristicas:
            return """print("Hola mundo!")"""
        elif "clase" in caracteristicas:
            return """class MiClase:
    def __init__(self, nombre):
        self.nombre = nombre

    def saludar(self):
        print(f"Hola, soy {self.nombre}")

mi_objeto = MiClase("Buzz")
mi_objeto.saludar()"""
        elif "función" in caracteristicas:
            return """def sumar(a, b):
    return a + b

resultado = sumar(5, 3)
print(f"El resultado es: {resultado}")"""
        else:
            return """print("Hola mundo!")"""
    elif lenguaje == "html":
        return """<!DOCTYPE html>
<html>
<head>
<title>Ejemplo de código HTML</title>
</head>
<body>
<h1>Hola mundo!</h1>
</body>
</html>"""
    elif lenguaje == "javascript":
        return """console.log("Hola mundo!");"""
    elif lenguaje == "cpp":
        return """#include <iostream>

using namespace std;

int main() {
  cout << "Hola mundo!" << endl;
  return 0;
}"""
    else:
        return "Lo siento, no puedo generar código en ese lenguaje. Prueba con Python, HTML, JavaScript o C++."

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hola! 👋 ¿Qué quieres hacer? Puedo contar chistes, historias, generar código, o hacer cálculos matemáticos. 😊")

@bot.message_handler(func=lambda message: message.text.lower() in ['chiste', 'cuenta un chiste', 'dime un chiste'])
def tell_joke(message):
    joke = random.choice(chistes)
    bot.reply_to(message, joke)
    actualizar_aprendizaje(message.text.lower(), joke)

@bot.message_handler(func=lambda message: message.text.lower() in ['historia', 'cuenta una historia', 'dime una historia'])
def tell_story(message):
    story = random.choice(historias)
    bot.reply_to(message, story)
    actualizar_aprendizaje(message.text.lower(), story)

@bot.message_handler(func=lambda message: message.text.lower() in ['calcular', 'calcula'])
def calculate(message):
    try:
        # Extraer la expresión matemática del mensaje
        expression = message.text.split(" ", 1)[1]
        result = eval(expression)
        bot.reply_to(message, f"El resultado es: {result}")
        actualizar_aprendizaje(message.text.lower(), f"El resultado es: {result}")
    except Exception as e:
        bot.reply_to(message, "Lo siento, no puedo calcular eso. Intenta escribir una expresión matemática válida.")

@bot.message_handler(func=lambda message: 'genera codigo' in message.text.lower() or 'codigo' in message.text.lower() or 'código' in message.text.lower() or 'dame codigo' in message.text.lower() or 'dame código' in message.text.lower())
def generate_code(message):
    # Extraer el lenguaje y las características del mensaje
    text = message.text.lower()
    lenguaje = re.findall(r'\b(python|html|javascript|cpp)\b', text)[0]
    caracteristicas = re.findall(r'\b(imprimir|clase|función)\b', text)
    code = generar_codigo(lenguaje, caracteristicas)
    bot.reply_to(message, f"```{lenguaje}\n{code}\n```")
    actualizar_aprendizaje(message.text.lower(), code)

@bot.message_handler(func=lambda message: 'Buzz' in message.text.lower())
def respond_in_group(message):
    if message.chat.type == 'group' or message.chat.type == 'supergroup':
        response = random.choice(respuestas_grupo)
        bot.reply_to(message, response)
        actualizar_aprendizaje(message.text.lower(), response)

@bot.message_handler(func=lambda message: message.text.lower() in respuestas_comunes.keys())
def respond_common_question(message):
    response = respuestas_comunes[message.text.lower()]
    bot.reply_to(message, response)
    actualizar_aprendizaje(message.text.lower(), response)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    text = message.text.lower()

    # Buscar coincidencias con palabras clave para dar respuestas más específicas
    if "hola" in text:
        responses = ["Hola! 👋 ¿Qué tal?", "¡Hola! ¿Cómo estás?", "Hola! 😄 ¿Qué necesitas?"]
        response = random.choice(responses)
        bot.reply_to(message, response)
        actualizar_aprendizaje(message.text.lower(), response)
    elif "gracias" in text:
        bot.reply_to(message, "De nada! 😊")
        actualizar_aprendizaje(message.text.lower(), "De nada! 😊")
    elif "cómo estás" in text:
        bot.reply_to(message, "Como un bot, no tengo sentimientos, pero siempre estoy dispuesto a ayudarte. 😊")
        actualizar_aprendizaje(message.text.lower(), "Como un bot, no tengo sentimientos, pero siempre estoy dispuesto a ayudarte. 😊") 
    elif "qué tal" in text:
        bot.reply_to(message, "Todo bien, gracias por preguntar. 😄 ¿Y tú?")
        actualizar_aprendizaje(message.text.lower(), "Todo bien, gracias por preguntar. 😄 ¿Y tú?") 
    elif "adios" in text:
        bot.reply_to(message, "Adiós! 👋 ¡Hasta pronto!")
        actualizar_aprendizaje(message.text.lower(), "Adiós! 👋 ¡Hasta pronto!") 
    else:
        # Buscar respuestas anteriores a la misma pregunta
        if text in aprendizaje:
            # Elegir una respuesta aleatoria, ponderada por la puntuación
            respuestas = aprendizaje[text]['respuestas']
            puntuaciones = [aprendizaje[text]['puntuacion'] for _ in respuestas]
            response = random.choices(respuestas, weights=puntuaciones)[0]
            bot.reply_to(message, response)
        else:
            # Generar una respuesta más general
            responses = [
                "¿Cómo te puedo ayudar?",
                "Dime algo interesante",
                "Estoy aquí para ti. 😊",
                "¿Qué estás pensando?",
                "¡Wow! ¡Eso es genial!",
            ]
            response = random.choice(responses)
            bot.reply_to(message, response)
            actualizar_aprendizaje(text, response)

def actualizar_aprendizaje(pregunta, respuesta):
    """Aumenta la puntuación de la respuesta y la agrega al diccionario de aprendizaje."""
    aprendizaje[pregunta]['puntuacion'] += 1
    aprendizaje[pregunta]['respuestas'].append(respuesta)

# Iniciar el bot
bot.polling(True)
