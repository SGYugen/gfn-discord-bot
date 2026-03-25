import discord
import os
import google.generativeai as genai
import requests

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 🔴 URL DE TU JSON (opcional)
URL_JSON = "https://raw.githubusercontent.com/SGYugen/gfn-discord-bot/main/data/errors.json"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# 🔍 Obtener base propia
def obtener_json():
    try:
        res = requests.get(URL_JSON)
        return res.json()
    except:
        return {}


# 🧠 IA (Google Gemini)
def analizar_con_ia(codigo):
    prompt = f"""
    El error {codigo} pertenece a GeForce NOW.

    Investiga y responde en español con este formato:

    Resumen:
    Explica claramente el problema

    Soluciones:
    - solución 1
    - solución 2
    - solución 3

    Sé directo, útil y basado en problemas reales.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "⚠️ No pude obtener información en este momento."


@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if "0x" in message.content.lower():

        codigo = None

        for palabra in message.content.split():
            if palabra.lower().startswith("0x"):
                codigo = palabra.lower().strip()
                break

        if not codigo:
            return

        data = obtener_json()

        # 🔹 1. RESPUESTA RÁPIDA (JSON)
        if codigo in data:
            info = data[codigo]

            respuesta = f"🔎 **Error: {codigo}**\n\n"
            respuesta += f"📌 **Resumen:**\n{info.get('descripcion', '')}\n\n"
            respuesta += "💡 **Soluciones:**\n"

            for s in info.get("soluciones", []):
                respuesta += f"- {s}\n"

        else:
            # 🔹 2. IA (GEMINI)
            await message.channel.send(f"🔍 Analizando {codigo}...")

            ia = analizar_con_ia(codigo)

            respuesta = f"🔎 **Error: {codigo}**\n\n{ia}"

        await message.channel.send(respuesta)


client.run(TOKEN)
