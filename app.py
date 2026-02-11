import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Extrator Completo de Patrimônio", layout="wide")

st.title("📂 Extrator de Patrimônio (Todas as Colunas)")
st.markdown("Este app remove os cabeçalhos e extrai Item, PIB, Descrição, Usuário, Situação e Valor.")

uploaded_file = st.file_uploader("Upload do arquivo PDF", type="pdf")

def processar_pdf(file):
    dados_finais = []
    
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            # Extraímos a tabela da página
            # O pdfplumber consegue ignorar o cabeçalho se focarmos nas linhas que começam com números
            linhas = pagina.extract_text().split('\n')
            
            for linha in linhas:
                partes = linha.split()
                
                # Regra: A linha de dados válida sempre começa com o número do ITEM (numérico)
                # E ignoramos linhas que contenham "Relatório", "Emissão" ou "Página" (cabeçalhos)
                if partes and partes[0].isdigit() and len(partes) > 4:
                    try:
                        item = partes[0]
                        pib = partes[1]
                        valor = partes[-1]  # O valor é sempre o último elemento
                        situacao = "ATIVO" if "ATIVO" in linha else ""
                        
                        # Extração do Meio (Descrição + Usuário)
                        # Pegamos tudo que está entre o PIB e a palavra ATIVO
                        texto_linha = " ".join(partes)
                        inicio_meio = texto_linha.find(pib) + len(pib)
                        fim_meio = texto_linha.find("ATIVO")
                        
                        conteudo_meio = texto_linha[inicio_meio:fim_meio].strip()
                        
                        # No seu PDF, o Usuário/Localização está separado da Descrição por espaços longos
                        # Se não houver espaço longo, tentamos separar pelas últimas palavras maiúsculas
                        if "  " in conteudo_meio:
                            sub_partes = conteudo_meio.split("  ")
                            descricao = sub_partes[0].strip()
                            usuario = sub_partes[-1].strip()
                        else:
                            # Fallback: assume que as últimas 3 palavras são o usuário/setor
                            p_meio = conteudo_meio.split()
                            descricao = " ".join(p_meio[:-3])
                            usuario = " ".join(p_meio[-3:])

                        dados_finais.append({
                            "ITEM": item,
                            "PIB": pib,
                            "DESCRIÇÃO DO BEM": descricao,
                            "USUÁRIO/LOCAL": usuario,
                            "SITUAÇÃO DO BEM": situacao,
                            "VALOR (R$)": valor
                        })
                    except Exception:
                        continue
                        
    return pd.DataFrame(dados_finais)

if uploaded_file is not None:
    df = processar_pdf(uploaded_file)
    
    if not df.empty:
        st.success(f"Foram identificados {len(df)} itens em todo o documento.")
        
        # Exibe a tabela completa no navegador
        st.dataframe(df, use_container_width=True)
        
        # Conversão para Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Baixar Planilha Completa",
            data=output.getvalue(),
            file_name="patrimonio_sem_cabecalho.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Nenhum dado encontrado. Verifique se o PDF possui o formato esperado.")
