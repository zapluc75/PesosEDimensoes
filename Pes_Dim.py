from colorama import Fore, Style
import pandas as pd

Tabela = pd.read_csv("Caminhoes.csv")

while True:
    tipo = input('Entre com o Tipo de Caminhão: ').upper()
    if tipo in Tabela["Codigo"].values:
        try:
            qt_tara = int(input(f'Quantidade de Tara(s): '))
            taras = []
            placas = []

            for i in range(qt_tara):
                placa = input(f'Placa {i + 1}: ').upper()
                tara = float(input(f'Tara {i + 1} (Kg): '))
                placas.append(placa)
                taras.append(tara)

            nota_fiscal = int(input('Peso Líquido da Nota Fiscal: '))
            comprimento = float(input('Comprimento do Caminhão (em metros): '))
        except ValueError:
            print("❌ Valor inválido. Use apenas números.")
            continue

        pbt = sum(taras) + nota_fiscal
        linha = Tabela[Tabela["Codigo"] == tipo].iloc[0]
        CompMx = linha["Tamax"]
        AET = linha["AET"]
        OBS = linha["OBS"]
        limite = linha["Pbt1"] if comprimento <= linha["Tam"] else linha["Pbt2"]
        excesso = max(0, pbt - limite)

        print('-' * 50)
        print(f'{"Listagem de Medidas":^40}')
        print('-' * 50)
        print("Resumo das Placas e Taras:")
        for p, t in zip(placas, taras):
            print(f' - Placa: {p} | Tara: {t} Kg')
        print(f'Total da(s) Tara(s): {sum(taras):.>10.2f} Kg')
        print(f'Peso constante na Nota Fiscal: {nota_fiscal:.>10.2f} Kg')
        print(f'Peso Bruto Total (PBT): {pbt:.>10.2f} Kg')

        print('-' * 50)
        if excesso > 0:
            print(f'{Fore.RED}⚠️ Excesso de Peso: {excesso:.2f} Kg{Style.RESET_ALL}')
        else:
            print('✅ Peso dentro do limite.')

        print('-' * 50)
        print(f'Resumo dos limites do Caminhão classe {tipo}')
        print(f' - PBT: {limite:.>0.2f} Kg | Compr. Max.: {CompMx:.>0.0f} Metros.')
        print(f' - {AET} necessita de AET | Observação: {OBS}\n')

        if input('Deseja continuar? [S/N]: ').strip().upper() != 'S':
            break
    else:
        print("Tipo de veículo não encontrado.")

