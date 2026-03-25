import discord
import os
import requests
from google import genai

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 🔴 CAMBIA ESTO POR TU REPO REAL (opcional)
URL_JSON = "https://raw.githubusercontent.com/SGYugen/gfn-discord-bot/main/data/errors.json"

# Cliente IA (Gemini)
client_ai = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# 🔍 Obtener base propia
def obtener_json():
    try:
        res = requests.get(URL_JSON, timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}
    except:
        return {}

# 🧠 IA REAL (Gemini)
def analizar_con_ia(codigo):
    try:
        response = client_ai.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            El error {codigo} pertenece a GeForce NOW.

            Explica en español con este formato EXACTO:

            Resumen:
            Explica claramente el problema

            Soluciones:
            - solución 1
            - solución 2
            - solución 3

            Sé claro, útil y basado en problemas reales.
            """
        )

        return response.text

    except Exception as e:
        print("ERROR GEMINI:", e)
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
