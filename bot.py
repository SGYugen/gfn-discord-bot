import discord
import os
import json
import re
import pandas as pd
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

FORO_TECNICO_ID = 1486483140271931495
CANAL_RAPIDO_ID = 1486499974119166012
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
# 📄 EXCEL INTELIGENTE
# =========================

def cargar_excel():
    try:
        df = pd.read_excel("data/errores.xlsx", engine="openpyxl", header=None)
        df = df.dropna(how="all")
        return df
    except:
        return None

excel_data = cargar_excel()

def buscar_en_excel(texto):
    if excel_data is None:
        return None

    texto = texto.lower()
    mejor_match = None
    score_max = 0

    for _, row in excel_data.iterrows():
        fila = " ".join([str(x).lower() for x in row.values])

        score = sum(1 for palabra in texto.split() if palabra in fila)

        if score > score_max:
            score_max = score
            mejor_match = row

    return mejor_match if score_max > 1 else None

def formatear_excel(row):
    contenido = []

    for valor in row.values:
        v = str(valor).strip()
        if v and v.lower() != "nan":
            contenido.append(v)

    contenido = list(dict.fromkeys(contenido))

    texto = "\n".join(contenido[:6])

    return texto

# =========================
# 🧠 IA
# =========================

def analizar_con_ia(texto, contexto_excel=None):
    try:
        prompt = f"""
        Problema en GeForce NOW: {texto}
        """

        if contexto_excel:
            prompt += f"\nInformación adicional:\n{contexto_excel}\n"

        prompt += """
        Responde en español:

        Resumen:
        ...

        Soluciones:
        - ...
        - ...
        - ...

        Si existe una solución clara, inclúyela.
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
    texto = texto.lower()

    match = re.search(r'0x[0-9a-f]+', texto)
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

    if len(contenido) < 5:
        return

    codigo = detectar_codigo(contenido)

    if es_foro and message.id == message.channel.id:
        if not codigo and not es_problema(contenido):
            await message.channel.send(
                f"{message.author.mention} ⚠️ Describe mejor el problema."
            )
        return

    if not codigo and not es_problema(contenido):
        return

    # evitar spam
    async for msg in message.channel.history(limit=20):
        if msg.author == client.user:
            return

    await message.channel.send("🔍 Analizando...")

    excel_resultado = buscar_en_excel(contenido)

    contexto_excel = formatear_excel(excel_resultado) if excel_resultado is not None else None

    respuesta_ia = analizar_con_ia(contenido, contexto_excel)

    if codigo:
        registrar_error(codigo)

    link_google = f"https://www.google.com/search?q=geforce+now+{contenido.replace(' ', '+')}"

    respuesta = f"🔎 **Consulta:** {codigo if codigo else 'General'}\n\n{respuesta_ia}"

    if contexto_excel:
        respuesta += f"\n\n📄 **Fuente NVIDIA:**\n{contexto_excel}"

    respuesta += f"\n\n🔗 Más info: {link_google}"

    await message.channel.send(respuesta)

# =========================
# 🛠️ COMANDOS
# =========================

def es_mod(user):
    return any(role.id == ROL_MOD_ID for role in user.roles)

class ErrorSelect(discord.ui.Select):
    def __init__(self, stats):
        options = [
            discord.SelectOption(label=k, description=f"Consultas: {v}")
            for k, v in list(stats.items())[:25]
        ]
        super().__init__(placeholder="Selecciona un error", options=options)
        self.stats = stats

    async def callback(self, interaction: discord.Interaction):
        codigo = self.values[0]
        cantidad = self.stats.get(codigo, 0)

        await interaction.response.send_message(
            f"🔎 {codigo} → {cantidad}",
            ephemeral=True
        )

class ErrorView(discord.ui.View):
    def __init__(self, stats):
        super().__init__()
        self.add_item(ErrorSelect(stats))

@tree.command(name="errorinfo", description="Ver errores con selector")
async def errorinfo(interaction: discord.Interaction):

    if not es_mod(interaction.user):
        await interaction.response.send_message("❌ Sin permisos", ephemeral=True)
        return

    stats = cargar_stats()

    if not stats:
        await interaction.response.send_message("No hay datos", ephemeral=True)
        return

    view = ErrorView(stats)

    await interaction.response.send_message(
        "📊 Selecciona un error:",
        view=view,
        ephemeral=True
    )

client.run(TOKEN)
