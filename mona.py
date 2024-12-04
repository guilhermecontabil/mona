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
    /* Estilo dos inputs */
    .stTextInput>div>div>input {
        background-color: #333333;
        color: #ffffff;
    }
    /* Estilo dos selectboxes */
    .stSelectbox>div>div>div>select {
        background-color: #333333;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# --- Barra Lateral ---
st.sidebar.title("⚙️ Configurações")

# Upload do arquivo Excel
uploaded_file = st.sidebar.file_uploader("📥 Importar arquivo Excel", type=["xlsx", "xls"])

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

    # Criar coluna de Mês/Ano para filtros e agrupamentos
    df['Mês/Ano'] = df['Data'].dt.to_period('M').dt.to_timestamp()

    # Filtro por Conta Bancária
    if 'Conta bancária' in df.columns:
        contas_bancarias = df['Conta bancária'].unique()
        conta_selecionada = st.sidebar.selectbox("🏦 Filtrar por Conta Bancária:", ["Todas as Contas"] + list(contas_bancarias))

        # Aplicando o filtro de Conta Bancária
        if conta_selecionada != "Todas as Contas":
            df_filtrado = df[df['Conta bancária'] == conta_selecionada]
        else:
            df_filtrado = df
    else:
        st.sidebar.error("A coluna 'Conta bancária' não foi encontrada no arquivo.")
        df_filtrado = df

    # Filtro por Mês
    meses_disponiveis = df['Mês/Ano'].dt.strftime('%b %Y').unique()
    meses_selecionados = st.sidebar.multiselect("🗓️ Filtrar por Mês:", options=meses_disponiveis, default=meses_disponiveis)

    # Converter meses selecionados para datetime para filtrar
    meses_selecionados_dt = pd.to_datetime(meses_selecionados, format='%b %Y')

    # Aplicar filtro de mês
    df_filtrado = df_filtrado[df_filtrado['Mês/Ano'].isin(meses_selecionados_dt)]

    # Filtro por Plano de Contas
    filtro_plano_contas = st.sidebar.text_input("🔍 Filtrar Plano de Contas:")

    if filtro_plano_contas:
        df_filtrado = df_filtrado[df_filtrado['Plano de contas'].str.contains(filtro_plano_contas, case=False, na=False)]

    # --- Cabeçalho ---
    st.title("💹 Dashboard Financeiro Neon")
    st.markdown("Bem-vindo ao dashboard financeiro com temática neon. Visualize e analise os dados financeiros com um visual moderno.")

    # --- Criação das Abas ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumo", "📄 Dados", "📈 Gráficos", "💾 Exportação"])

    # --- Aba Resumo ---
    with tab1:
        st.subheader("Resumo Financeiro")
        total_receitas = df_filtrado[df_filtrado['Valor'] > 0]['Valor'].sum()
        total_despesas = df_filtrado[df_filtrado['Valor'] < 0]['Valor'].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Receitas 💰", f"R$ {total_receitas:,.2f}")
        col2.metric("Total Despesas 💸", f"R$ {abs(total_despesas):,.2f}")

        # Resumo por plano de contas agrupado por Mês/Ano
        summary = df_filtrado.groupby(['Plano de contas', 'Mês/Ano'])['Valor'].sum().reset_index()
        summary_pivot = summary.pivot(index='Plano de contas', columns='Mês/Ano', values='Valor').fillna(0)
        summary_pivot['Total'] = summary_pivot.sum(axis=1)

        # Ordenar as colunas de Mês/Ano
        summary_pivot = summary_pivot.sort_index(axis=1)

        st.subheader("Total por Plano de Contas (Agrupado por Mês/Ano)")
        st.dataframe(
            summary_pivot.style.format("{:,.2f}")
            .set_properties(**{'background-color': '#1a1a1a', 'color': '#ffffff'})
        )

    # --- Aba Dados ---
    with tab2:
        st.subheader("Dados Importados")
        st.dataframe(
            df_filtrado.style.format({'Valor': 'R$ {:,.2f}', 'Data': '{:%d/%m/%Y}'})
            .set_properties(**{'background-color': '#1a1a1a', 'color': '#ffffff'})
        )

    # --- Aba Gráficos ---
    with tab3:
        # Gráfico de Receitas por Mês
        st.subheader("Receitas por Mês")
        df_receitas = df_filtrado[df_filtrado['Valor'] > 0]

        # Agrupar e ordenar os dados
        df_receitas_agrupado = df_receitas.groupby('Mês/Ano')['Valor'].sum().reset_index()
        df_receitas_agrupado = df_receitas_agrupado.sort_values('Mês/Ano')

        if not df_receitas_agrupado.empty:
            fig_receitas = px.bar(
                df_receitas_agrupado,
                x='Mês/Ano',
                y='Valor',
                title='Receitas por Mês',
                labels={'Valor': 'Valor (R$)', 'Mês/Ano': 'Mês/Ano'},
                template='plotly_dark',
                color_discrete_sequence=['#39ff14']
            )
            fig_receitas.update_layout(
                xaxis_tickangle=-45,
                xaxis_title='Mês/Ano',
                yaxis_title='Valor (R$)',
                xaxis_tickformat='%b\n%Y',
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#39ff14')
            )
            st.plotly_chart(fig_receitas, use_container_width=True)
        else:
            st.write("Não há receitas para exibir.")

        # Gráfico de Despesas por Plano de Contas
        st.subheader("Despesas por Plano de Contas")
        df_despesas = df_filtrado[df_filtrado['Valor'] < 0]
        df_despesas_agrupado = df_despesas.groupby('Plano de contas')['Valor'].sum().reset_index()
        if not df_despesas_agrupado.empty:
            df_despesas_agrupado['Valor'] = df_despesas_agrupado['Valor'].abs()
            fig_despesas = px.bar(
                df_despesas_agrupado,
                x='Plano de contas',
                y='Valor',
                color='Plano de contas',
                title='Despesas por Plano de Contas',
                labels={'Valor': 'Valor (R$)'},
                template='plotly_dark',
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_despesas.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#39ff14')
            )
            st.plotly_chart(fig_despesas, use_container_width=True)
        else:
            st.write("Não há despesas para exibir.")

        # Gráfico de Linha do Saldo Acumulado
        st.subheader("Evolução do Saldo Acumulado")
        df_filtrado_sorted = df_filtrado.sort_values('Data')
        df_filtrado_sorted['Saldo Acumulado'] = df_filtrado_sorted['Valor'].cumsum()
        fig_saldo = px.line(
            df_filtrado_sorted,
            x='Data',
            y='Saldo Acumulado',
            title='Evolução do Saldo Acumulado',
            labels={'Saldo Acumulado': 'Saldo Acumulado (R$)', 'Data': 'Data'},
            template='plotly_dark'
        )
        fig_saldo.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#39ff14')
        )
        st.plotly_chart(fig_saldo, use_container_width=True)

    # --- Aba Exportação ---
    with tab4:
        st.subheader("Exportar Resumo")
        csv_data = convert_df(summary_pivot.reset_index())
        st.download_button(
            label="💾 Exportar Resumo para CSV",
            data=csv_data,
            file_name='Resumo_Plano_De_Contas.csv',
            mime='text/csv'
        )

        # Opção para exportar os dados filtrados
        st.subheader("Exportar Dados Filtrados")
        csv_dados_filtrados = convert_df(df_filtrado)
        st.download_button(
            label="💾 Exportar Dados Filtrados para CSV",
            data=csv_dados_filtrados,
            file_name='Dados_Filtrados.csv',
            mime='text/csv'
        )

else:
    st.warning("Por favor, faça o upload de um arquivo Excel para começar.")
