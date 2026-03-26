import pandas as pd
import json

df = pd.read_excel("data/errores.xlsx", engine="openpyxl")

df = df.fillna("")

data = []

for _, row in df.iterrows():
    fila = {}

    for col in df.columns:
        valor = str(row[col]).strip()
        if valor:
            fila[col] = valor

    data.append(fila)

with open("data/errores.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("✅ JSON generado")
