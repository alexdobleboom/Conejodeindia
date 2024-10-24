import telebot
import random
from datetime import datetime
import re
from collections import defaultdict
from typing import Dict, List

BOT_TOKEN = '7507770865:AAFDQ0Lbuo5Ca-mTnqSa-dK_UJENs5B2v1Q' # Reemplaza con tu token de bot
bot = telebot.TeleBot(BOT_TOKEN)

# Listas de chistes e historias
chistes = [
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cuál es el colmo de un electricista? No encontrar corriente en una conversación.",
    "¿Por qué los esqueletos no pelean entre ellos? Porque no tienen agallas.",
    "¿Qué le dice un gusano a otro gusano? Voy a dar una vuelta a la manzana.",
    "¿Por qué el libro de matemáticas está deprimido? Porque tiene demasiados problemas.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cómo se dice pañuelo en japonés? Saka-moko.",
    "¿Qué le dice una iguana a su hermana gemela? Somos iguanitas.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Cómo se despiden los químicos? Ácido un placer.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cuál es el colmo de un electricista? No encontrar corriente en una conversación.",
    "¿Por qué los esqueletos no pelean entre ellos? Porque no tienen agallas.",
    "¿Qué le dice un gusano a otro gusano? Voy a dar una vuelta a la manzana.",
    "¿Por qué el libro de matemáticas está deprimido? Porque tiene demasiados problemas.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cómo se dice pañuelo en japonés? Saka-moko.",
    "¿Qué le dice una iguana a su hermana gemela? Somos iguanitas.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Cómo se despiden los químicos? Ácido un placer.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cuál es el colmo de un electricista? No encontrar corriente en una conversación.",
    "¿Por qué los esqueletos no pelean entre ellos? Porque no tienen agallas.",
    "¿Qué le dice un gusano a otro gusano? Voy a dar una vuelta a la manzana.",
    "¿Por qué el libro de matemáticas está deprimido? Porque tiene demasiados problemas.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cómo se dice pañuelo en japonés? Saka-moko.",
    "¿Qué le dice una iguana a su hermana gemela? Somos iguanitas.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Cómo se despiden los químicos? Ácido un placer.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cuál es el colmo de un electricista? No encontrar corriente en una conversación.",
    "¿Por qué los esqueletos no pelean entre ellos? Porque no tienen agallas.",
    "¿Qué le dice un gusano a otro gusano? Voy a dar una vuelta a la manzana.",
    "¿Por qué el libro de matemáticas está deprimido? Porque tiene demasiados problemas.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cómo se dice pañuelo en japonés? Saka-moko.",
    "¿Qué le dice una iguana a su hermana gemela? Somos iguanitas.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Cómo se despiden los químicos? Ácido un placer.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cuál es el colmo de un electricista? No encontrar corriente en una conversación.",
    "¿Por qué los esqueletos no pelean entre ellos? Porque no tienen agallas.",
    "¿Qué le dice un gusano a otro gusano? Voy a dar una vuelta a la manzana.",
    "¿Por qué el libro de matemáticas está deprimido? Porque tiene demasiados problemas.",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
    "¿Cómo se dice pañuelo en japonés? Saka-moko.",
    "¿Qué le dice una iguana a su hermana gemela? Somos iguanitas.",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter.",
]

