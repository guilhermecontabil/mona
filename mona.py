import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração inicial da página do Streamlit
st.set_page_config(page_title="Dashboard Financeiro Neon", layout="wide")

# Função para converter DataFrame para CSV
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# --- Estilos CSS Personalizados ---
st.markdown("""
    <style>
    /* Estilo dos títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #39ff14;
    }
    /* Estilo dos textos */
    .st-text, .st-dataframe {
        color: #ffffff;
    }
    /* Estilo das métricas */
    .stMetric-label {
        color: #39ff14;
    }
    .stMetric-value {
        color: #39ff14;
    }
    /* Estilo dos botões */
    .stButton>button {
        background-color: #39ff14;
        color: #000000;
    }
    /* Estilo dos elementos da barra lateral */
    .sidebar .sidebar-content {
        background-color: #1a1a1a;
    }
    </style>
""", unsafe_allow_html=True)

# --- Barra Lateral ---
st.sidebar.title("⚙️ Configurações")

# Upload do arquivo Excel
uploaded_file = st.sidebar.file_uploader("📥 Importar arquivo Excel", type=["xlsx"])

if uploaded_file is not None:
    # Carregar o arquivo Excel na memória
    df = pd.read_excel(uploaded_file)
    st.sidebar.success("Arquivo carregado com sucesso.")
    # Armazenar o DataFrame no session_state
    st.session_state['df'] = df
elif 'df' in st.session_state:
    # Usar o DataFrame armazenado no session_state
    df = st.session_state['df']
else:
    st.sidebar.warning("Por favor, faça o upload de um arquivo Excel para começar.")
    df = None

if df is not None:
    # Tratamento de dados (formatação de datas)
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

    # Filtro por loja
    lojas = df['Loja'].unique()
    loja_selecionada = st.sidebar.selectbox("🏬 Filtrar por Loja:", ["Todas as Lojas"] + list(lojas))

    # Aplicando o filtro de loja
    if loja_selecionada != "Todas as Lojas":
        df_filtrado = df[df['Loja'] == loja_selecionada]
    else:
        df_filtrado = df

    # Filtro por Plano de Contas
    filtro_plano_contas = st.sidebar.text_input("🔍 Filtrar Plano de Contas:")

    if filtro_plano_contas:
        df_filtrado = df_filtrado[df_filtrado['Plano de contas'].str.contains(filtro_plano_contas, case=False, na=False)]

    # --- Cabeçalho ---
    st.title("💹 Dashboard Financeiro Neon")
    st.markdown("Bem-vindo ao dashboard financeiro com temática neon. Visualize e analise os dados de vendas e despesas com um visual moderno.")

    # --- Criação das Abas ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumo", "📄 Dados", "📈 Gráficos", "💾 Exportação"])

    # --- Aba Resumo ---
    with tab1:
        st.subheader("Resumo de Vendas")
        total_vendas = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)^vendas$', na=False)]['Valor'].sum()
        total_vendas_balcao = df_filtrado[df_filtrado['Plano de contas'].str.contains(r'(?i)vendas no balcão', na=False)]['Valor'].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Vendas 🛒", f"R$ {total_vendas:,.2f}")
        col2.metric("Total Vendas Balcão 🏬", f"R$ {total_vendas_balcao:,.2f}")

        # Resumo por plano de contas agrupado por Mês/Ano
        df_filtrado['Mês/Ano'] = df_filtrado['Data'].dt.to_period('M')
        summary = df_filtrado.groupby(['Plano de contas', 'Mês/Ano'])['Valor'].sum().reset_index()
        summary_pivot = summary.pivot(index='Plano de contas', columns='Mês/Ano', values='Valor').fillna(0)
        summary_pivot['Total'] = summary_pivot.sum(axis=1)

        st.subheader("Total por Plano de Contas (Agrupado por Mês/Ano)")
        st.dataframe(summary_pivot.style.format({'Total': 'R$ {:,.2f}'}).set_properties(**{'background-color': '#1a1a1a', 'color': '#ffffff'}))

    # --- Aba Dados ---
    with tab2:
        st.subheader("Dados Importados")
        st.dataframe(df_filtrado.style.format({'Valor': 'R$ {:,.2f}'}).set_properties(**{'background-color': '#1a1a1a', 'color': '#ffffff'}))

    # --- Aba Gráficos ---
    with tab3:
        # Gráfico de Entradas de Disponibilidade (valores positivos)
        st.subheader("Entradas de Disponibilidade (Valores Positivos)")
        df_positivo = df_filtrado[df_filtrado['Valor'] > 0]
        df_positivo_agrupado = df_positivo.groupby('Plano de contas')['Valor'].sum().reset_index()
        if not df_positivo_agrupado.empty:
            fig = px.bar(
                df_positivo_agrupado,
                x='Plano de contas',
                y='Valor',
                color='Plano de contas',
                title='Entradas de Disponibilidade por Plano de Contas',
                labels={'Valor': 'Valor (R$)'},
                template='plotly_dark',
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#39ff14')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Não há valores positivos para exibir.")

        # Top 5 categorias de despesas
        st.subheader("Top 5 Categorias de Despesas")
        df_negativo = df_filtrado[df_filtrado['Valor'] < 0]
        df_negativo_agrupado = df_negativo.groupby('Plano de contas')['Valor'].sum().abs().reset_index()
        if not df_negativo_agrupado.empty:
            top_5 = df_negativo_agrupado.nlargest(5, 'Valor')
            fig3 = px.bar(
                top_5,
                y='Plano de contas',
                x='Valor',
                orientation='h',
                title='Top 5 Categorias de Despesas',
                labels={'Valor': 'Valor (R$)', 'Plano de contas': 'Plano de Contas'},
                template='plotly_dark',
                color_discrete_sequence=['#ff1493']
            )
            fig3.update_layout(
                yaxis={'categoryorder':'total ascending'},
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#39ff14')
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.write("Não há valores negativos para exibir nas top 5 despesas.")

    # --- Aba Exportação ---
    with tab4:
        st.subheader("Exportar Resumo")
        csv_data = convert_df(summary_pivot)
        st.download_button(
            label="💾 Exportar Resumo para CSV",
            data=csv_data,
            file_name='Resumo_Plano_De_Contas.csv',
            mime='text/csv'
        )

else:
    st.warning("Por favor, faça o upload de um arquivo Excel para começar.")
