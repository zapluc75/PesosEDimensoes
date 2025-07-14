import pandas as pd
import streamlit as st
from datetime import datetime
import os
import re   #leitura placa veicular
import glob
tab1, tab2 , tab3 = st.tabs(["Cálculo", "Anexo da Resolução", "Pesquisa"])

# Função para carregar a tabela com cache
@st.cache_data
def carregar_tabela(nome_arquivo):
    return pd.read_csv(nome_arquivo)

# Função para leitura de placa Normal ou Mercosul
def validar_placa(placa: str) -> bool:
    """
    Valida se a placa está no formato:
    - Antigo: ABC1234
    - Mercosul: ABC1D23
    """
    padrao = r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$'
    return re.fullmatch(padrao, placa.upper()) is not None

# Função para calcular excesso
def calcular_excesso(linha, taras, nota_fiscal, comprimento):
    pbt = sum(taras) + nota_fiscal
    limite = linha["Pbt1"] if comprimento <= linha["Tam"] else linha["Pbt2"]
    excesso = max(0, pbt - limite)
    return pbt, limite, excesso

# Função para Salvar Resultado
def salvar_csv(dados, nome_arquivo="resultados.csv"):
    df = pd.DataFrame([dados])

    if os.path.exists(nome_arquivo):
        df.to_csv(nome_arquivo, mode='a', header=False, index=False)
    else:
        df.to_csv(nome_arquivo, index=False)

#Função para limpar o estado
def limpar_estado():
    for chave in list(st.session_state.keys()):
        st.write(f"Removendo chave: {chave}")
        del st.session_state[chave]

#Preparação da barra lateral
st.sidebar.header("VEÍCULO")

