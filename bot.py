import discord
import requests
import os

TOKEN = os.getenv("TOKEN")

URL_JSON = "https://raw.githubusercontent.com/SGYugen/gfn-discord-bot/main/data/errors.json"

HEADERS = {"User-Agent": "gfn-bot"}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def obtener_json():
    try:
        res = requests.get(URL_JSON)
        return res.json()
    except:
        return {}

def buscar_en_reddit(codigo):
    url = f"https://www.reddit.com/r/GeForceNOW/search.json?q={codigo}&restrict_sr=1&sort=relevance&limit=3"
    
    try:
        res = requests.get(url, headers=HEADERS)
        data = res.json()
    except:
        return []

    resultados = []

    for post in data.get("data", {}).get("children", []):
        titulo = post["data"]["title"]
        link = "https://reddit.com" + post["data"]["permalink"]

        resultados.append(f"🔗 {titulo}\n{link}")

    return resultados

def buscar_en_google(codigo):
    query = f"{codigo} geforce now error solucion"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    return f"🌐 Buscar en Google:\n{url}"

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
                codigo = palabra.lower().strip()
                break

        if not codigo:
            return

        data = obtener_json()

        # 🔹 1. BUSCAR EN JSON
        if codigo in data:
            info = data[codigo]

            respuesta = f"🔎 Error: {codigo}\n"
            respuesta += f"{info.get('descripcion', '')}\n\nSoluciones:\n"

            for s in info.get("soluciones", []):
                respuesta += f"- {s}\n"

            await message.channel.send(respuesta)

        else:
            # 🔹 2. BUSCAR EN REDDIT
            await message.channel.send(f"🔍 Buscando en Reddit {codigo}...")

            resultados = buscar_en_reddit(codigo)

            if resultados:
                respuesta = "💡 Encontré esto en Reddit:\n\n"
                for r in resultados:
                    respuesta += r + "\n\n"

                await message.channel.send(respuesta)

            else:
                # 🔹 3. GOOGLE FALLBACK
                google = buscar_en_google(codigo)

                await message.channel.send(
                    f"⚠️ No encontré en Reddit.\n\n{google}"
                )

client.run(TOKEN)
