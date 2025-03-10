import json
import os
import pandas as pd
import time
import glob

''' 
1.	Função para carregar as preferências do usuário (load_user_preferences).
2.	Função para verificar se a cabeça está alinhada com os monitores (is_head_position_valid).
3.	Função para classificar o áudio do ambiente (classify_audio).
4.	Função para classificar o estado de atenção (classify_state).
5.	Função para analisar a atenção em blocos de tempo (analyze_attention_in_blocks).
6.	Monitoramento do CSV gerado em tempo real.
'''


# Pasta onde os arquivos CSV são salvos
CSV_DIRECTORY = "/Users/cassianosouza/Projects/MediaPipe-audio/data/"

def get_latest_csv():
    """Encontra o arquivo CSV mais recente na pasta. Se não houver, retorna None."""
    csv_files = glob.glob(os.path.join(CSV_DIRECTORY, "RawMultimodalData_*.csv"))  # Pega arquivos do formato esperado
    if not csv_files:
        return None  # Não lança erro, apenas retorna None
    return max(csv_files, key=os.path.getctime)  # Retorna o mais recente baseado na data de criação/modificação


# 1. Carregar Preferências do Usuário
def load_user_preferences():
    """
    Carrega as preferências do usuário a partir do JSON.
    Retorna: Um dicionário contendo as preferências do usuário.
    """
    try:
        with open("user_preferences.json", "r", encoding="utf-8") as f:
            preferences = json.load(f)
        return preferences
    except (FileNotFoundError, json.JSONDecodeError):
        print("Erro ao carregar user_preferences.json. Usando configurações padrão.")
        return {
            "Foco": [],
            "Contexto": {
                "UsandoFones": False,
                "PreferenciaMusica": "Não afeta meu foco"
            },
            "Monitores": {"Monitor 1": "Frente"}
        }
    



# 2. Verificar se a Cabeça Está Alinhada com os Monitores
def is_head_position_valid(head_pose, monitor_preferences):
    """
    Verifica se a posição da cabeça está alinhada com os monitores configurados.
    head_pose: string indicando a direção da cabeça (e.g., "Looking Left").
    OBS: "Looking Down" como uma posição válida para foco.
    monitor_preferences: dict com a posição dos monitores.
    Retorna: True se a posição for válida, False caso contrário.
    """
    
    head_position_map = {
        "Olhando para Frente": "Frente",
        "Olhando para a Esquerda": "Esquerda",
        "Olhando para a Direita": "Direita",
        "Olhando para Cima": "Acima",
        "Olhando para Baixo": "Baixo",  # Adiciona a opção de "Olhando para Baixo" como válido
        "Sem Detecção de Rosto": "Sem Detecção de Rosto"  # Indica que a pessoa não está no PC
    }

    # Permitir pequenas variações da posição da cabeça
    if head_pose == "Olhando para Baixo":
        return True  # Agora, nunca será considerado distração

    # Se "No Face Detected", retornar automaticamente False (Distraído)
    if head_pose == "No Face Detected":
        return False   

    return any(head_position_map.get(head_pose, "") == position for position in monitor_preferences.values())