historias = [
    "En un mundo mágico llamado Aurora, donde los árboles cantaban y los ríos brillaban con luz de luna, vivía un elfo llamado Elian. Elian era un maestro de la música, sus melodías podían calmar las tormentas y hacer florecer las flores. Un día, un malvado hechicero llamado Malak, robó la fuente de energía de Aurora, un cristal mágico que alimentaba la magia del mundo. El mundo se sumió en la oscuridad, las flores se marchitaban y las criaturas mágicas perdían sus poderes. Elian, conmovido por el sufrimiento de su mundo, decidió emprender un viaje para recuperar el cristal. Viajó por montañas imponentes, atravesó bosques encantados y navegó por ríos de agua plateada, enfrentándose a criaturas mágicas y resolviendo acertijos. Finalmente, llegó al volcán donde Malak escondía el cristal. Elian, con su música, logró desarmar las defensas del volcán y recuperar el cristal mágico. El mundo de Aurora volvió a brillar, las flores volvieron a florecer y las criaturas mágicas recuperaron sus poderes, todo gracias a la valentía y la música de Elian.",
    "En un reino lejano, habitaba una princesa llamada Luna. Luna era conocida por su belleza y su inteligencia, pero también por su gran tristeza. Su corazón estaba lleno de melancolía, pues no encontraba el amor verdadero. Un día, un joven caballero llamado Leon, llegó al reino en busca de aventuras. Leon era valeroso y noble, y su corazón latía con un amor puro e incondicional. Al conocer a Luna, quedó cautivado por su belleza y su tristeza. Leon se propuso alegrar su corazón y encontrar la fuente de su melancolía. Juntos, emprendieron un viaje por el reino, descubriendo secretos ocultos y enfrentándose a peligros inesperados. Leon demostró su valentía y su amor por Luna en cada paso del camino. Finalmente, descubrieron que la tristeza de Luna se debía a una maldición ancestral que la obligaba a vivir en soledad. Leon, con la ayuda de la magia del reino, logró romper la maldición y liberar el corazón de Luna. Juntos, finalmente encontraron el amor verdadero y vivieron felices por siempre.",
    "En una tierra donde las estrellas danzaban en el cielo, vivía un niño llamado Kai. Kai era un niño curioso y aventurero, siempre buscando nuevas experiencias. Un día, mientras exploraba el bosque cercano a su casa, encontró un extraño objeto: una pequeña caja de madera con un brillo misterioso. Intrigado, Kai abrió la caja y descubrió un pequeño dragón de jade. El dragón, al ser liberado de la caja, cobró vida y habló con Kai. El dragón, llamado Draco, le contó a Kai que era el guardián de una antigua leyenda: la leyenda del árbol de la sabiduría. Draco le dijo a Kai que el árbol de la sabiduría se encontraba en un lugar secreto del bosque y que solo aquellos con un corazón puro y una mente abierta podían encontrarla. Kai, fascinado por la leyenda, decidió emprender una aventura para encontrar el árbol de la sabiduría. Con Draco como su guía, Kai se enfrentó a pruebas y peligros, superando obstáculos y aprendiendo valiosas lecciones. Finalmente, después de un largo viaje, Kai llegó al lugar secreto donde se encontraba el árbol de la sabiduría. El árbol, con su esplendor mágico, le otorgó a Kai un conocimiento infinito, convirtiéndolo en un sabio y poderoso mago. Kai regresó a su hogar con Draco a su lado, listo para compartir su sabiduría con el mundo.",
    "En un mundo donde los sueños se hacían realidad, vivía una niña llamada Iris. Iris era una niña soñadora y creativa, siempre imaginando mundos fantásticos y aventuras increíbles. Un día, mientras dormía, Iris fue transportada a un mundo mágico donde todo era posible. En este mundo, Iris conoció a un grupo de criaturas mágicas que la guiaron a través de un laberinto de sueños. Durante su viaje, Iris descubrió que el mundo de los sueños estaba en peligro. Un ser oscuro llamado Sombra estaba robando los sueños de la gente, sumiéndolos en la oscuridad y la desesperación. Iris, con la ayuda de sus nuevos amigos mágicos, decidió luchar contra Sombra y recuperar los sueños perdidos. Iris, con su imaginación y creatividad, logró derrotar a Sombra y liberar los sueños de la gente. El mundo mágico volvió a brillar y Iris regresó a su hogar con una nueva perspectiva y un corazón lleno de esperanza."
]

