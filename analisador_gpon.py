import pandas as pd
import asyncio
import aiohttp
import json

print("\n===== ANALISADOR GPON =====")

# =========================
# INPUTS
# =========================

tipo_problema = input(
"""O que você quer verificar?

1 - Primárias com sinal ruim
2 - Clientes com problema isolado

Escolha: """)

while tipo_problema not in ["1", "2"]:
    tipo_problema = input("Escolha inválida. Digite 1 ou 2: ")

tipo_sinal = input(
"""
Qual sinal deseja analisar?

1 - RX
2 - TX

Escolha: """)

while tipo_sinal not in ["1", "2"]:
    tipo_sinal = input("Escolha inválida. Digite 1 ou 2: ")

# =========================
# ARQUIVO
# =========================

if tipo_sinal == "1":
    arquivo = "relatorio_rx.csv"
    coluna_sinal = "Sinal RX"
else:
    arquivo = "relatorio_tx.csv"
    coluna_sinal = "Sinal TX"

dados = pd.read_csv(arquivo, sep=";")
print("\nArquivo carregado com sucesso!\n")

# =========================
# AGRUPAR CLIENTES POR PON
# =========================

estrutura = {}

for _, linha in dados.iterrows():
    try:
        sinal = float(linha[coluna_sinal])
    except:
        continue

    chave = (linha["Transmissor"], linha["PON ID"])

    if chave not in estrutura:
        estrutura[chave] = []

    estrutura[chave].append({
        "cliente": linha["Nome"],
        "sn": linha["MAC/Serial"],
        "sinal": sinal
    })

# =========================
# RANKING (PIOR PRIMEIRO)
# =========================

ranking = sorted(
    [(chave, min(c["sinal"] for c in clientes))
     for chave, clientes in estrutura.items()],
    key=lambda x: x[1]
)

# =========================
# API (SÓ PRA PRIMÁRIA)
# =========================

async def consultar_media(session, olt, pon):
    url = "https://nmt.nmultifibra.com.br/monitoramento/optical-info"
    headers = {'Content-Type': 'application/json'}

    try:
        payload = json.dumps({"gpon": pon, "host": olt})

        async with session.post(
            url,
            headers=headers,
            data=payload,
            timeout=aiohttp.ClientTimeout(total=6)
        ) as resp:

            if resp.status != 200:
                return None

            data = await resp.json()

            if "median" not in data:
                return None

            if tipo_sinal == "1":
                return data["median"].get("rxPower")
            else:
                return data["median"].get("txPower")

    except:
        return None


async def coletar_medias(pons):
    medias = {}
    semaphore = asyncio.Semaphore(6)

    async with aiohttp.ClientSession() as session:

        async def task(olt, pon):
            async with semaphore:
                media = await consultar_media(session, olt, pon)
                return (olt, pon, media)

        tarefas = [task(olt, pon) for olt, pon in pons]
        resultados = await asyncio.gather(*tarefas)

        for olt, pon, media in resultados:
            if media is not None:
                medias[(olt, pon)] = media

    return medias

# =========================
# PROCESSAMENTO
# =========================

relatorio = []
contador = 0
limite = 20

# =========================
# CASO 1 - PRIMÁRIA
# =========================

if tipo_problema == "1":

    print("Consultando API (somente PONs com potencial de primária)...")

    # só consulta PONs com 5+ clientes
    pons_para_api = [
        chave for chave, clientes in estrutura.items()
        if len(clientes) >= 5
    ]

    medias_pons = asyncio.run(coletar_medias(pons_para_api))

    relatorio.append("PONs com PROBLEMA DE PRIMÁRIA\n")

    for (olt, pon), pior_sinal in ranking:

        if contador >= limite:
            break

        if (olt, pon) not in medias_pons:
            continue

        media = medias_pons[(olt, pon)]
        clientes = estrutura[(olt, pon)]

        if len(clientes) < 5:
            continue

        clientes_ordenados = sorted(clientes, key=lambda x: x["sinal"])
        top_clientes = clientes_ordenados[:5]

        # clientes próximos da média
        proximos = [
            c for c in top_clientes
            if abs(c["sinal"] - media) <= 2
        ]

        # regra de primária
        if media <= -25 and len(proximos) >= 3:

            relatorio.append(
                f"\nOLT: {olt} | PON: {pon} | Média: {media} | Pior: {pior_sinal}"
            )

            # 🔥 TODOS OS CLIENTES
            for c in clientes_ordenados:
                relatorio.append(
                    f"Cliente: {c['cliente']} | SN: {c['sn']} | Sinal: {c['sinal']}"
                )

            relatorio.append("\n")
            contador += 1

# =========================
# CASO 2 - ISOLADO
# =========================

else:

    relatorio.append("PONs com CLIENTES ISOLADOS\n")

    for (olt, pon), pior_sinal in ranking:

        if contador >= limite:
            break

        clientes = estrutura[(olt, pon)]

        # 🔥 REGRA SIMPLES E EFICIENTE
        if len(clientes) <= 4:

            clientes_ordenados = sorted(clientes, key=lambda x: x["sinal"])

            relatorio.append(
                f"\nOLT: {olt} | PON: {pon} | Pior: {pior_sinal}"
            )

            for c in clientes_ordenados:
                relatorio.append(
                    f"Cliente: {c['cliente']} | SN: {c['sn']} | Sinal: {c['sinal']}"
                )

            relatorio.append("\n")
            contador += 1

# =========================
# SALVAR
# =========================

with open("relatorio_gpon.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(relatorio))

print("\nRelatório gerado com sucesso! (Top 20)\n")