import datetime
import json
import streamlit as st
from streamlit_option_menu import option_menu
from attention_rules import process_attention_data  # processar dados de atenção
import subprocess
import os
import signal
import time
import plotly.graph_objects as go
import plotly.express as px



PID_FILE = "process.pid"  # Arquivo para salvar o PID do processo de coleta


# Dicionário com categorias, softwares e descrições
software_categories = {
    "Produtividade": {
        "description": "Softwares usados para escrever e depurar código",
        "apps": ["Visual Studio Code", "PyCharm", "Eclipse", "ChatGPT", "GitHub Desktop"]
    },
    "Documentos": {
        "description": "Ferramentas para criar, visualizar e editar documentos",
        "apps": ["Microsoft Word", "Microsoft Powerpoint", "Microsoft Excel", "Pré-Visualização", "Google Sheets", "Google Docs", "LaTeX"]
    },
    "Reuniões": {
        "description": "Plataformas para videoconferências e colaboração online",
        "apps": ["Zoom", "Microsoft Teams", "Google Meet", "zoom.us"]
    },
    "Entretenimento": {
        "description": "Plataformas de streaming e jogos",
        "apps": ["YouTube", "Netflix", "Spotify", "Steam", "Epic Games Launcher", "Roblox"]
    },
    "Redes Sociais": {
        "description": "Plataformas de redes sociais e mensagens",
        "apps": ["Facebook", "Instagram", "TikTok", "WhatsApp"]
    },
    "Educação": {
        "description": "Plataformas e ferramentas educacionais",
        "apps": ["Coursera", "Moodle", "Udemy"]
    }
}



