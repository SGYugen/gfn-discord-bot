import requests
import re
import json

WEBHOOK = "TU_WEBHOOK_DISCORD"

URL = "https://www.reddit.com/r/GeForceNOW/new.json?limit=10"
HEADERS = {"User-Agent": "gfn-bot"}

response = requests.get(URL, headers=HEADERS)
data = response.json()

with open("data/errors.json", "r") as f:
    errors = json.load(f)

with open("data/detected_errors.json", "r") as f:
    detected = json.load(f)

def enviar_discord(msg):
    requests.post(WEBHOOK, json={"content": msg})

for post in data["data"]["children"]:
    texto = post["data"]["title"] + " " + post["data"].get("selftext", "")

    codigos = re.findall(r'0x[a-fA-F0-9]+', texto)

    for codigo in codigos:
        if codigo not in errors and codigo not in detected:

            mensaje = f"""🚨 **Nuevo error detectado**
Código: {codigo}
Origen: Reddit (GeForceNOW)

⚠️ Aún sin solución documentada"""

            enviar_discord(mensaje)

            detected.append(codigo)

with open("data/detected_errors.json", "w") as f:
    json.dump(detected, f, indent=2)
