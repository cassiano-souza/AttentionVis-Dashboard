import cv2
import mediapipe as mp
import numpy as np
import time


#baseado em: https://github.com/niconielsen32
#artigo: https://medium.com/@jaykumaran2217/real-time-head-pose-estimation-facemesh-with-mediapipe-and-opencv-a-comprehensive-guide-b63a2f40b7c6


class HeadService:
    def __init__(self):
        """Inicializa os serviços necessários para o processamento da cabeça."""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        self.drawing_spec = mp.solutions.drawing_utils.DrawingSpec(thickness=1, circle_radius=1)
        self.cap = cv2.VideoCapture(1) # Abre a captura de vídeo da webcam
        self.latest_result = None # Armazena o resultado mais recente


    def process_frame(self):
        """Processa um frame da câmera."""
        success, image = self.cap.read()
        if not success:
            return "No Frame Captured"

        start = time.time()  # Corrigido: adicionado parênteses

        # Flip the image horizontally for a later selfie-view display
        # Also convert the color space from BGR to RGB
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)

        # To improve performance
        image.flags.writeable = False

        # Get the result
        results = self.face_mesh.process(image)

        if not results.multi_face_landmarks:
            return "Sem Detecção de Rosto"

        # To improve performance
        image.flags.writeable = True

        # Convert the color space from RGB to BGR
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        for face_landmarks in results.multi_face_landmarks:
            face_2d = []
            face_3d = []
            img_h, img_w, _ = image.shape  # Obtém dimensões do frame

            # Coleta os marcos faciais necessários para análise
            for idx, lm in enumerate(face_landmarks.landmark):
                if idx in [33, 263, 1, 61, 291, 199]:
                    x, y = int(lm.x * img_w), int(lm.y * img_h)
                    # Get the 2D Coordinates
                    face_2d.append([x, y])
                    # Get the 3D Coordinates
                    face_3d.append([x, y, lm.z])

            # Converte para array NumPy
            face_2d = np.array(face_2d, dtype=np.float64)  
            face_3d = np.array(face_3d, dtype=np.float64)

            # Matriz de câmera
            focal_length = 1 * img_w
            cam_matrix = np.array([[focal_length, 0, img_h / 2],
                                   [0, focal_length, img_w / 2],
                                   [0, 0, 1]])
             # The distortion parameters
            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            # Resolve o problema PnP para calcular ângulos
            success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
             # Get rotational matrix
            rmat = cv2.Rodrigues(rot_vec)
            # Get angles
            angles = cv2.RQDecomp3x3(rmat)

            # Calcula ângulos de inclinação (pitch, yaw, roll)
            x = angles[0] * 360
            y = angles[1] * 360
            z = angles[2] * 360

            # Determina a posição da cabeça com base nos ângulos
            if y < -5:
                return "Olhando para a Esquerda"
            elif y > 5:
                return "Olhando para a Direita"
            elif x < -3:
                return "Olhando para Baixo"
            elif x > 8:
                return "Olhando para Cima"
            else:
                return "Olhando para Frente"
            
    def run_head_module(self):
        """Executa o módulo de cabeça e atualiza o resultado mais recente."""
        self.latest_result = self.process_frame()  # Processa um frame da webcam
        return self.latest_result  # Retorna o resultado mais recente

    def stop(self):
        """Libera os recursos usados pelo módulo."""
        self.cap.release()  # Libera a captura de vídeo
        