# 3. Classificar o Impacto do Áudio Ambiente no Estado de Atenção
def classify_audio(audio_group, active_window, audio_score, preferences):
    """
    Classifica o impacto do áudio captado no estado de atenção.
    audio_group: Categoria do áudio (e.g., "Fala e Vozes", "Música").
    active_window: Software ativo no momento (e.g., "Zoom", "YouTube").
    preferences: Configurações do usuário, incluindo fones e preferência musical.
    Retorna: "Foco", "Distração" ou "Neutro".
    """

    usando_fones = preferences["Contexto"]["UsandoFones"]
    preferencia_musica = preferences["Contexto"]["PreferenciaMusica"]

    # Se o score for baixo (< 0.4), o áudio é considerado Neutro
    if audio_score < 0.4:
        return "Neutro"  # Sons fracos não influenciam, mas o foco ainda pode ser analisado!

    # Agora segue com a lógica normal de classificação (se o score for >= 0.4)

    # Se o usuário está usando fones
    if usando_fones:
        if audio_group == "Música":
            if preferencia_musica == "Me ajuda a concentrar":
                return "Foco"
            elif preferencia_musica == "Me distrai":
                return "Distração"
            else:  # "Não afeta meu foco"
                return "Foco"

        elif audio_group == "Fala e Vozes":
            if active_window in ["zoom.us", "Meet", "Microsoft Teams"]:
                return "Foco"  # Reuniões
            else:
                return "Distração"  # Conversa doméstica

        return "Neutro"  # Outros sons não influenciam com fones

    # Se o usuário NÃO está usando fones
    else:
        if audio_group == "Fala e Vozes":
            if active_window in ["zoom.us", "Meet", "Microsoft Teams"]:
                return "Foco"  # Reuniões
            elif audio_score >= 0.85:  
                return "Distração"  # TV ligada ou conversa no ambiente
            else:
                return "Neutro"  # Conversa fraca ao fundo
            


        elif audio_group == "Música":
            if preferencia_musica == "Me ajuda a concentrar":
                return "Foco"
            elif preferencia_musica == "Me distrai":
                return "Distração"
            else:  # "Não afeta meu foco"
                return "Foco"

        elif audio_group in ["Ruídos Intrusivos", "Ruídos Mecânicos e Veiculares", "Outros Sons"]:
            if audio_score >= 0.7:
                return "Distração"  # Sons altos e irritantes
            return "Neutro"  # Se for fraco, não afeta tanto

        elif audio_group in ["Ruídos de Fundo Neutros", "Natureza e Ambiente", "Ambiente Silencioso", "Não Classificado"]:
            return "Neutro"  # Sons não disruptivos são neutros

    return "Neutro"  # Caso padrão




# 4. Classificar o Estado de Atenção
def classify_state(row, preferences):
    """
    Classifica o estado de atenção com base nos dados do momento.
    row: dict contendo os dados de coleta.
    preferences: dict com as preferências do usuário.
    Retorna: estado de atenção (Atento, Distraído).
    """
    
    # Verificar janela ativa
    active_window = row.get("ActiveWindow", "")
    active_url = row.get("URL", "")  # Pode ser uma string vazia
    focus_urls = preferences.get("FocoURLs", [])  # Lista de sites relevantes para foco
    is_focus_software = active_window in preferences["Foco"] # Verifica se o software ativo está na lista de softwares de foco e retorna True ou False

    # Se o Safari estiver ativo, considerar a URL para determinar se é um site de foco
    if active_window == "Safari":
        if active_url:  
            is_focus_software = any(domain in active_url for domain in focus_urls)  # Verifica se a URL contém algum domínio de foco
        else:
            is_focus_software = False  # Se não houver URL, assume-se que não é um site de foco

    # Adicionando o print para depuração:
    #print(f"Software ativo: {active_window}, URL ativa: {active_url}, É foco? {is_focus_software}")

    # Verificar direção da cabeça
    head_pose = row.get("HeadPose", "")
    monitor_preferences = preferences.get("Monitores", {})
    head_position_valid = is_head_position_valid(head_pose, monitor_preferences)

    # Classificar impacto do áudio
    audio_group = row.get("AudioGroup", "Neutro") # Se a coluna AudioGroup estiver vazia ou não existir, ele retorna "Neutro" como valor padrão
    audio_score = row.get("AudioScore", 0.0)  # Se a coluna AudioScore estiver vazia ou não existir, retorna um valor padrão 0.0
    audio_state = classify_audio(audio_group, active_window, audio_score, preferences)


    # REGRAS PARA ATENÇÃO E DISTRAÇÃO:

    # Se o usuário está em um software de foco, olhando para um local válido e o áudio for classificado como "Foco" ou "Neutro" → Atento
    if is_focus_software and head_position_valid and audio_state in ["Foco", "Neutro"]:
        return "Atento"

    # Se o usuário está em um software de foco, mas olhando para um local sem monitor → Distraído
    elif is_focus_software and not head_position_valid:
        return "Distraído"

    # Se o software NÃO for de foco → Distraído (independente da posição da cabeça e do áudio)
    elif not is_focus_software:
        return "Distraído"

    return "Distraído"  # Caso padrão
    



