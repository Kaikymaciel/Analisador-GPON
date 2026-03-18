import pandas as pd

print("\n===== ANALISADOR GPON =====")

# essas são as perguntas que são feitas ao usuário para exibir as informações de forma personalizada

tipo_problema = input(
"""O que você quer verificar?

1 - Primárias com sinal ruim
2 - Clientes com problema isolado


Escolha: """)

tipo_sinal = input(
"""
Qual sinal deseja analisar?

1 - RX
2 - TX

Escolha: """)

limite_sinal = float(input("\nDigite o limite de sinal (ex: -27): "))

quantidade_ranking = int(input("\nQuantas PONs deseja verificar? "))

quantidade_clientes = int(input("Quantos clientes deseja exibir por PON? "))

#Aqui estamos definindo os arquivos que vão ser analisados e definimos as colunas

if tipo_sinal == "1":
    arquivo = "relatorio_rx.csv"
    coluna_sinal = "Sinal RX"
    chave_sinal = "rx"
else: 
    arquivo = "relatorio_tx.csv"
    coluna_sinal = "Sinal TX"
    chave_sinal = "tx"

#apos o arquivo ser selecionado ele é carregado 

dados = pd.read_csv(arquivo, sep=";")

print("\nArquivo carregado com sucesso!\n")

#Esse comando cria a lista de olts

lista_olts = dados["Transmissor"].dropna().unique().tolist()

#Aqui definimos a estrutura da rede

estrutura_rede = {}

for olt in lista_olts:

    estrutura_rede[olt] = {}

    for placa in range(1, 17):

        for porta in range(0, 16):

            pon = f"0/{placa}/{porta}"

            estrutura_rede[olt][pon] = []

#associando clientes às pons

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

#analisar pons

pon_problema = {}

for olt in estrutura_rede:

    for pon in estrutura_rede[olt]:

        clientes_ruins = 0   # inicia contador da PON

        for cliente in estrutura_rede[olt][pon]:

            if cliente["sinal"] <= limite_sinal:

                clientes_ruins += 1
        
        if clientes_ruins > 0:
         
            chave = (olt, pon)

            pon_problema[chave] = clientes_ruins

#filtrar resultados 

if tipo_problema == "2":

    #cliente isolados
    pon_problema = {
        chave: valor for chave, valor in pon_problema.items() if valor <= 3
    }

    ranking = sorted(pon_problema.items(), key=lambda x: x[1])

    print("\nRanking de PONs com problemas ISOLADOS:\n")

else:

    ranking = sorted(pon_problema.items(), key=lambda x: x[1], reverse=True)

    print("\nRanking de PONs com MAIS clientes com sinal ruim:\n")

top_ranking = ranking[:quantidade_ranking]

#Mostrar rankig

for (olt, pon), total in top_ranking:

    print(f"OLT: {olt} | PON: {pon} | Clientes com sinal ruim: {total}")

print("\nClientes com piores sinais:\n")

#Mostrar clientes

for (olt, pon), total in top_ranking:

    print(f"\nOLT: {olt} | PON: {pon}")

    clientes_ruins_lista = []

    for cliente in estrutura_rede[olt][pon]:

        if cliente ["sinal"] <= limite_sinal:

            clientes_ruins_lista.append(cliente)

#ordenar pelo pior sinal  
    clientes_ruins_lista = sorted(clientes_ruins_lista, key=lambda x: x["sinal"])

    piores = clientes_ruins_lista[:quantidade_clientes]

    for cliente in piores:

        print(
            f"Cliente: {cliente['cliente']} | SN: {cliente['sn']} | Sinal: {cliente['sinal']}"
        )