# 1. Página de Configuração de Preferências
def configure_preferences():
    st.title("Configuração de Preferências")
    st.markdown(
        """
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px;">
            <p style="font-size: 13px; margin: 10px 0;">Nesta página, você pode:</p>
            <ul style="font-size: 13px; padding-left: 20px;">
                <li>Selecionar os softwares que considera úteis para trabalho ou estudo (<b>Foco Atencional</b>).</li>
                <li>Configurar o uso de <b>fones de ouvido</b> e definir como a <b>música</b> afeta sua concentração.</li>
                <li>A disposição dos seus monitores para melhorar a análise da <b>posição da cabeça</b>.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Cria duas colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Seleção de Ferramentas")
        st.write("Selecione os softwares, classificados por categoria, que você considera úteis para trabalho ou estudo:")
        focus_apps = []
        for category, details in software_categories.items():
            st.markdown(f"<p style='color: #000000; font-size: 15px; font-weight: bold;'>{category}</p>", unsafe_allow_html=True)
            selected_apps_focus = st.multiselect(details["description"] + ":", details["apps"])
            focus_apps.extend(selected_apps_focus)
        
    
    with col2:
        st.subheader("Domínios de Sites")
        st.write("Se você usa o Safari para trabalho ou estudo, adicione os domínios permitidos abaixo (exemplo: openai.com, google.com).")
        focus_urls = st.text_area("Digite os domínios separados por vírgula:", "").split(",")
        
        st.markdown("<br><br>", unsafe_allow_html=True)  # Quebras de linha

        st.subheader("Contexto")
        is_using_headphones = st.checkbox("Estou usando fone de ouvido", value=False)
        music_preference = st.radio(
            "Como a música afeta seu foco?",
            options=["Me ajuda a concentrar", "Me distrai", "Não afeta meu foco"],
            index=2
        )

        st.markdown("<br><br>", unsafe_allow_html=True)  # Quebras de linha
    
        st.subheader("Monitores")
        num_monitors = st.number_input("Quantos monitores você utiliza?", min_value=1, max_value=3, step=1, value=1)
        monitor_positions = {}
        for i in range(1, num_monitors + 1):
            position = st.selectbox(f"Posição do Monitor {i}:", ["Frente", "Esquerda", "Direita", "Acima"], key=f"monitor-{i}")
            monitor_positions[f"Monitor {i}"] = position
        st.markdown("<br>", unsafe_allow_html=True)  # Quebras de linha
    
    # Botão para salvar as preferências (fora das colunas para centralizar)
    col1_center, col2_center, col3_center = st.columns(3)
    with col2_center:
        if st.button("Salvar Preferências"):
            preferences = {
                "Monitores": monitor_positions,
                "Foco": focus_apps,
                "Contexto": {
                    "UsandoFones": is_using_headphones,
                    "PreferenciaMusica": music_preference
                },
                "FocoURLs": [url.strip() for url in focus_urls if url.strip()]
            }
            with open("user_preferences.json", "w") as f:
                json.dump(preferences, f, indent=4)
            st.success("Preferências salvas com sucesso!")




# 2. Página para Iniciar a Coleta de Dados
def start_data_collection():
    st.title("Iniciar/Parar Coleta de Dados")
    st.write("Clique nos botões abaixo para iniciar ou parar o processo de coleta de dados.")

    col1, col2 = st.columns(2)

    # Botão para Iniciar Coleta
    with col1:
        if st.button("Iniciar Coleta"):
            if os.path.exists(PID_FILE):
                st.warning("A coleta de dados já está em execução.")
            else:
                try:
                    # Inicia o subprocesso e salva o PID
                    process = subprocess.Popen(["python", "main.py"], cwd=os.getcwd())
                    with open(PID_FILE, "w") as f:
                        f.write(str(process.pid))
                    #st.success("Coleta de dados iniciada com sucesso.")
                    st.success("Este é um exemplo demonstrativo. A coleta de dados real não está ocorrendo.")
                except Exception as e:
                    st.error(f"Erro ao iniciar a coleta: {e}")

    # Botão para Parar Coleta
    with col2:
        if st.button("Parar Coleta"):
            if not os.path.exists(PID_FILE):
                st.warning("Nenhuma coleta de dados em execução.")
            else:
                try:
                    # Lê o PID do arquivo e encerra o processo
                    with open(PID_FILE, "r") as f:
                        pid = int(f.read())
                    os.kill(pid, signal.SIGTERM)  # Encerra o processo
                    os.remove(PID_FILE)  # Remove o arquivo PID
                    st.success("Coleta de dados interrompida.")
                except Exception as e:
                    st.error(f"Erro ao parar a coleta: {e}")


# 3. Página de Análise dos Dados
def analyze_data():
    st.title("Análise dos Dados Atencionais")
    print("--------------------------------------------------------")
    print("DATA", datetime.datetime.now())
    print("--------------------------------------------------------")

    # Criar colunas para alinhar botão e última atualização
    col1, col2 = st.columns([1, 1.5])

    # Inicializar a variável na sessão (se ainda não existir)
    if "last_update" not in st.session_state:
        st.session_state["last_update"] = None

    # Botão para iniciar análise
    with col1:
        if st.button("Analisar Dados Recentes"):
            st.session_state["show_graph"] = True  # Define variável de estado
            st.session_state["last_update"] = datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y')

    # Mostrar a última atualização ao lado
    with col2:
        with st.container():
            st.markdown(
                """
                <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                    <p style="margin: auto; font-size: 16px; margin-left: -10px; margin-top: 5px;">
                        📅 <strong>Última atualização:</strong> 
                        {last_update}
                    </p>
                </div>
                """.format(last_update=st.session_state["last_update"] if st.session_state["last_update"] else "Dados ainda não analisados."),
                unsafe_allow_html=True
            )

    # Se o botão foi pressionado, exibir o gráfico
    if st.session_state.get("show_graph", False):
        # Criar um espaço para atualizar dinamicamente o gráfico
        graph_placeholder = st.empty()

        # Obtém os dados processados do attention_rules.py
        data, software_usage_time, sound_impact_data = process_attention_data()

        # DEBUG: Exibir os últimos 10 registros processados
        print("\n Dados antes de gerar o gráfico:")
        print(data.tail(10))  # Últimos 10 registros para análise
        print("\n ------  DADOS COMPLETOS - ANTES DE GERAR O GRAFICO:  --------")
        print(data.to_string())  # Exibir todos os registros sem truncamento

        if not data.empty:
            # Limpar gráfico anterior antes de renderizar o novo
            graph_placeholder.empty()

            # Preparar os dados para o gráfico
            timestamps = data.index
            attention_levels = data["Atento (%)"]
            attention_types = data["Tipo de Atenção"]

            attention_colors = {
                "Atenção": "#66C2A5",  # Verde suave
                "Atenção Alternada": "#8DA0CB",  # Azul lavanda
                "Atenção Sustentada": "#228B22",  # Verde escuro, enfatiza o alto foco
                "Atenção Seletiva": "#FFD92F",  # Amarelo claro (atenção com ruidos de fundo)
                "Distração": "#eb5f53",  # avermelhado
                "Neutro": "#B3B3B3"  # Cinza neutro
            }


            # Criar gráfico interativo com Plotly
            fig = go.Figure()

            # Adicionar linha principal do gráfico
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=attention_levels,
                mode="lines+markers",
                marker=dict(size=8, color="black", opacity=0.6),
                line=dict(width=2, color="black"),
                name="Nível de Atenção",
                hoverinfo="skip"  # Isso remove o tooltip padrão da linha
            ))

            # Adicionar pontos coloridos e tooltips detalhados
            for i, timestamp in enumerate(timestamps):
                tipo_atencao = attention_types.iloc[i]
                cor = attention_colors.get(tipo_atencao, "gray")

                # Determinar corretamente o Estado de Atenção
                porcentagem_atencao = data.iloc[i]["Atento (%)"]
                porcentagem_distracao = data.iloc[i]["Distraído (%)"]

                if porcentagem_atencao > porcentagem_distracao:
                    estado = f"Atento ({porcentagem_atencao:.1f}%)"
                else:
                    estado = f"Distraído ({porcentagem_distracao:.1f}%)"

                # DEBUG: Exibir informações antes de plotar
                print(f"Plotando ponto -> Timestamp: {timestamp}, Atento (%): {porcentagem_atencao}, Tipo: {tipo_atencao}")

                # Criar tooltip com detalhes do bloco de tempo
                detalhes = (
                    f"⏰ {timestamp.strftime('%H:%M:%S')}<br>"
                    f"🎯 Estado: {estado}<br>"
                    f"💻 Software Mais Usado: {data.iloc[i]['Software Mais Usado']}<br>"
                    f"👀 Posição Mais Frequente: {data.iloc[i]['Posição Cabeça Mais Comum']}<br>"
                    f"🔊 Som Predominante: {data.iloc[i]['Som Predominante']}<br>"
                    f"🏷️ Tipo de Atenção: {tipo_atencao}"
                )

                # Adicionar ponto ao gráfico com tooltip
                fig.add_trace(go.Scatter(
                    x=[timestamp],
                    y=[porcentagem_atencao],
                    mode="markers",
                    marker=dict(size=10, color=cor, line=dict(color="black", width=1)),
                    name=tipo_atencao,
                    text=detalhes,
                    hoverinfo="text",
                    showlegend=False  # Evita que as legendas se repitam
                ))

            # Configurar layout do gráfico
            fig.update_layout(
                title="Evolução da Atenção ao Longo do Tempo (Atualizado a cada 30 segundos)", #atualização a cada 30s
                xaxis_title="Tempo",
                yaxis_title="Estado de Atenção (%)",
                yaxis=dict(range=[0, 105]),  # Pequena margem extra para evitar corte no 100%
                hovermode="closest",
                template="plotly_white"
            )

            # EXPLICAÇÃO DOS TIPOS DE ATENÇÃO EM UMA DIV ABAIXO DO GRÁFICO**
            st.markdown(
                """
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <h4 style="font-size: 16px;">Classificação dos Estados Atencionais</h4>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #1B9E77; font-weight: bold;">Atenção Sustentada:</span> Manutenção do foco em uma atividade por um período prolongado, sem interrupções significativas.</p>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #8DA0CB; font-weight: bold;">Atenção Alternada:</span> Habilidade de alternar o foco entre diferentes tarefas, mantendo a eficiência na execução.</p>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #FFD92F; font-weight: bold;">Atenção Seletiva:</span> Capacidade de concentrar-se em um estímulo específico, mesmo com distrações no ambiente.</p>
                    <p style="font-size: 13px; margin: 10px 0;"><span style="color: #66C2A5; font-weight: bold;">Atenção:</span> Estado de foco adequado na atividade principal, sem alternâncias frequentes ou interferências externas.</p>
                    <p style="font-size: 13px;"><span style="color: #eb5f53; font-weight: bold;">Distração:</span> Perda de atenção devido a fatores externos ou dificuldades em manter o engajamento na tarefa em execução.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Atualizar gráficos no Streamlit
            # Gráfico principal de atenção ao longo do tempo
            graph_placeholder.plotly_chart(fig, use_container_width=True)

            # Criar colunas de tamanhos diferentes (gráfico de barras maior)
            col1, col2 = st.columns([1.7, 1])

            # Adicionar o gráfico de softwares usados na coluna maior
            with col1:
                fig_bar = plot_most_used_software(software_usage_time)
                if fig_bar:
                    st.plotly_chart(fig_bar, use_container_width=True)

            # Adicionar o gráfico de pizza (Atenção x Distração) na coluna menor
            with col2:
                fig_pie = plot_attention_pie_chart(data)
                if fig_pie:
                    st.plotly_chart(fig_pie, use_container_width=True)

            # Adicionar o gráfico de impacto do som
            fig_sound = plot_sound_impact_chart(sound_impact_data)
            if fig_sound:
                st.plotly_chart(fig_sound, use_container_width=True)

        else:
            st.warning("Ainda não há dados processados para análise.")

        # Atualiza automaticamente a página a cada 30 segundos
        #now = datetime.datetime.now()
        #seconds = now.second

        # Espera até o próximo ciclo de 00 ou 30 segundos
        #sleep_time = 30 - seconds if seconds < 30 else 60 - seconds
        #time.sleep(sleep_time)
        #st.rerun()




# Criar gráfico de barras para softwares mais usados
def plot_most_used_software(software_usage_time):
    """
    Gera um gráfico de barras com os 3 softwares mais usados, mantendo um design mais limpo e profissional.
    """
    top_software = software_usage_time.nlargest(3)

    # Cores alternativas da paleta Set2 que não conflitam com o gráfico principal
    custom_colors_bar = ["#89A8B2", "#B3C8CF", "#E5E1DA", "#F1F0E8"]

    fig = px.bar(
        x=top_software.index,
        y=top_software.values,
        labels={"x": "Software", "y": "Tempo de Uso (min)"},
        title="Tempo de Uso por Software",
        color=top_software.index,
        #color_discrete_sequence=px.colors.qualitative.Set2  # Paleta de cores Set2
        color_discrete_sequence=custom_colors_bar, 
        hover_data={"color": False}  # REMOVE "color=Microsoft Excel" DO TOOLTIP
    )


    # Melhorar rótulos e layout
    fig.update_traces(
        texttemplate='%{y:2f} min',  # tempo com 1 casa decimal
        textposition='outside',
        marker=dict(line=dict(width=0)),  # Remove bordas das barras
    )

    fig.update_layout(
        showlegend=False,
        yaxis_title="Tempo (min)",
        xaxis_title="Softwares",
        xaxis_tickangle=0,
        yaxis=dict(
            tickformat=".2f", 
            showgrid=True, 
            range=[0, software_usage_time.max() * 1.2]  # Adiciona 20% extra para evitar corte
        ),
        margin=dict(t=60, b=50, l=50, r=50),
        width=650,  
        height=450  # Reduzindo a altura para um encaixe mais fluído
    )

    return fig




# Grafico de pizza para distribuição de atenção e distração
def plot_attention_pie_chart(grouped):
    """
    Gera um gráfico de pizza mostrando a distribuição total de atenção e distração.
    """
    if grouped.empty:
        st.warning("Nenhum dado disponível para análise de atenção.")
        return None

    # Calcular médias gerais de atenção e distração
    total_atento = grouped["Atento (%)"].mean()
    total_distraido = grouped["Distraído (%)"].mean()

    # Criar um DataFrame para o gráfico
    pie_data = {
        "Estado": ["Atento", "Distraído"],
        "Porcentagem": [total_atento, total_distraido]
    }

    # Criar gráfico de pizza com Plotly
    fig = px.pie(
        pie_data,
        names="Estado",
        values="Porcentagem",
        title="Distribuição de Atenção e Distração",
        color="Estado",
        color_discrete_map={"Atento": "#66C2A5", "Distraído": "#eb5f53"}  # Verde para atenção, vermelho para distração
    )

    fig.update_traces(
        textfont=dict(family="Open Sans, Verdana, Arial, sans-serif", color="#ffffff"),
        marker=dict(line=dict(color="white", width=1)),  # Remove bordas indesejadas
        hovertemplate="<b>%{label}</b><br>%{percent:.2%}<extra></extra>",
    )

    fig.update_layout(
        margin=dict(t=60),  # Margens uniformes
        showlegend=True,  # Exibir legenda
        legend=dict(
            orientation="h",  # Legenda horizontal
            yanchor="bottom",  # Ancorar na parte inferior
        )
    )

    return fig





# Criar gráfico de barras para impacto do som na atenção
def plot_sound_impact_chart(sound_impact_data):
    """
    Gráfico de barras refinado para mostrar o impacto do som no estado de atenção.
    """

    custom_colors_sound = ["#89A8B2", "#B3C8CF", "#E5E1DA", "#F1F0E8"]

    if sound_impact_data.empty:
        st.warning("Nenhum dado disponível para o impacto do som na atenção.")
        return None

    filtered_data = sound_impact_data[sound_impact_data["Distração Média (%)"] > 0]
    if filtered_data.empty:
        st.warning("Nenhum som relevante foi identificado como impactando na atenção.")
        return None

    filtered_data = filtered_data.sort_values(by="Tempo Total do Som (min)", ascending=False)

    fig = px.bar(
        filtered_data,
        x="Tempo Total do Som (min)",
        y="Som Predominante",
        orientation="h",
        color="Som Predominante",
        color_discrete_sequence=custom_colors_sound,
        #color_discrete_sequence=px.colors.qualitative.Set2,  
        title="Tempo Estimado dos Sons que Impactaram na Atenção",
        text="Tempo Total do Som (min)",  
    )

    fig.update_traces(
        texttemplate='%{x:.2f} min',
        textposition="outside",
        marker=dict(line=dict(width=0))  # Remove bordas das barras
    )

    fig.update_layout(
        xaxis_title="Tempo Estimado (min)",
        yaxis_title="Som Predominante",
        height=320,  
        width=750,  
        margin=dict(t=30, b=30, l=50, r=10),  # Redução das margens
        xaxis=dict(showgrid=True, range=[0, filtered_data["Tempo Total do Som (min)"].max() * 1.2]),
        showlegend=False  
    )

    return fig






# Menu de Navegação
def main_dashboard():
    # Mostrar o diretório atual no Streamlit Cloud
    # st.write("Diretório atual:", os.getcwd())
    # Adicionar o logo acima do menu
    logo_path = os.path.join(os.getcwd(), "AttentionPrototype", "logo.png")
    st.sidebar.image(logo_path)

    # Criar menu estilizado
    with st.sidebar:
        selected = option_menu(
            menu_title="Menu Principal",  # Título do menu
            options=["Configurar Preferências", "Iniciar Coleta de Dados", "Analisar Dados"],  # Opções do menu
            icons=["gear", "cloud-download", "graph-up"],  # Ícones correspondentes
            menu_icon="display",  # Ícone do título
            default_index=0,  # Aba padrão selecionada
            styles={
                "container": {"padding": "5px", "background-color": "#FAFAFA"},  # Cor de fundo do menu
                "icon": {"color": "black", "font-size": "20px"},  # Estilização dos ícones
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "5px",
                    "--hover-color": "#EEE",
                },
                "nav-link-selected": {"background-color": "#eb5f53", "color": "white"},  # Destaque para item selecionado
            }
        )


        # Conteúdo de cada aba
    if selected == "Configurar Preferências":
        configure_preferences()
    elif selected == "Iniciar Coleta de Dados":
        start_data_collection()
    elif selected == "Analisar Dados":
        analyze_data()



if __name__ == "__main__":
    main_dashboard()