import streamlit as st
import pandas as pd
import requests

st.title("TESTE")
st.write("LOREM IPSUM")

produto_busca = st.text_input("O que você está procurando?", "iPhone 15")

# Alterado de os.environ para o sistema nativo do Streamlit
API_KEY = st.secrets.get("API_KEY")
URL_API = "https://google.serper.dev/shopping"

if st.button("Buscar"):
    st.write(f"Buscando {produto_busca}...")
    
    # Validação segura da chave do Streamlit
    if not API_KEY:
        st.error("🔑 Erro de Configuração: A chave 'API_KEY' não foi encontrada nos Segredos do Streamlit.")
        st.info("Certifique-se de criar o arquivo `.streamlit/secrets.toml` no seu projeto.")
    else:
        payload = {"q": produto_busca, "gl": "br", "hl": "pt-br"}
        headers = {"X-API-KEY": API_KEY, 'content-type': 'application/json'}
        
        try:
            response = requests.post(URL_API, json=payload, headers=headers)
            data = response.json()
            results_raw = data.get("shopping", [])
        except Exception as e:
            st.error(f"Erro ao conectar com a API: {e}")
            results_raw = []

        resultados_processados = []
        
        for item in results_raw:
            try:
                preco_texto = item.get("price", "0").replace("R$", "").replace(".", "").replace(",", ".").strip()
                preco = float(preco_texto)
            except:
                preco = 0.0
                
            frete_texto = item.get("delivery", "0").lower()
            frete = 0.0 if ("grátis" in frete_texto or "gratis" in frete_texto) else 25.0

            avaliacao = item.get("rating", 4.0)
            custo_real = preco + frete
            score = custo_real - (avaliacao * 10)
            
            if preco > 0:
                resultados_processados.append({
                    "Produto": item.get("title"),
                    "Loja": item.get("source"),
                    "Preço": preco,          
                    "Frete": frete,          
                    "Total": custo_real,     
                    "Avaliação": f"{avaliacao}⭐",
                    "Score Custo-Benefício": round(score, 2),
                    "Link": item.get("link", "") 
                })
        
        if resultados_processados:
            df = pd.DataFrame(resultados_processados)
            
            # Filtro de Outliers (Desvio Padrão)
            if len(df) > 2:
                media = df["Preço"].mean()
                desvio_padrao = df["Preço"].std()
                limite_inferior = media - (1.2 * desvio_padrao)
                df = df[df["Preço"] >= limite_inferior]
                
            # Ordenação e Correção de Índices
            df = df.sort_values(by="Score Custo-Benefício")
            df = df.reset_index(drop=True)
            df.index = df.index + 1
            
            st.success("Ofertas reais indexadas com sucesso!")
            
            # Exibição com Hyperlinks e Formatação de Moeda
            st.dataframe(
                df,
                column_config={
                    "Preço": st.column_config.NumberColumn("Preço", format="R$%.2f"),
                    "Frete": st.column_config.NumberColumn("Frete", format="R$%.2f"),
                    "Total": st.column_config.NumberColumn("Total", format="R$%.2f"),
                    "Link": st.column_config.LinkColumn("Onde Comprar", display_text="Ir para a loja ↗️")
                },
                column_order=["Produto", "Loja", "Preço", "Frete", "Total", "Avaliação", "Score Custo-Benefício", "Link"],
                use_container_width=True
            )
        else:
            st.error("Nenhum resultado encontrado para este termo.")