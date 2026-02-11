import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Extrator de Patrimônio", layout="wide")

st.title("📂 Extrator de Dados com Usuário")
st.markdown("Extração de Item, PIB, Descrição, Usuário, Situação e Valor.")

uploaded_file = st.file_uploader("Arraste o PDF aqui", type="pdf")

def processar_pdf(file):
    dados_finais = []
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            
            linhas = texto.split('\n')
            for i, linha in enumerate(linhas):
                partes = linha.split()
                
                # Identifica a linha principal pelo número do ITEM
                if partes and partes[0].isdigit() and len(partes) > 5:
                    try:
                        item = partes[0]
                        pib = partes[1]
                        texto_completo = " ".join(partes)
                        
                        if "ATIVO" in texto_completo:
                            # 1. Extrair Situação
                            situacao = "ATIVO"
                            
                            # 2. Extrair Valor (último elemento numérico da linha)
                            valor = partes[-1]
                            
                            # 3. Extrair Descrição e Usuário
                            # Lógica: O usuário no seu PDF geralmente vem após a descrição 
                            # e antes da palavra ATIVO, ou na linha imediatamente abaixo.
                            inicio_desc = texto_completo.find(pib) + len(pib)
                            fim_dados = texto_completo.find("ATIVO")
                            
                            miolo = texto_completo[inicio_desc:fim_dados].strip()
                            
                            # No seu PDF, o nome do usuário/setor costuma estar no final do 'miolo'
                            # Vamos tentar separar a descrição do nome (geralmente em MAIÚSCULAS no final)
                            partes_miolo = miolo.split("  ") # Tenta identificar espaços duplos
                            if len(partes_miolo) > 1:
                                descricao = partes_miolo[0].strip()
                                usuario = partes_miolo[-1].strip()
                            else:
                                # Caso não haja espaço duplo, pegamos as últimas palavras
                                p_m = miolo.split()
                                usuario = " ".join(p_m[-2:]) # Pega as últimas 2 palavras como usuário
                                descricao = " ".join(p_m[:-2])
                            
                            dados_finais.append({
                                "ITEM": item,
                                "PIB": pib,
                                "DESCRIÇÃO DO BEM": descricao,
                                "USUÁRIO": usuario,
                                "SITUAÇÃO DO BEM": situacao,
                                "VALOR": valor
                            })
                    except:
                        continue
    return pd.DataFrame(dados_finais)

if uploaded_file is not None:
    df = processar_pdf(uploaded_file)
    if not df.empty:
        st.success(f"Sucesso! {len(df)} itens processados.")
        st.dataframe(df, use_container_width=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Baixar Excel com Usuários",
            data=output.getvalue(),
            file_name="patrimonio_completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
