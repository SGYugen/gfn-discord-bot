import discord
import os
import json
import re
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

FORO_TECNICO_ID = 1486483140271931495
CANAL_RAPIDO_ID = 1486499974119166012  # CAMBIAR
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
# 📄 JSON DATA
# =========================

def cargar_errores():
    try:
        with open("data/errores.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

errores_data = cargar_errores()

def buscar_error(texto):
    texto = texto.lower()

    mejor = None
    score_max = 0

    for item in errores_data:
        contenido = " ".join(item.values()).lower()

        score = sum(1 for palabra in texto.split() if palabra in contenido)

        if score > score_max:
            score_max = score
            mejor = item

    return mejor if score_max > 1 else None

def formatear_json(item):
    texto = "📄 **Información oficial (NVIDIA):**\n\n"

    for k, v in item.items():
        texto += f"**{k}:** {v}\n"

    return texto

# =========================
# 🧠 IA
# =========================

def analizar_con_ia(texto, contexto=None):
    try:
        prompt = f"Problema en GeForce NOW: {texto}\n"

        if contexto:
            prompt += f"\nInformación oficial:\n{contexto}\n"

        prompt += """
        Responde en español:

        Resumen:
        ...

        Soluciones:
        - ...
        - ...
        - ...
        """

        response = client_ai.chat.completions.create(
            model="llama3.1-8b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )

        return response.choices[0].message.content

    except:
        return "⚠️ No pude obtener información."

# =========================
# 🔍 DETECCIÓN
# =========================

def detectar_codigo(texto):
    match = re.search(r'0x[0-9a-f]+', texto.lower())
    return match.group() if match else None

def es_problema(texto):
    palabras = ["error", "problema", "no funciona", "lag", "crash", "borroso"]
    return any(p in texto.lower() for p in palabras)

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

    es_foro = (
        isinstance(message.channel, discord.Thread) and
        message.channel.parent and
        message.channel.parent.id == FORO_TECNICO_ID
    )

    es_canal = message.channel.id == CANAL_RAPIDO_ID

    if not (es_foro or es_canal):
        return

    contenido = message.content.strip()

    if len(contenido) < 4:
        return

    codigo = detectar_codigo(contenido)

    if not codigo and not es_problema(contenido):
        return

    await message.channel.send("🔍 Analizando...")

    resultado = buscar_error(contenido)

    contexto = formatear_json(resultado) if resultado else None

    respuesta_ia = analizar_con_ia(contenido, contexto)

    if codigo:
        registrar_error(codigo)

    link = f"https://www.google.com/search?q=geforce+now+{contenido.replace(' ', '+')}"

    respuesta = f"🔎 **Consulta:** {codigo if codigo else 'General'}\n\n{respuesta_ia}"

    if contexto:
        respuesta += f"\n\n{contexto}"

    respuesta += f"\n🔗 {link}"

    await message.channel.send(respuesta)

# =========================
# 🛠️ COMANDOS
# =========================

def es_mod(user):
    return any(role.id == ROL_MOD_ID for role in user.roles)

@tree.command(name="errorinfo", description="Ver errores")
async def errorinfo(interaction: discord.Interaction):

    if not es_mod(interaction.user):
        await interaction.response.send_message("❌ Sin permisos", ephemeral=True)
        return

    stats = cargar_stats()

    texto = "\n".join([f"{k} → {v}" for k, v in stats.items()])

    await interaction.response.send_message(
        f"📊 **Errores:**\n{texto}",
        ephemeral=True
    )

client.run(TOKEN)