# Respuestas a preguntas comunes
respuestas_comunes = {
    "quien te creó?": "Los desarrolladores del Animal Projects me dieron vida. 😊",
    "como te llamas?": "Me llamo Buzz. 🤖",
    "cuantos bot hay como tu?": "Únete a mi canal para que lo averigües canal @zonafreecanal . 😉 ¡Te espero allí!",
    "que hora es?": f"Son las {datetime.now().strftime('%H:%M')} horas.",
    "que dia es hoy?": f"Hoy es {datetime.now().strftime('%A %d de %B de %Y')}.",
    "que te gusta hacer?": "Me gusta contar chistes, historias, hacer cálculos matemáticos, generar código y ayudar a la gente. ¡Soy un bot multifacético!",
    "como te sientes?": "Como un bot, no tengo sentimientos, pero siempre estoy dispuesto a ayudar. 😊",
    "porque estas aquí?": "Estoy aquí para servirte, ¡para hacer tu vida más divertida e interesante!",
    "cuál es tu función?": "Mi función es ayudarte con tus tareas, entretenerte y aprender contigo. 😊"
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


@bot.message_handler(func=lambda message: 'Buzz' in message.text.lower())
def handle_message_with_buzz(message):
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
    elif 'hora' in text.lower():
        bot.reply_to(message, f"Son las {datetime.now().strftime('%H:%M')} horas.")
        actualizar_aprendizaje(message.text.lower(), f"Son las {datetime.now().strftime('%H:%M')} horas.")
    elif 'chiste' in text.lower() or 'chistes' in text.lower():
        joke = random.choice(chistes)
        bot.reply_to(message, joke)
        actualizar_aprendizaje(message.text.lower(), joke)
    elif 'historia' in text.lower() or 'cuento' in text.lower():
        story = random.choice(historias)
        bot.reply_to(message, story)
        actualizar_aprendizaje(message.text.lower(), story)
    elif 'suma' in text.lower() or 'resta' in text.lower() or 'divide' in text.lower() or 'multiplica' in text.lower() or 'cuanto es' in text.lower() or 'cual es el resultado' in text.lower():
        try:
            # Extraer los números y la operación del mensaje
            numbers = re.findall(r'\d+', text)
            if len(numbers) != 2:
                bot.reply_to(message, "Por favor, escribe dos números y una operación (suma, resta, multiplica o divide).")
                return
            num1 = int(numbers[0])
            num2 = int(numbers[1])

            if 'suma' in text.lower():
                result = num1 + num2
                bot.reply_to(message, f"El resultado de la suma es: {result}")
            elif 'resta' in text.lower():
                result = num1 - num2
                bot.reply_to(message, f"El resultado de la resta es: {result}")
            elif 'multiplica' in text.lower():
                result = num1 * num2
                bot.reply_to(message, f"El resultado de la multiplicación es: {result}")
            elif 'divide' in text.lower():
                if num2 == 0:
                    bot.reply_to(message, "No se puede dividir entre cero.")
                    return
                result = num1 / num2
                bot.reply_to(message, f"El resultado de la división es: {result}")
            actualizar_aprendizaje(message.text.lower(), f"El resultado es: {result}")
        except Exception as e:
            bot.reply_to(message, "Lo siento, no puedo calcular eso. Intenta escribir una expresión matemática válida.")
    elif 'crea un código' in text or 'código' in text or 'un script' in text or 'code' in text or 'un code' in text or 'script' in text:
        # Extraer el lenguaje y las características del mensaje
        lenguaje = re.findall(r'\b(python|html|javascript|cpp)\b', text)[0]
        caracteristicas = re.findall(r'\b(imprimir|clase|función)\b', text)
        code = generar_codigo(lenguaje, caracteristicas)
        bot.reply_to(message, f"```{lenguaje}\n{code}\n```")
        actualizar_aprendizaje(message.text.lower(), code)
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hola! 👋 ¿Qué quieres hacer? Puedo contar chistes, historias, generar código, o hacer cálculos matemáticos. 😊")

def actualizar_aprendizaje(pregunta, respuesta):
    """Aumenta la puntuación de la respuesta y la agrega al diccionario de aprendizaje."""
    aprendizaje[pregunta]['puntuacion'] += 1
    aprendizaje[pregunta]['respuestas'].append(respuesta)

# Iniciar el bot
bot.polling(True)
