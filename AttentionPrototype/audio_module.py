import argparse
import time
from mediapipe.tasks import python
from mediapipe.tasks.python.audio.core import audio_record
from mediapipe.tasks.python.components import containers
from mediapipe.tasks.python import audio
from threading import Event

class AudioService:
    last_inference_time = None
    interval_between_inference  = None
    pause_time  = None
    record  = None 
    audio_data = None
    classifier = None
    score_threshold = 0.5
    buffer_size = 15600
    latest_result = None
    result_ready = Event()
    
    def run(self, model: str, max_results: int, score_threshold: float, overlapping_factor: float) -> None:
        """Executa continuamente a inferência em dados de áudio adquiridos do dispositivo.
        Args:
        model: Nome do modelo TFLite de classificação de áudio.
        max_results: Número máximo de resultados de classificação a serem exibidos.
        score_threshold: O limiar de pontuação dos resultados de classificação.
        overlapping_factor: Fator de sobreposição entre inferências adjacentes.
        """

        if (overlapping_factor <= 0) or (overlapping_factor >= 1.0):
            raise ValueError('Overlapping factor must be between 0 and 1.')

        if (score_threshold < 0) or (score_threshold > 1.0):
            raise ValueError('Score threshold must be between (inclusive) 0 and 1.')

        # Definindo o caminho do arquivo CSV
        csv_path = "/Users/cassianosouza/Projects/MediaPipe-audio/data/audio_classifications.csv"

        # Função de callback para salvar os resultados no CSV
        def save_result(result: audio.AudioClassifierResult, timestamp_ms: int):
            self.latest_result = result,
            self.result_ready.set()


        self.score_threshold = score_threshold

        # Inicializa o modelo de classificação de áudio
        base_options = python.BaseOptions(model_asset_path=model)
        options = audio.AudioClassifierOptions(
            base_options=base_options,
            running_mode=audio.RunningMode.AUDIO_STREAM,
            max_results=max_results,
            score_threshold=score_threshold,
            result_callback=save_result
        )
        classifier = audio.AudioClassifier.create_from_options(options)

        # Configura o gravador de áudio
        sample_rate, num_channels = 16000, 1
        audio_format = containers.AudioDataFormat(num_channels, sample_rate)
        record = audio_record.AudioRecord(num_channels, sample_rate, self.buffer_size)
        audio_data = containers.AudioData(self.buffer_size, audio_format)

        # Define o intervalo entre inferências
        input_length_in_second = float(len(audio_data.buffer)) / audio_data.audio_format.sample_rate
        interval_between_inference = input_length_in_second * (1 - overlapping_factor)
        pause_time = interval_between_inference * 0.1
        last_inference_time = time.time()

        # Inicia a gravação de áudio em segundo plano
        record.start_recording()

        self.last_inference_time = last_inference_time
        self.interval_between_inference  = interval_between_inference
        self.pause_time  = pause_time
        self.record  = record 
        self.audio_data = audio_data
        self.classifier = classifier

    def startEngine(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--model', help='Nome do modelo de classificação de áudio.', required=False, default='yamnet.tflite')
        parser.add_argument('--maxResults', help='Número máximo de resultados a serem exibidos.', required=False, default=1)
        parser.add_argument('--overlappingFactor', help='Fator de sobreposição entre inferências adjacentes. Valor entre (0, 1)', required=False, default=0.5)
        parser.add_argument('--scoreThreshold', help='Limiar de pontuação dos resultados de classificação.', required=False, default=0.0)
        args = parser.parse_args()

        self.run(args.model, int(args.maxResults), float(args.scoreThreshold), float(args.overlappingFactor))


    def processorAudio(self):
        try:
            now = time.time()
            diff = now - self.last_inference_time
            if diff < self.interval_between_inference:
                time.sleep(self.pause_time)
                #return None
            self.last_inference_time = now

            # Carrega e classifica os dados de áudio
            data = self.record.read(self.buffer_size)
            self.audio_data.load_from_array(data)
            self.result_ready.clear()
            print("laste_inference_time: ", self.last_inference_time)
            print("interval_between_inference: ", self.interval_between_inference)
            print("round: ", round(self.last_inference_time * 1000))
            print("pause time: ", self.pause_time)
            self.classifier.classify_async(self.audio_data, round(self.last_inference_time * 1000))
        except KeyboardInterrupt:
            print("Processo interrompido pelo usuário.")
    
    def stopRecording(self):
        self.record.stop_recording()
        print("Gravação de áudio encerrada.")
    