#5. Função para contar trocas de software (indicativo de atenção alternada)
def count_software_switches(data, focus_apps):
    """
    Conta o número de trocas de software entre softwares de foco em cada bloco de tempo.
    data: DataFrame contendo os dados coletados, com a coluna 'ActiveWindow'.
    focus_apps: Lista de softwares que o usuário definiu como foco.
    Retorna: O número de trocas de software entre softwares de foco no bloco.
    """
    # Filtrar apenas os softwares de foco
    focus_data = data[data["ActiveWindow"].isin(focus_apps)]
    
    # Identificar mudanças de software no bloco (considerando apenas os de foco)
    switches = focus_data["ActiveWindow"].ne(focus_data["ActiveWindow"].shift())
    return switches.sum()


# Função para calcular o tempo total de uso de cada software
def calculate_software_usage(data, interval_seconds=5):
    """
    Calcula o tempo total de uso de cada software baseado na quantidade de vezes que ele aparece no CSV.
    Cada linha equivale a um intervalo fixo de tempo (5 segundos).
    """
    # Conta quantas vezes cada software aparece
    software_usage_counts = data["ActiveWindow"].value_counts()

    # Multiplica pelo tempo por entrada (5 segundos) e converte para minutos
    software_usage_time = (software_usage_counts * interval_seconds) / 60  

    return software_usage_time.round(2)  # Arredondar para duas casas decimais para melhor exibição





# Classificar os tipos de atenção (por bloco de tempo)
''''
switch_threshold=2: Limite de trocas de software para identificar atenção alternada 
Neste caso, mais de 2 alternâncias de software em um bloco de tempo de 30 segundos considera atenção alternada
'''
def classify_block(row, software_switches, switch_threshold=3, previous_blocks=None):
    """
    Classifica o tipo de atenção com base no estado do bloco.
    row: Uma linha do DataFrame agrupado por bloco.
    software_switches: Número de trocas de software no bloco (apenas softwares de foco).
    switch_threshold: Limite de trocas de software para identificar atenção alternada.
    previous_blocks: Lista dos últimos 3 blocos processados (para verificar atenção sustentada).
    """

    # Definição inicial dos tipos de atenção
    # 1. Atenção Alternada → Muitas trocas de software e ainda atento
    if 60 <= row["Atento (%)"] <= 100 and software_switches >= switch_threshold:
        return "Atenção Alternada"

    # 2. Atenção Sustentada → Manutenção da atenção por tempo prolongado (mínimo 4 blocos seguidos ≥ 60%)
    if previous_blocks is not None and len(previous_blocks) >= 3:
        # Coletar os últimos 3 blocos
        last_blocks = previous_blocks[-3:]
        # Se todos os últimos blocos e o atual têm atenção ≥ 90%, então é sustentada
        if all(block["Atento (%)"] >= 90 for block in last_blocks) and row["Atento (%)"] >= 90:
            return "Atenção Sustentada"
        
        
    # 3. Atenção Seletiva → Se a pessoa estiver atenta, mas com som de distração (exceto reuniões e música que ajuda a focar)
    user_preferences = load_user_preferences()
    if row["Atento (%)"] >= 60:
        # Se o som predominante for **Fala e Vozes** (mas não em reuniões)
        if row["Som Predominante"] == "Fala e Vozes" and row["Software Mais Usado"] not in ["zoom.us", "Meet", "Microsoft Teams"]:
            return "Atenção Seletiva"
        # Se o som predominante for **Música**, e o usuário configurou que "Me distrai"
        if row["Som Predominante"] == "Música" and user_preferences["Contexto"]["PreferenciaMusica"] == "Me distrai":
            return "Atenção Seletiva"
        # Se o som predominante for **Ruídos Intrusivos** ou **Ruídos Mecânicos e Veiculares**, mas não for extremamente alto
        if row["Som Predominante"] in ["Ruídos Intrusivos", "Ruídos Mecânicos e Veiculares", "Outros Sons"]:
            if row.get("Som Predominante Score", 0.0) < 0.7:  # Se o score for alto, então é muito disruptivo → Distração
                return "Atenção Seletiva"

    # 4. Se não se enquadrar em Atenção Seletiva, então considera-se "Atenção"
    if row["Atento (%)"] >= 60:
        return "Atenção"
    
    # 5. Distração → Se Distração (%) for maior
    if row["Distraído (%)"] >= 50:
        return "Distração"

    # Caso padrão, se nada for classificado antes
    return "Distração"

    



