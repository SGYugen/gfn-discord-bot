import discord
import requests

TOKEN = "TU_TOKEN_AQUI"
URL_JSON = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/data/errors.json"

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

    # detectar código directamente en mensaje
    if "0x" in message.content.lower():
        codigo = None
        palabras = message.content.split()

        for palabra in palabras:
            if palabra.lower().startswith("0x"):
                codigo = palabra
                break

        if not codigo:
            return

        data = requests.get(URL_JSON).json()

        if codigo in data:
            info = data[codigo]

            respuesta = f"🔎 **Error: {codigo}**\n"
            respuesta += f"📌 {info['descripcion']}\n\n💡 Soluciones:\n"

            for s in info["soluciones"]:
                respuesta += f"- {s}\n"

        else:
            respuesta = f"⚠️ Error {codigo} no encontrado en base de datos.\nSe investigará."

        await message.channel.send(respuesta)

client.run(TOKEN)
