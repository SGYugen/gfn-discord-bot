import discord
import requests
import os

TOKEN = os.getenv("TOKEN")

URL_JSON = "https://raw.githubusercontent.com/SGYugen/gfn-discord-bot/main/data/errors.json"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

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

        try:
            data = requests.get(URL_JSON).json()
        except:
            await message.channel.send("⚠️ Error al obtener datos")
            return

        if codigo in data:
            info = data[codigo]

            respuesta = f"🔎 **Error: {codigo}**\n"
            respuesta += f"📌 {info['descripcion']}\n\n💡 Soluciones:\n"

            for s in info["soluciones"]:
                respuesta += f"- {s}\n"
        else:
            respuesta = f"⚠️ Error {codigo} no encontrado.\nSe investigará."

        await message.channel.send(respuesta)

client.run(TOKEN)