# 6. Analisar Atenção (em Blocos de Tempo)
def analyze_attention_in_blocks(data, interval="30s", switch_threshold=3):
    """
    Analisa os dados em blocos de tempo para calcular atenção.
    Agora adiciona também o Tipo de Atenção (Atenção Alternada, Atenção Sustentada, etc.).
    """
    data["Timestamp"] = pd.to_datetime(data["Timestamp"])

    # Carregar preferências
    preferences = load_user_preferences()
    focus_apps = preferences["Foco"]

    # Classificar estado de atenção
    data["AttentionState"] = data.apply(lambda row: classify_state(row, preferences), axis=1)

    # Lista para armazenar blocos anteriores
    previous_blocks = []

    # Agrupar os dados em blocos de tempo de 30 segundos
    data.set_index("Timestamp", inplace=True)
    grouped = data.resample(interval).apply(lambda x: {
        #"Atento (%)": (x["AttentionState"] == "Atento").mean() * 100,
        "Atento (%)": ((x["AttentionState"] == "Atento") & (x["HeadPose"] != "Olhando para Baixo")).mean() * 100,
        "Distraído (%)": (x["AttentionState"] == "Distraído").mean() * 100,
        "Trocas de Software": count_software_switches(x, focus_apps),
        "Software Mais Usado": x["ActiveWindow"].mode()[0] if not x["ActiveWindow"].isna().all() else "Desconhecido",
        "Posição Cabeça Mais Comum": x["HeadPose"].mode()[0] if not x["HeadPose"].isna().all() else "Sem Detecção de Rosto",
        "Som Predominante": (
            x.loc[x["AudioScore"] >= 0.4, "AudioGroup"].mode()[0]  
            if len(x.loc[x["AudioScore"] >= 0.4, "AudioGroup"]) > 1  # Exigir pelo menos 2 ocorrências
            else "Irrelevante para Análise"
        ),
        "Looking Down Count": (x["HeadPose"] == "Olhando para Baixo").sum()  # Conta quantas vezes olhou para baixo no bloco
    }).apply(pd.Series)

    



    # Chamar classify_block() para determinar o Tipo de Atenção
    for index, row in grouped.iterrows():
        #print(f"Previous Blocks: {[b['Atento (%)'] for b in previous_blocks]}")
        attention_type = classify_block(row, row["Trocas de Software"], switch_threshold, previous_blocks)
        
        # Se a pessoa olhou para baixo muitas vezes no bloco (3 ou mais), forçamos "Distração".
        if row["Looking Down Count"] >= 3:
            print(f"DEBUG - Muitas olhadas para baixo detectadas ({row['Looking Down Count']}). Classificando como Distração.")
            attention_type = "Distração"
        
        grouped.at[index, "Tipo de Atenção"] = attention_type
        previous_blocks.append(row)  # Adiciona o bloco atual ao histórico
        if len(previous_blocks) > 3:
            previous_blocks.pop(0)  # Mantém apenas os últimos 3 blocos no histórico

    return grouped




