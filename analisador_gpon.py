import pandas as pd

print("\n===== ANALISADOR GPON =====")

tipo_problema = input(
"""O que você quer verificar?

1 - Primárias com sinal ruim
2 - Clientes com problema isolado

Escolha: """)

while tipo_problema not in ["1", "2"]:
    print("Escolha inválida. Digite 1 ou 2.")
    tipo_problema = input("Escolha: ")

tipo_sinal = input(
"""
Qual sinal deseja analisar?

1 - RX
2 - TX

Escolha: """)

while tipo_sinal not in ["1", "2"]:
    print("Escolha inválida. Digite 1 ou 2.")
    tipo_sinal = input("Escolha: ")

# definição de arquivos

if tipo_sinal == "1":
    arquivo = "relatorio_rx.csv"
    coluna_sinal = "Sinal RX"
else:
    arquivo = "relatorio_tx.csv"
    coluna_sinal = "Sinal TX"

# carregar dados

dados = pd.read_csv(arquivo, sep=";")

print("\nArquivo carregado com sucesso!\n")

lista_olts = dados["Transmissor"].dropna().unique().tolist()

estrutura_rede = {}

for olt in lista_olts:

    estrutura_rede[olt] = {}

    for placa in range(1, 17):

        for porta in range(0, 16):

            pon = f"0/{placa}/{porta}"

            estrutura_rede[olt][pon] = []

# associar clientes

for index, linha in dados.iterrows():

    olt = linha["Transmissor"]
    pon = linha["PON ID"]
    cliente = linha["Nome"]
    sn = linha["MAC/Serial"]

    sinal = float(linha[coluna_sinal])

    if olt in estrutura_rede and pon in estrutura_rede[olt]:

        estrutura_rede[olt][pon].append({
            "cliente": cliente,
            "sn": sn,
            "sinal": sinal
        })

# analisar pons

pon_problema = {}

for olt in estrutura_rede:

    for pon in estrutura_rede[olt]:

        lista_clientes = estrutura_rede[olt][pon]

        if len(lista_clientes) > 0:

            pior_sinal = min(cliente["sinal"] for cliente in lista_clientes)

            chave = (olt, pon)

            pon_problema[chave] = pior_sinal

# ordenar pons pelo pior sinal

ranking = sorted(pon_problema.items(), key=lambda x: x[1])

top_ranking = ranking[:20]

# gerar relatório

relatorio = []

if tipo_problema == "2":
    relatorio.append("PONs com POSSÍVEIS clientes isolados\n")
else:
    relatorio.append("PONs com PIORES sinais\n")

for (olt, pon), pior_sinal in top_ranking:

    relatorio.append(f"\nOLT: {olt} | PON: {pon} | Pior sinal: {pior_sinal}")

    clientes = estrutura_rede[olt][pon]

    clientes_ordenados = sorted(clientes, key=lambda x: x["sinal"])

    top_clientes = clientes_ordenados[:5]

    for cliente in top_clientes:

        relatorio.append(
            f"Cliente: {cliente['cliente']} | SN: {cliente['sn']} | Sinal: {cliente['sinal']}"
        )

# salvar relatório

with open("relatorio_gpon.txt", "w", encoding="utf-8") as f:

    for linha in relatorio:
        f.write(linha + "\n")

print("Relatório gerado com sucesso: relatorio_gpon.txt")