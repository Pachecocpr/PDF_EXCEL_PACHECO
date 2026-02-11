import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Extrator Patrimonial Pro", layout="wide")

st.title("📂 PDF/EXCEL")
st.markdown("Extração completa.")

uploaded_file = st.file_uploader("Upload do PDF", type="pdf")

def processar_pdf(file):
    dados_finais = []
    
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            
            linhas = texto.split('\n')
            for linha in linhas:
                partes = linha.split()
                
                # Identifica se a linha começa com o número do ITEM
                if partes and partes[0].isdigit() and "ATIVO" in linha:
                    try:
                        item = partes[0]
                        pib = partes[1]
                        
                        # O Valor é sempre o último elemento
                        valor = partes[-1]
                        
                        # Localizar a posição do "ATIVO" para dividir a linha
                        texto_linha = " ".join(partes)
                        idx_pib = texto_linha.find(pib) + len(pib)
                        idx_ativo = texto_linha.find("ATIVO")
                        
                        # 1. PARTE ANTES DO ATIVO (Descrição, Contrato, Série)
                        parte_antes = texto_linha[idx_pib:idx_ativo].strip()
                        
                        # Tentamos capturar o Contrato/AF (Padrão: 00/0000 ou similar)
                        match_contrato = re.search(r'(\d{2,}/\d{4})', parte_antes)
                        if match_contrato:
                            contrato = match_contrato.group(1)
                            # Descrição é tudo antes do contrato
                            descricao = parte_antes[:match_contrato.start()].strip()
                            # Série é o que sobra entre contrato e ATIVO
                            serie = parte_antes[match_contrato.end():].strip()
                        else:
                            contrato = ""
                            descricao = parte_antes
                            serie = ""

                        # 2. PARTE DEPOIS DO ATIVO (Usuário e Valor)
                        # Pegamos o texto entre "ATIVO" e o "Valor" final
                        parte_depois = texto_linha[idx_ativo + 5 : texto_linha.rfind(valor)].strip()
                        usuario = parte_depois
                        
                        dados_finais.append({
                            "ITEM": item,
                            "PIB": pib,
                            "DESCRIÇÃO DO BEM": descricao,
                            "CONTRATO/AF": contrato,
                            "NÚMERO DE SÉRIE": serie,
                            "SITUAÇÃO DO BEM": "ATIVO",
                            "NOME DO USUÁRIO": usuario,
                            "VALOR": valor
                        })
                    except:
                        continue
    return pd.DataFrame(dados_finais)

if uploaded_file is not None:
    df = processar_pdf(uploaded_file)
    if not df.empty:
        st.success(f"Foram extraídos {len(df)} itens com todas as colunas!")
        st.dataframe(df, use_container_width=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Baixar Planilha Excel Completa",
            data=output.getvalue(),
            file_name="patrimonio_detalhado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