# 7. Monitorar CSV em Tempo Real
def monitor_csv_in_real_time(file_path, process_function, polling_interval=5):
    last_processed_timestamp = None
    while True:
        try:
            data = pd.read_csv(file_path)
            data["Timestamp"] = pd.to_datetime(data["Timestamp"], format="%H:%M:%S %d/%m/%Y")
            if last_processed_timestamp:
                new_data = data[data["Timestamp"] > last_processed_timestamp]
            else:
                new_data = data
            if not new_data.empty:
                process_function(new_data)
                last_processed_timestamp = new_data["Timestamp"].max()
        except Exception as e:
            print(f"Erro ao monitorar o CSV: {e}")
        time.sleep(polling_interval)





def calculate_sound_impact(data, block_interval_seconds=30):
    """
    Calcula o impacto do som predominante no estado de atenção.
    
    Retorna um DataFrame com:
        - Tempo total em que cada som predominou (em minutos).
        - Percentual médio de distração enquanto esse som predominava.
    """
    # Remover blocos onde o som predominante foi "Irrelevante para Análise"
    data = data[data["Som Predominante"] != "Irrelevante para Análise"]

    # Calcular o tempo total que cada som predominou (em minutos)
    sound_presence_time = data["Som Predominante"].value_counts() * block_interval_seconds / 60

    # Calcular a média de distração para cada som predominante
    distraction_by_sound = data.groupby("Som Predominante")["Distraído (%)"].mean()

    # Criar um DataFrame consolidado
    sound_impact_df = pd.DataFrame({
        "Tempo Total do Som (min)": sound_presence_time,
        "Distração Média (%)": distraction_by_sound
    }).reset_index().rename(columns={"index": "Som Predominante"})

    return sound_impact_df




# 8. Processar Dados de Atenção
def process_attention_data():
    """
    Processa os dados do CSV mais recente e retorna um DataFrame com os estados de atenção.
    """

    csv_path = get_latest_csv()  # Só tenta buscar um CSV aqui
    
    if csv_path is None:
        print("Nenhum arquivo CSV encontrado. Verifique se os dados estão sendo coletados.")
        return pd.DataFrame()  # Retorna um DataFrame vazio se não houver CSV
    
    try:
        print(f"Carregando dados de {csv_path}...")  # Log para depuração
        data = pd.read_csv(csv_path)
        data["Timestamp"] = pd.to_datetime(data["Timestamp"], format="%H:%M:%S %d/%m/%Y")
        data["URL"] = data["URL"].fillna("Nenhuma URL") # Substituir valores vazios por um identificador padrão

        # Carregar preferências do usuário
        preferences = load_user_preferences()

        # Classificar estado de atenção para cada linha
        data["AttentionState"] = data.apply(lambda row: classify_state(row, preferences), axis=1)

        # Agrupar por blocos de tempo (30 segundos)
        grouped = analyze_attention_in_blocks(data, interval="30s")

        # PRINT DOS RESULTADOS NO CONSOLE PARA TESTES
        print("\n Dados Processados:")
        print(grouped.tail(5))  # Mostra os últimos 5 registros no console
        print("\n")

        #return grouped
        # Calcular tempo total dos softwares corretamente
        software_usage_time = calculate_software_usage(data)

        # Calcular impacto do som predominante na atenção/distração
        sound_impact_data = calculate_sound_impact(grouped)

        return grouped, software_usage_time, sound_impact_data  # Retorna 3 DataFrames

    except Exception as e:
        print(f" Erro ao processar os dados: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()  # Retorna DataFrames vazios em caso de erro

    


