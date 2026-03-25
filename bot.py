import discord
import os
import requests
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# 🔴 opcional (tu base)
URL_JSON = "https://raw.githubusercontent.com/SGYugen/gfn-discord-bot/main/data/errors.json"

# Cliente Cerebras
client_ai = OpenAI(
    api_key=CEREBRAS_API_KEY,
    base_url="https://api.cerebras.ai/v1"
)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# 🔍 JSON base
def obtener_json():
    try:
        res = requests.get(URL_JSON, timeout=5)
        if res.status_code == 200:
            return res.json()
        return {}
    except:
        return {}

# 🧠 IA (Cerebras)
def analizar_con_ia(codigo):
    try:
        response = client_ai.chat.completions.create(
            model="llama3.1-8b",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    El error {codigo} es de GeForce NOW.

                    Dame respuesta en español con este formato:

                    Resumen:
                    Explica el problema

                    Soluciones:
                    - solución 1
                    - solución 2
                    - solución 3

                    Sé claro y basado en problemas reales.
                    """
                }
            ],
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:
        print("ERROR IA:", e)
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

        # 🔹 JSON primero
        if codigo in data:
            info = data[codigo]

            respuesta = f"🔎 **Error: {codigo}**\n\n"
            respuesta += f"📌 **Resumen:**\n{info.get('descripcion', '')}\n\n"
            respuesta += "💡 **Soluciones:**\n"

            for s in info.get("soluciones", []):
                respuesta += f"- {s}\n"

        else:
            await message.channel.send(f"🔍 Analizando {codigo}...")

            ia = analizar_con_ia(codigo)

            respuesta = f"🔎 **Error: {codigo}**\n\n{ia}"

        await message.channel.send(respuesta)

client.run(TOKEN)
