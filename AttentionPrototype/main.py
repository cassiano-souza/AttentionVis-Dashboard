import threading
from audio_module import AudioService  # Importa a classe AudioService
from window_module import WindowService # Importa a classe WindowService do Módulo de janela ativa
from head_module import HeadService  # Importa a classe HeadService do módulo de vídeo
import csv
import time
from audio_groups import map_to_group


# Gera um nome de arquivo com timestamp para cada nova execução
timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")  # Formato: "2024-01-29_12-45-30"
csv_filename = f"RawMultimodalData_{timestamp}.csv"
csv_path = f"/Users/cassianosouza/Projects/MediaPipe-audio/data/{csv_filename}"

# Cria o novo arquivo com cabeçalho
with open(csv_path, mode="w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Timestamp", "AudioClass", "AudioScore", "AudioGroup", "ActiveWindow", "URL", "HeadPose"])




def main():
    """Função principal que gerencia a execução paralela."""
    try:
        audio_service = AudioService() # Instancia a classe AudioService
        audio_service.startEngine()  # Inicializa o serviço de áudio
        window_service = WindowService()  # Inicializa o serviço de janelas
        head_service = HeadService()  # Inicializa o serviço de cabeça
        
        while True:
            print("Iniciando processo principal...")

            # Processamento do audio
            print("processando o audio...")
            audio_service.processorAudio()
            audio_service.result_ready.wait() # Espera o resultado estar pronto
            audio_result = audio_service.latest_result[0].classifications[0]
            audio_class = audio_result.categories[0].category_name
            audio_score = audio_result.categories[0].score
            print(audio_service.latest_result)

            # Mapeia a classe para seu grupo funcional
            audio_group = map_to_group(audio_class)
            print(f"Classificação do áudio: {audio_class}, Grupo: {audio_group}, Score: {audio_score}")

            # Processamento da janela
            print("processando a janela ativa...")
            window_data = window_service.get_active_app()
            print(f"Janela ativa: {window_data['Janela Ativa']}, URL: {window_data['URL']}, Timestamp: {window_data['Timestamp']}")

            # Processamento do vídeo
            print("processando o vídeo...")
            head_pose = head_service.run_head_module()  # Chama a função para obter a posição da cabeça
            print(f"Posição da cabeça: {head_pose}")



            # Salva dados no CSV
            with open(csv_path, mode="a", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                timestamp = time.strftime("%H:%M:%S %d/%m/%Y")
                csv_writer.writerow([timestamp, audio_class, audio_score, audio_group, window_data['Janela Ativa'], window_data['URL'], head_pose])

            # Tempo entre cada iteração do loop principal
            time.sleep(5) 

    except KeyboardInterrupt:
        print("Execução interrompida pelo usuário.")
    except Exception as e:
        print(f"Erro ao iniciar threads: {e}")
    finally:
        head_service.stop()  # Libera recursos do módulo de cabeça

if __name__ == "__main__":
    main()

