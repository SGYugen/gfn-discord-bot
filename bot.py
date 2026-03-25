import discord
import os
import requests
import json
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# 🔒 CONFIGURACIÓN
FORO_TECNICO_ID = 1486483140271931495
ROL_MOD_ID = 1486483938665959596

# IA
client_ai = OpenAI(
    api_key=CEREBRAS_API_KEY,
    base_url="https://api.cerebras.ai/v1"
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

tree = discord.app_commands.CommandTree(client)

# =========================
# 📊 STATS
# =========================

def cargar_stats():
    try:
        with open("data/stats.json", "r") as f:
            return json.load(f)
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
# 🧠 IA
# =========================

def analizar_con_ia(codigo):
    try:
        response = client_ai.chat.completions.create(
            model="llama3.1-8b",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    El error {codigo} es de GeForce NOW.

                    Responde en español:

                    Resumen:
                    ...

                    Soluciones:
                    - ...
                    - ...
                    """
                }
            ],
            max_tokens=300
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
    for palabra in texto.split():
        if palabra.startswith("0x") or any(c.isdigit() for c in palabra):
            return palabra
    return None

# =========================
# 🚀 READY
# =========================

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot listo como {client.user}")

# =========================
# 💬 MENSAJES
# =========================

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # 🔒 Solo foro técnico
    if not (
        isinstance(message.channel, discord.Thread) and
        message.channel.parent_id == FORO_TECNICO_ID
    ):
        return

    contenido = message.content
    codigo = detectar_codigo(contenido)

    # 🧵 MENSAJE INICIAL DEL HILO
    if message.id == message.channel.id:
        if not codigo:
            await message.channel.send(
                f"{message.author.mention} ⚠️ Por favor incluye un código de error o describe el problema técnico."
            )
        return

    # ❌ si no hay código ni contexto
    if not codigo and len(contenido) < 10:
        return

    # 🔁 evitar repetir misma respuesta en el hilo
    async for msg in message.channel.history(limit=50):
        if msg.author == client.user and codigo and codigo in msg.content:
            return

    # 📊 registrar
    if codigo:
        registrar_error(codigo)

    await message.channel.send(f"🔍 Analizando...")

    ia = analizar_con_ia(codigo if codigo else contenido)

    stats = cargar_stats()
    cantidad = stats.get(codigo, 0) if codigo else 0

    respuesta = f"🔎 **Consulta:** {codigo if codigo else 'General'}\n\n{ia}"

    if codigo:
        respuesta += f"\n\n📊 Consultas: {cantidad}"

    await message.channel.send(respuesta)

# =========================
# 🛠️ COMANDOS MOD
# =========================

def es_mod(user):
    return any(role.id == ROL_MOD_ID for role in user.roles)

@tree.command(name="feedback", description="Lista de errores registrados")
async def feedback(interaction: discord.Interaction):

    if not es_mod(interaction.user):
        await interaction.response.send_message(
            "❌ No tienes permisos.",
            ephemeral=True
        )
        return

    stats = cargar_stats()

    if not stats:
        await interaction.response.send_message("No hay datos.", ephemeral=True)
        return

    lista = "\n".join(stats.keys())

    await interaction.response.send_message(
        f"📊 **Errores registrados:**\n{lista}",
        ephemeral=True
    )

@tree.command(name="errorinfo", description="Cantidad de consultas de un error")
async def errorinfo(interaction: discord.Interaction, codigo: str):

    if not es_mod(interaction.user):
        await interaction.response.send_message(
            "❌ No tienes permisos.",
            ephemeral=True
        )
        return

    stats = cargar_stats()
    cantidad = stats.get(codigo.lower(), 0)

    await interaction.response.send_message(
        f"🔎 {codigo} | Cantidad: {cantidad}",
        ephemeral=True
    )

client.run(TOKEN)
