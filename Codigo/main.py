import cv2
import tkinter as tk
import threading
import psycopg2
import requests
import time
from tkinter import messagebox
from datetime import datetime

# URL aplicación web de Google Apps Script
web_app_url = 'https://script.google.com/macros/s/AKfycbx50YUb6m-niROa5dBVo9UixE9EFHNkl7H5NC-MPSuf4cfJ5eETcAQaDiq5Wd1LZdXS/exec'

# ----DEFINCION FUNCIONES----

# funcion para capturar parametro deseado (RUT en este caso)
def parametro_rut(urlC_formato):
    # Buscar la posición del parámetro 'RUN=' en la URL
    run_start = urlC_formato.find('RUN=')
    if run_start == -1:
        return None
    
    # Encontrar el inicio del valor del parámetro 'RUN'
    run_start += len('RUN=')
    
    # Encontrar el final del valor del parámetro 'RUN'
    run_end = urlC_formato.find('&', run_start)
    
    # Si no hay un '&', tomar el valor hasta el final de la URL
    if run_end == -1:
        run_end = len(urlC_formato)
    
    # Extraer el valor del parámetro 'RUN'
    run_value = urlC_formato[run_start:run_end]
    
    return run_value

# funcion para establecer conexion python - postgreSQL  (verificar credenciales)
def conexion_posgtresql():
    try:
        connection = psycopg2.connect(
            database='pruebas_1',
            user='basti',
            password='basti',
            host='localhost',
            port='5432'
        )
        cursor = connection.cursor()
        return connection, cursor
    except (Exception, psycopg2.Error) as error:
        print("Error al conectar con PostgreSQL", error)
        return None, None

# funcion para cerrar la conexion con postgreSQL establecida
def cierre_conexion(connection, cursor):
    if cursor:
        cursor.close()
    if connection:
        connection.close()
        print("Conexion con PostgreSQL cerrada")

# funcion de Don este
def validarRun(run):
    return "NO"

# funcion de Don este
def implementacionConSpreadsheets(run):
    validacion = validarRun(run)
    time.sleep(1)

    # Enviar los datos a la aplicación web de Google Apps Script
    response = requests.post(web_app_url, data={'RUN': run, 'VALIDACION': validacion})
    if response.status_code == 200:
        print("Datos enviados a la aplicación web")
    else:
        print("Error al enviar los datos a la aplicación web")

# funcion para capturar ultimo registroID y generar el siguiente respectivo
def verf_registroID(cursor):
    try:
        # consulta con el último registroID de la tabla
        consult = "SELECT registroID FROM RegistroQR ORDER BY registroID DESC LIMIT 1"
        cursor.execute(consult)
        regID_anterior = cursor.fetchone()
        if regID_anterior:
            ultimo_registro_id = regID_anterior[0]
            # extrae el número del registroID
            numero_actual = int(ultimo_registro_id.split('-')[1])
            # genera el próximo registroID
            nuevo_numero = numero_actual + 1
            nuevo_registro_id = f'REG-{nuevo_numero}'
        else:
            # Si no hay registros, comenzar con REG-1
            nuevo_registro_id = 'REG-1'
        return nuevo_registro_id
    except Exception as e:
        # para casos de mal manejo de datos
        print("Error al obtener el último registroID:", e) 
        return None


# objeto camara
class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RAS.v1")
        self.root.geometry("300x200")
        # inicializar variables
        self.capture = None
        self.running = False
        self.qr_info = None
        self.qr_date = None  
        self.qr_time = None

        # inicializar el detector QR
        self.qrCodeDetector = cv2.QRCodeDetector()

        self.boton = tk.Button(root, text="Abrir Cámara", command=self.iniciar_camara)
        self.boton.pack(expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def inicializar_camara(self):
        # inicializar cámara en segundo plano para reducir el tiempo de espera (opcional)
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print("No se pudo abrir la cámara")
            return False
        return True

    def iniciar_camara(self):
        if not self.running:
            self.running = True
            if self.capture is None or not self.capture.isOpened():
                if not self.inicializar_camara():
                    return
            self.hilo = threading.Thread(target=self.mostrar_video)
            self.hilo.start()

    def mostrar_video(self):
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                print("No se pudo capturar el video") # para controlar el uso de la camara
                break

            # detectar y decodificar QR en el frame
            ret_qr, decoded_info, points, _ = self.qrCodeDetector.detectAndDecodeMulti(frame)
            if ret_qr:
                for info, point in zip(decoded_info, points):
                    if info:
                        now = datetime.now()
                        color = (0, 255, 0)
                        self.qr_info = str(info)  # guarda la info del QR 
                        self.qr_date = now.strftime('%d-%m-%Y')  # Guarda la fecha del QR
                        self.qr_time = now.strftime('%H:%M:%S')
                        self.detener_camara() 
                        self.mostrar_mensaje(info) 
                    else:
                        color = (0, 0, 255)
                    frame = cv2.polylines(frame, [point.astype(int)], True, color, 8)

            # muestra el frame (foto) con el QR detectados (si los hay)
            cv2.imshow('Detector de codigos QR', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.running = False
        cv2.destroyAllWindows()

    def detener_camara(self):
        self.running = False
        if self.capture and self.capture.isOpened():
            self.capture.release()

    def mostrar_mensaje(self, mensaje):
        # muestra el mensaje en la interfaz grafica
        messagebox.showinfo("RAS.v1","QR detectado correctamente")

    def on_closing(self):
        self.detener_camara()
        self.root.destroy()

if __name__ == "__main__":
    # Crear la ventana principal
    root = tk.Tk()
    app = CameraApp(root)

    # Iniciar el bucle principal de la interfaz gráfica
    root.mainloop()

    info_QR = app.qr_info
    rutQR = parametro_rut(info_QR)
    fechaQR = app.qr_date
    horaQR = app.qr_time


    print(f"RUT escaneado: {rutQR}")
    print(f"Fecha registrada: {fechaQR}")
    print(f"Hora registrada: {horaQR}")

    # Enviar a spreadsheets
    # implementacionConSpreadsheets(rutQR) # Puede que esta funcion haga que tu codigo se relantize porque utilizo time.sleep(1) para simular un proceso de validacion
    
    # conexion a la BD
    conexion, cursor = conexion_posgtresql()
        
    if conexion and cursor:
        try:
            # verificar registros
            nuevo_registro = verf_registroID(cursor)

            # mandar datos del QR a la BD
            ins_1 = "INSERT INTO Usuario(RUN, nombre_completo) VALUES (%s, %s)"
            ins_2 = "INSERT INTO RegistroQR(registroID, fecha, hora) VALUES (%s, %s, %s)"  
            #auxQR = '21456789-4'
            cursor.execute(ins_1,(rutQR,"Alumno3"))
            cursor.execute(ins_2, (nuevo_registro,fechaQR, horaQR))

            #mandar datos ya registrados a la tabla Ingreso 
            ins_3 = "INSERT INTO Ingreso (RUN, registroID) VALUES (%s, %s)"
            cursor.execute(ins_3, (rutQR,nuevo_registro)) 

            # Confirmar los cambios
            conexion.commit()
            print("Datos guardados correctamente en la base de datos.")
        except Exception as e:
            print("Error al guardar los datos:", e)
        finally:
            # Cerrar la conexión
            cierre_conexion(conexion, cursor)