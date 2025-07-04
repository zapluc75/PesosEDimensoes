import pandas as pd
import streamlit as st

# Função para carregar a tabela CSV
@st.cache_data
def carregar_tabela(nome_arquivo):
    return pd.read_csv(nome_arquivo)

# Função para calcular excesso
def calcular_excesso(linha, taras, nota_fiscal, comprimento):
    pbt = sum(taras) + nota_fiscal
    limite = linha["Pbt1"] if comprimento <= linha["Tam"] else linha["Pbt2"]
    excesso = max(0, pbt - limite)
    return pbt, limite, excesso

#Preparação da barra lateral
st.sidebar.header("CALCULO DE PBT")

# App Streamlit
def main():
    st.title("📦 CÁLCULO DE PESO E DIMENSÕES - DER DF")
    
    tabela = carregar_tabela("Caminhoes.csv")

    tipo = st.sidebar.selectbox("Selecione o Tipo de Caminhão", tabela["Codigo"].unique())

    linha = tabela[tabela["Codigo"] == tipo].iloc[0]
    qt_tara = st.sidebar.number_input("Quantidade de Taras (número de unidades tracionadas)", min_value=1, max_value=10, step=1)

    placas = []
    taras = []

    st.subheader("🚛 Informações de cada unidade (Placa + Tara)")
    for i in range(qt_tara):
        col1, col2 = st.columns(2)
        with col1:
            placa = st.text_input(f"Placa {i + 1}", key=f"placa_{i}").upper()
        with col2:
            tara = st.number_input(f"Tara {i + 1} (Kg)", min_value=0.0, key=f"tara_{i}")
        placas.append(placa)
        taras.append(tara)

    nota_fiscal = st.sidebar.number_input("Peso Líquido da Nota Fiscal (Kg)", min_value=0)
    comprimento = st.sidebar.number_input("Comprimento do Caminhão (em metros)", min_value=0.0)

    if st.button("Calcular"):
        if not all(placas) or any(t == 0 for t in taras):
            st.error("⚠️ Preencha todas as placas e taras corretamente.")
            return

        pbt, limite, excesso = calcular_excesso(linha, taras, nota_fiscal, comprimento)

        st.markdown("---")
        st.subheader("📊 Resultado da Apuração")

        st.markdown(f"""
        - **Classe do Caminhão:** {tipo}  
        - **PBT Máximo Permitido:** `{limite:.2f}` Kg  
        - **Comprimento Máximo:** `{linha["Tamax"]:.0f}` m  
        - **AET Necessário:** `{linha["AET"]}`  
        - **Observação:** `{linha["OBS"]}`  
        """)

        st.markdown("### ✅ Resumo das Taras")
        for p, t in zip(placas, taras):
            st.write(f" - Placa: `{p}` | Tara: `{t:.2f}` Kg")

        st.markdown(f"""
        - **Total de Taras:** `{sum(taras):.2f}` Kg  
        - **Peso da Nota Fiscal:** `{nota_fiscal:.2f}` Kg  
        - **Peso Bruto Total (PBT):** `{pbt:.2f}` Kg  
        """)

        if excesso > 0:
            st.error(f"🚨 Excesso de Peso: **{excesso:.2f} Kg**")
        else:
            st.success("✅ Peso dentro do limite.")

if __name__ == "__main__":
    main()