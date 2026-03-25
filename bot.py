import discord
import requests
import os
import re

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

HEADERS = {"User-Agent": "gfn-bot"}

def buscar_en_reddit(codigo):
    url = f"https://www.reddit.com/r/GeForceNOW/search.json?q={codigo}&restrict_sr=1&limit=3"
    
    try:
        res = requests.get(url, headers=HEADERS)
        data = res.json()
    except:
        return None

    resultados = []

    for post in data["data"]["children"]:
        titulo = post["data"]["title"]
        texto = post["data"].get("selftext", "")
        link = "https://reddit.com" + post["data"]["permalink"]

        resultados.append(f"🔗 {titulo}\n{link}")

    return resultados if resultados else None


@client.event
async def on_ready():
    print(f"Bot conectado como {client.user}")

@client.event
URL_JSON = "https://raw.githubusercontent.com/SGYugen/gfn-discord-bot/main/data/errors.json"

def obtener_json():
    try:
        return requests.get(URL_JSON).json()
    except:
        return {}

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if "0x" in message.content.lower():

        codigo = None
        for palabra in message.content.split():
            if palabra.lower().startswith("0x"):
                codigo = palabra
                break

        if not codigo:
            return

        data = obtener_json()

        # 🔹 1. Buscar en base propia
        if codigo in data:
            info = data[codigo]

            respuesta = f"🔎 **Error: {codigo}**\n"
            respuesta += f"📌 {info['descripcion']}\n\n💡 Soluciones:\n"

            for s in info["soluciones"]:
                respuesta += f"- {s}\n"

            await message.channel.send(respuesta)

        else:
            # 🔹 2. Buscar en Reddit
            await message.channel.send(f"🔍 Buscando en Reddit...")

            resultados = buscar_en_reddit(codigo)

            if resultados:
                respuesta = f"💡 Encontré esto en Reddit:\n\n"
                for r in resultados:
                    respuesta += r + "\n\n"
            else:
                respuesta = f"⚠️ No encontré información para {codigo}"

            await message.channel.send(respuesta)

client.run(TOKEN)