# App Principal Streamlit
def main():
    with tab1:
        if st.session_state.get("encerrar", False):
            st.title("🚧 Aplicação finalizada.")
            st.info("Obrigado por utilizar o sistema.")
            st.stop()   #estrutura para finalizar tela
        st.title("📦 APURAÇÃO DE PESOS E DIMENSÕES - DER DF")
        
        tabela = carregar_tabela("Caminhoes.csv")
        tipo = st.sidebar.selectbox("Selecione o Tipo de Caminhão", tabela["Codigo"].unique(), key="tipo")
        linha = tabela[tabela["Codigo"] == tipo].iloc[0] # Define a quantidade de placas e taras a serem digitadas
        qt_tara = linha["Qtara"]
        placas = []
        taras = []

        nota_fiscal = st.sidebar.number_input("Peso Líquido da Nota Fiscal (Kg)", min_value=0, key="nota_fiscal")
        comprimento = st.sidebar.number_input("Comprimento do Caminhão (em metros)", min_value=0, key="comprimento")
        ano_atual = datetime.now().year
        fabricacao = st.sidebar.number_input("Ano de fabricação do caminhão",min_value=1950, max_value=ano_atual, step=1, key="fabricacao")
        nome_caminhao = linha["Nome"]
        st.sidebar.info(f"Tipo Selecionado: **{nome_caminhao}**")
    
        st.subheader("🚛 Informações de cada unidade (Placa + Tara)")
        for i in range(qt_tara): # Coleta os dados primeiro
            col1, col2 = st.columns(2)
            with col1:
                placa = st.text_input(f"Placa {i + 1} (Ex: ABC1234 ou ABC1D23)", key=f"placa_{i}").strip().upper()                       
            with col2:
                tara = st.number_input(f"Tara {i + 1} (Kg)", min_value=0.0, key=f"tara_{i}")
            placas.append(placa)
            taras.append(tara)
    
        if st.button("✅ Validar Placa(s)"): # Validação em lote
            for i in range(qt_tara):
                placa = placas[i]
    
                if len(placa) != 7:
                    st.error(f"❌ Placa {i + 1} inválida: Deve conter exatamente 7 caracteres.")
                elif not validar_placa(placa):
                    st.error(f"❌ Placa {i + 1} inválida: Use um dos formatos: ABC1234 ou ABC1D23.")
                else:
                    st.success(f"✅ Placa {i + 1} válida: {placa} | Tara: {taras[i]} Kg")
           
      
        if "calculado" not in st.session_state:
            st.session_state.calculado = False
    
        if st.button("Calcular"):
            if not all(placas) or any(t == 0 for t in taras) or nota_fiscal == 0:
                st.error("⚠️ Preencha com dados os campos: placa(s), tara(s), nota fiscal")
                st.button("🔁 Nova Apuração")
                                                 
            else:
                pbt, limite, excesso = calcular_excesso(linha, taras, nota_fiscal, comprimento)
    
            agora = datetime.now().strftime("%d-%m-%Y %H:%M:%S") #data e hora atual
    
            #preparar dados para exportação
            dados_exportar = {
                "DataHora": agora,
                "TipoCaminhao": tipo,
                "Placas": ";".join(placas),
                "TaraTotal": sum(taras),
                "NotaFiscal": nota_fiscal,
                "Comprimento": comprimento,
                "PBT": pbt,
                "LimiteLegal": limite,
                "Excesso": excesso,
                "Fabricacao": fabricacao
            }
    
            salvar_csv(dados_exportar)
    
            st.session_state.calculado = True
            st.session_state.resultado = {
                "tipo": tipo, "limite": limite, "taras": taras, "placas": placas,
                "nota_fiscal": nota_fiscal, "comprimento": comprimento,
                "pbt": pbt, "excesso": excesso, "linha": linha, "fabricacao": fabricacao
            }
    
            st.rerun()
    
    # Exibir resultados, se já calculado
        if st.session_state.calculado:
            r = st.session_state.resultado
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 INFORMAÇÕES ")
        
                st.markdown(f"""
                - ***Classe do Caminhão:*** `{r["tipo"]}`  
                - **Comprimento Máx. Permitido:**. `{r["linha"]["Tamax"]:.0f}` m  
                - **Autorização AET:**.. `{r["linha"]["AET"]}`  
                - **Observação:**....... `{r["linha"]["OBS"]}`  
                """)
                if comprimento <= r["linha"]["Tam"]:
                    st.markdown(f"- *Comprimento inferior a* `{r["linha"]["Tam"]:.0f}`m - PBT `{r["linha"]["Pbt1"]}` Kg")
                else:
                    st.markdown(f"- *Comprimento Superior a* `{r["linha"]["Tam"]:.0f}`m - PBT `{r["linha"]["Pbt2"]}` Kg")
            with col2:
                st.markdown("### ✅ Resultado da Apuração")
                for p, t in zip(r["placas"], r["taras"]):
                    st.write(f" - Placa: `{p}` | Tara: `{t:.2f}` Kg")
        
                st.markdown(f"""
                - **Somatório de Tara(s):**`{sum(r["taras"]):.2f}` Kg  
                - **Peso Liquido da NF:**... `{r["nota_fiscal"]:.2f}` Kg  
                - **Peso Bruto Total (PBT):** ``{r["pbt"]:.2f}`` Kg  
                """)
    
            if r["excesso"] > 0:
                st.error(f"🚨 Excesso de Peso: **{r['excesso']:.2f} Kg.** 📁 Dados salvos com sucesso !")
                st.balloons ()
            else:
                st.success("✅ Peso dentro do limite. 📁 Dados salvos com sucesso !")
                st.balloons() 
            st.markdown("---")
            col1, col2 = st.columns(2)
            if col1.button("🔁 Nova Apuração"):
                limpar_estado()
                st.rerun()      
    
            if col2.button("❌ Encerrar"):
                st.session_state.encerrar = True
                st.rerun()
         
    with tab2:
        st.write("📄 Selecione o tipo de Caminhão")

        # lista de todos os arquivos jpgs da pasta imagens
        lista_jpgs = sorted(glob.glob(os.path.join("imagens", "*.jpg")))
        nomes_arquivos = [os.path.basename(f) for f in lista_jpgs]

        #Variável para armazenar seleção
        selecionado = None
        num_colunas = 6

        #Cria pares de elementos (2 por linha)
        for i in range(0, len(nomes_arquivos), num_colunas):
            cols = st.columns(num_colunas)

            for j in range (num_colunas):
                if i + j < len(nomes_arquivos):
                    with cols[j]:
                        if st.button(nomes_arquivos[i + j]):
                            selecionado = nomes_arquivos[i + j]
        if selecionado:
            caminho_img = os.path.join("imagens", selecionado)
            st.image(caminho_img, caption=selecionado, use_container_width=True)
    
    with tab3:
        st.write("📄 Pesquisa Avançada")

        # Carrega o CSV
        tabela = pd.read_csv("resultados.csv")

        # Converte a coluna de DataHora para datetime (se ainda não for)
        tabela["DataHora"] = pd.to_datetime(tabela["DataHora"], format="%d-%m-%Y %H:%M:%S")

        # Extrai dia e mês
        tabela["Dia"] = tabela["DataHora"].dt.day
        tabela["Mes"] = tabela["DataHora"].dt.month

        st.title("Consulta de Pesagens por Dia e Mês")

        # Interface para escolha do mês e do dia
        meses = sorted(tabela["Mes"].unique())
        mes_escolhido = st.selectbox("Selecione o mês:", meses)

        # Após o mês, filtra os dias disponíveis naquele mês
        dias_disponiveis = sorted(tabela[tabela["Mes"] == mes_escolhido]["Dia"].unique())
        dia_escolhido = st.selectbox("Selecione o dia:", dias_disponiveis)

        # Aplica o filtro
        filtro = (tabela["Mes"] == mes_escolhido) & (tabela["Dia"] == dia_escolhido)
        dados_filtrados = tabela[filtro]

        # Exibe a tabela com os campos desejados
        st.subheader(f"Resultados para {dia_escolhido:02d}/{mes_escolhido:02d}")
        colunas_desejadas = ["DataHora", "TipoCaminhao", "Placas", "TaraTotal", "NotaFiscal", "Comprimento", "PBT",
                             "LimiteLegal", "Excesso"]
        st.dataframe(dados_filtrados[colunas_desejadas].reset_index(drop=True))
if __name__ == "__main__":
    main()
