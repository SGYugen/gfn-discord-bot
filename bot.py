import discord
import requests
import os

TOKEN = os.getenv("TOKEN")

# 🔴 CAMBIA ESTO POR TU REPO REAL
URL_JSON = "https://raw.githubusercontent.com/SGYugen/gfn-discord-bot/main/data/errors.json"

HEADERS = {"User-Agent": "gfn-bot"}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# 🔍 Obtener JSON desde GitHub
def obtener_json():
    try:
        res = requests.get(URL_JSON)
        return res.json()
    except:
        return {}

# 🧠 Buscar y analizar Reddit
def buscar_en_reddit(codigo):
    url = f"https://www.reddit.com/r/GeForceNOW/search.json?q={codigo}&restrict_sr=1&sort=relevance&limit=5"
    
    try:
        res = requests.get(url, headers=HEADERS)
        data = res.json()
    except:
        return None

    textos = []

    for post in data.get("data", {}).get("children", []):
        titulo = post["data"]["title"]
        cuerpo = post["data"].get("selftext", "")
        texto = (titulo + " " + cuerpo).lower()
        textos.append(texto)

    if not textos:
        return None

    texto_completo = " ".join(textos)

    # 📌 RESUMEN
    if "connection" in texto_completo or "conex" in texto_completo:
        resumen = "Problema de conexión o estabilidad con servidores."
    elif "login" in texto_completo or "auth" in texto_completo:
        resumen = "Problema de autenticación o inicio de sesión."
    elif "black screen" in texto_completo or "pantalla negra" in texto_completo:
        resumen = "Pantalla negra al iniciar juegos."
    else:
        resumen = "Error reportado por múltiples usuarios en GeForce NOW."

    # 💡 SOLUCIONES
    soluciones = []

    if "restart" in texto_completo or "reiniciar" in texto_completo:
        soluciones.append("Reiniciar la aplicación o dispositivo")

    if "browser" in texto_completo:
        soluciones.append("Usar la versión web del servicio")

    if "vpn" in texto_completo or "region" in texto_completo:
        soluciones.append("Cambiar región o desactivar VPN")

    if "network" in texto_completo or "internet" in texto_completo:
        soluciones.append("Revisar conexión a internet")

    if not soluciones:
        soluciones.append("Probar reiniciar sesión y verificar conexión")

    return resumen, soluciones

# 🌐 Google fallback
def buscar_en_google(codigo):
    query = f"{codigo} geforce now error solucion"
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    return url

@client.event
async def on_ready():
    print(f"✅ Bot conectado como {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if "0x" in message.content.lower():

        codigo = None

        # 🔍 Detectar código
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

            respuesta = f"🔎 **Error: {codigo}**\n\n"
            respuesta += f"📌 **Resumen:**\n{info.get('descripcion', 'Sin descripción')}\n\n"
            respuesta += "💡 **Soluciones:**\n"

            for s in info.get("soluciones", []):
                respuesta += f"- {s}\n"

            await message.channel.send(respuesta)

        else:
            # 🔹 2. REDDIT (resumen inteligente)
            resultado = buscar_en_reddit(codigo)

            if resultado:
                resumen, soluciones = resultado

                respuesta = f"🔎 **Error: {codigo}**\n\n"
                respuesta += f"📌 **Resumen:**\n{resumen}\n\n"
                respuesta += "💡 **Soluciones:**\n"

                for s in soluciones:
                    respuesta += f"- {s}\n"

                await message.channel.send(respuesta)

            else:
                # 🔹 3. GOOGLE
                google = buscar_en_google(codigo)

                await message.channel.send(
                    f"⚠️ No encontré información suficiente.\n\n🔎 Puedes buscar aquí:\n{google}"
                )

client.run(TOKEN)
