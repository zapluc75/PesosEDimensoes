import pandas as pd
import streamlit as st
from datetime import datetime
import os
import re   #leitura placa veicular

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
    if st.session_state.get("encerrar", False):
        st.title("🚧 Aplicação finalizada.")
        st.info("Obrigado por utilizar o sistema.")
        st.stop()   #estrutura para finalizar tela
    st.title("📦 APURAÇÃO DE PESOS E DIMENSÕES - DER DF")
    
    tabela = carregar_tabela("Caminhoes.csv")

    tipo = st.sidebar.selectbox("Selecione o Tipo de Caminhão", tabela["Codigo"].unique(), key="tipo")

    linha = tabela[tabela["Codigo"] == tipo].iloc[0]
    # Define a quantidade de placas a serem digitadas
    qt_tara = st.sidebar.number_input("Quantidade de Taras (número de unidades tracionadas)", min_value=1, max_value=10, step=1, key="qt_tara")

    placas = []
    taras = []

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
       
    nota_fiscal = st.sidebar.number_input("Peso Líquido da Nota Fiscal (Kg)", min_value=0, key="nota_fiscal")
    comprimento = st.sidebar.number_input("Comprimento do Caminhão (em metros)", min_value=0, key="comprimento")
    pdf_path = "Pes_e_Dim.pdf"
    st.markdown(f'<a href="{pdf_path}" target="_blank">📂 Clique aqui para abrir o Anexo da Resolução</a>', unsafe_allow_html=True)
    
    if "calculado" not in st.session_state:
        st.session_state.calculado = False

    if st.button("Calcular"):
        if not all(placas) or any(t == 0 for t in taras):
            st.error("⚠️ Preencha todas as placas e taras corretamente.")
        else:
            pbt, limite, excesso = calcular_excesso(linha, taras, nota_fiscal, comprimento)

           #data e hora atual
        agora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

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
            "Excesso": excesso
        }

        salvar_csv(dados_exportar)

        st.session_state.calculado = True
        st.session_state.resultado = {
            "tipo": tipo, "limite": limite, "taras": taras, "placas": placas,
            "nota_fiscal": nota_fiscal, "comprimento": comprimento,
            "pbt": pbt, "excesso": excesso, "linha": linha
        }

        st.rerun()

# Exibir resultados, se já calculado
    if st.session_state.calculado:
        r = st.session_state.resultado
        st.markdown("---")
        st.subheader("📊 INFORMAÇÕES ")

        st.markdown(f"""
        - ***Classe do Caminhão:*** `{r["tipo"]}`  
        - **Comprimento Máx.:**. `{r["linha"]["Tamax"]:.0f}` m  
        - **Autorização AET:**.. `{r["linha"]["AET"]}`  
        - **Observação:**....... `{r["linha"]["OBS"]}`  
        - **PBT Máx. Permitido:**`{r["limite"]:.2f}` Kg 
        """)

        st.markdown("### ✅ Resultado da Apuração")
        for p, t in zip(r["placas"], r["taras"]):
            st.write(f" - Placa: `{p}` | Tara: `{t:.2f}` Kg")

        st.markdown(f"""
        - **Somatório de Tara(s):**`{sum(r["taras"]):.2f}` Kg  
        - **Peso Liquido da NF:**... `{r["nota_fiscal"]:.2f}` Kg  
        - *Peso Bruto Total (PBT):* `{r["pbt"]:.2f}` Kg  
        """)

        if r["excesso"] > 0:
            st.error(f"🚨 Excesso de Peso: **{r['excesso']:.2f} Kg.** 📁 Dados salvos com sucesso !")
        else:
            st.success("✅ Peso dentro do limite. 📁 Dados salvos com sucesso !")

        
        st.markdown("---")
        col1, col2 = st.columns(2)
        if col1.button("🔁 Nova Apuração"):
            limpar_estado()
            st.rerun()      

        if col2.button("❌ Encerrar"):
            st.session_state.encerrar = True
            st.rerun()


if __name__ == "__main__":
    main()