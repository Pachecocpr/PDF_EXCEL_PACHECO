import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Conversor de Patrimônio", layout="wide")

st.title("📂 Extrator de Dados de Patrimônio")
st.markdown("Faça o upload do PDF para gerar a planilha Excel automaticamente.")

# Upload do arquivo
uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

def processar_pdf(file):
    dados_finais = []
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            
            linhas = texto.split('\n')
            for linha in linhas:
                partes = linha.split()
                # Verifica se a linha começa com o número do ITEM
                if partes and partes[0].isdigit() and len(partes) > 3:
                    try:
                        item = partes[0]
                        pib = partes[1]
                        texto_linha = " ".join(partes)
                        
                        if "ATIVO" in texto_linha:
                            inicio_desc = texto_linha.find(pib) + len(pib)
                            fim_desc = texto_linha.find("ATIVO")
                            
                            descricao = texto_linha[inicio_desc:fim_desc].strip()
                            situacao = "ATIVO"
                            
                            # Pega o valor que vem após "ATIVO"
                            resto = texto_linha[fim_desc + 5:].strip().split()
                            valor = resto[0] if resto else ""
                            
                            dados_finais.append({
                                "ITEM": item,
                                "PIB": pib,
                                "DESCRIÇÃO DO BEM": descricao,
                                "SITUAÇÃO DO BEM": situacao,
                                "VALOR": valor
                            })
                    except:
                        continue
    return pd.DataFrame(dados_finais)

if uploaded_file is not None:
    df = processar_pdf(uploaded_file)
    
    if not df.empty:
        st.success(f"Encontrados {len(df)} itens!")
        st.dataframe(df, use_container_width=True)
        
        # Botão para baixar Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Baixar Planilha Excel",
            data=output.getvalue(),
            file_name="patrimonio_extraido.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Não foi possível extrair dados. Verifique o formato do PDF.")
