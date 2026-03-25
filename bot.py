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

        await message.channel.send(f"🔍 Buscando solución para {codigo}...")

        resultados = buscar_en_reddit(codigo)

        if resultados:
            respuesta = f"💡 Posibles soluciones encontradas en Reddit para {codigo}:\n\n"
            
            for r in resultados:
                respuesta += r + "\n\n"

        else:
            respuesta = f"⚠️ No encontré soluciones en Reddit para {codigo}"

        await message.channel.send(respuesta)

client.run(TOKEN)
