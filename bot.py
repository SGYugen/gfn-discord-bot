import discord
import os
import json
import re
import pandas as pd
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# 🔒 CONFIG
FORO_TECNICO_ID = 1486483140271931495
CANAL_RAPIDO_ID = 1486499974119166012  # 👈 CAMBIAR
ROL_MOD_ID = 1486483938665959596

# IA
client_ai = OpenAI(
    api_key=CEREBRAS_API_KEY,
    base_url="https://api.cerebras.ai/v1"
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 🔥 FIX SLASH COMMANDS (IMPORTANTE)
tree = discord.app_commands.CommandTree(client)

# =========================
# 📊 STATS
# =========================

def cargar_stats():
    try:
        with open("data/stats.json", "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}

def guardar_stats(stats):
    with open("data/stats.json", "w") as f:
        json.dump(stats, f, indent=4)

def registrar_error(codigo):
    stats = cargar_stats()
    stats[codigo] = stats.get(codigo, 0) + 1
    guardar_stats(stats)

# =========================
# 📄 EXCEL (MODO CAÓTICO)
# =========================

def cargar_excel():
    try:
        df = pd.read_excel("data/errores.xlsx", engine="openpyxl", header=None)
        df = df.dropna(how="all")  # eliminar filas vacías
        return df
    except Exception as e:
        print("ERROR EXCEL:", e)
        return None

excel_data = cargar_excel()

def buscar_en_excel(texto):
    if excel_data is None:
        return None

    texto = str(texto).lower()

    for _, row in excel_data.iterrows():
        fila = " ".join([str(x).lower() for x in row.values])

        if texto in fila:
            return row

    return None

def formatear_excel(row):
    respuesta = "📄 **Información oficial (NVIDIA):**\n\n"

    contenido = []

    for valor in row.values:
        v = str(valor).strip()
        if v and v.lower() != "nan":
            contenido.append(v)

    # limpiar duplicados
    contenido = list(dict.fromkeys(contenido))

    for linea in contenido[:6]:  # limitar spam
        respuesta += f"• {linea}\n"

    return respuesta

# =========================
# 🧠 IA
# =========================

def analizar_con_ia(texto):
    try:
        response = client_ai.chat.completions.create(
            model="llama3.1-8b",
            messages=[{
                "role": "user",
                "content": f"""
                Problema en GeForce NOW: {texto}

                Responde en español:

                Resumen:
                ...

                Soluciones:
                - ...
                - ...
                - ...
                """
            }],
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        print("ERROR IA:", e)
        return "⚠️ No pude obtener información."

# =========================
# 🔍 DETECCIÓN
# =========================

def detectar_codigo(texto):
    texto = texto.lower()

    match = re.search(r'0x[0-9a-f]+', texto)
    if match:
        return match.group()

    match = re.search(r'\b[0-9]{4,}[a-z0-9]*\b', texto)
    if match:
        return match.group()

    return None

def es_problema(texto):
    palabras = [
        "error", "problema", "no funciona", "no inicia",
        "pantalla negra", "lag", "borroso", "crash",
        "se cierra", "no carga"
    ]
    return any(p in texto.lower() for p in palabras)

# =========================
# 🚀 READY
# =========================

@client.event
async def on_ready():
    try:
        await tree.sync()
        print("✅ Slash commands sincronizados")
    except Exception as e:
        print("ERROR SYNC:", e)

    print(f"✅ Bot listo como {client.user}")

# =========================
# 💬 MENSAJES
# =========================

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # detectar canal o foro
    es_foro = (
        isinstance(message.channel, discord.Thread) and
        message.channel.parent_id == FORO_TECNICO_ID
    )

    es_canal = message.channel.id == CANAL_RAPIDO_ID

    if not (es_foro or es_canal):
        return

    contenido = message.content.strip()

    if len(contenido) < 8:
        return

    codigo = detectar_codigo(contenido)

    # hilo sin info
    if es_foro and message.id == message.channel.id:
        if not codigo and not es_problema(contenido):
            await message.channel.send(
                f"{message.author.mention} ⚠️ Describe mejor el problema o incluye un error."
            )
        return

    if not codigo and not es_problema(contenido):
        return

    # evitar duplicados
    async for msg in message.channel.history(limit=30):
        if msg.author == client.user and codigo and codigo in msg.content:
            return

    # 📄 BUSCAR EN EXCEL
    excel_resultado = buscar_en_excel(codigo if codigo else contenido)

    if excel_resultado is not None:
        if codigo:
            registrar_error(codigo)

        respuesta = f"🔎 **Consulta:** {codigo if codigo else 'General'}\n\n"
        respuesta += formatear_excel(excel_resultado)

        await message.channel.send(respuesta)
        return

    # 🧠 IA
    msg_temp = await message.channel.send("🔍 Analizando...")

    ia = analizar_con_ia(codigo if codigo else contenido)

    if codigo:
        registrar_error(codigo)

    stats = cargar_stats()
    cantidad = stats.get(codigo, 0) if codigo else 0

    respuesta = f"🔎 **Consulta:** {codigo if codigo else 'General'}\n\n{ia}"

    if codigo:
        respuesta += f"\n\n📊 Consultas: {cantidad}"

    await msg_temp.edit(content=respuesta)

# =========================
# 🛠️ MOD COMMANDS
# =========================

def es_mod(user):
    return any(role.id == ROL_MOD_ID for role in user.roles)

@tree.command(name="feedback", description="Lista de errores")
async def feedback(interaction: discord.Interaction):

    if not es_mod(interaction.user):
        await interaction.response.send_message("❌ Sin permisos", ephemeral=True)
        return

    stats = cargar_stats()

    if not stats:
        await interaction.response.send_message("No hay datos", ephemeral=True)
        return

    lista = "\n".join([f"{k}" for k in stats.keys()])

    await interaction.response.send_message(
        f"📊 **Errores registrados:**\n{lista}",
        ephemeral=True
    )

@tree.command(name="errorinfo", description="Cantidad de un error")
async def errorinfo(interaction: discord.Interaction, codigo: str):

    if not es_mod(interaction.user):
        await interaction.response.send_message("❌ Sin permisos", ephemeral=True)
        return

    stats = cargar_stats()
    cantidad = stats.get(codigo.lower(), 0)

    await interaction.response.send_message(
        f"🔎 {codigo} → {cantidad}",
        ephemeral=True
    )

# =========================
# 🚀 START
# =========================

import time
time.sleep(2)

client.run(TOKEN)
