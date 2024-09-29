import cv2
import tkinter as tk
import threading
import psycopg2
import requests
import imutils
import time
import json
from tkinter import messagebox
from tkinter import ttk
from tkinter import PhotoImage
from datetime import datetime
from PIL import Image, ImageTk

# -----------------------  DEFINICION FUNCIONES FUNDAMENTALES -----------------------
def parametroRut(urlC_formato):
    """
        Objetivo: capturar el parametro 'RUN' de la URL.
        
        :param urlC_formato: URL con el formato deseado.
        :return: Valor del parametro 'RUN' o None si no se encuentra.
    """
    # Buscar la posición del parámetro 'RUN=' en la URL
    run_start = urlC_formato.find('RUN=')
    if run_start == -1:
        return None
    
    # encuentra el inicio del valor del parametro 'RUN'
    run_start += len('RUN=')
    
    # encuentra el final del valor del parametro 'RUN'
    run_end = urlC_formato.find('&', run_start)
    
    # Si no hay un '&', tomar el valor hasta el final de la URL
    if run_end == -1:
        run_end = len(urlC_formato)
    
    # extraer el valor del parametro 'RUN'
    run_value = urlC_formato[run_start:run_end]
    
    return run_value

def leerConfiguracion():
    """
        Objetivo: leer las credenciales de la base de datos desde un archivo .json.
        
        :return: Diccionario con las credenciales de la base de datos o None si no se pudo leer.
    """
    try:
        with open('creds.json', 'r') as archivo:
            config = json.load(archivo)
        return config
    except Exception as e:
        print("[RAS] Error al leer el archivo de configuración:", e)
        return None

def conexionPosgtresql():
    """
        Objetivo: establecer conexión con la base de datos PostgreSQL.
        
        :return: Objeto de conexión y cursor para ejecutar consultas o None si no se pudo establecer la conexión.
    """
    config = leerConfiguracion()
    if not config:
        print("[POSTGRESQL] No se pudo leer la configuración de la base de datos.")
        return None, None
    try:
        connection = psycopg2.connect(
            database=config['database'],
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port']
        )
        cursor = connection.cursor()
        print("[POSTGRESQL] Conexion exitosa.")
        return connection, cursor
    except (Exception, psycopg2.Error) as error:
        print("[POSTGRESQL] Error al conectar con PostgreSQL.", error)
        return None, None

def cierreConexion(connection, cursor):
    """
        Objetivo: cerrar la conexión con la base de datos PostgreSQL.
        
        :param connection: objeto de conexión a la base de datos. \n
        :param cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida.
        :return: None y mensaje de confirmación si la conexión se cerró correctamente.
    """
    if cursor:
        cursor.close()
    if connection:
        connection.close()
        print("[POSTGRESQL] Conexion con PostgreSQL cerrada.")

# funcion para capturar ultimo registroID y generar el siguiente respectivo
def verificarRegistroID(cursor):
    """
        Objetivo: verificar el último registroID en la tabla RegistroQR y generar el siguiente.
        
        :param cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida.
        :return: nuevo registroID o None si no se pudo obtener el último registroID.
    """
    try:
        # consulta con el ultimo registroID de la tabla
        consult = "SELECT registroID FROM RegistroQR ORDER BY registroID DESC LIMIT 1"
        cursor.execute(consult)
        regID_anterior = cursor.fetchone()
        if regID_anterior:
            ultimo_registro_id = regID_anterior[0]
            # extrae el numero del registroID
            numero_actual = int(ultimo_registro_id.split('-')[1])
            # genera el proximo registroID
            nuevo_numero = numero_actual + 1
            nuevo_registro_id = f'REG-{nuevo_numero}'
        else:
            # si no hay registros, comenzar con REG-1
            nuevo_registro_id = 'REG-1'
        return nuevo_registro_id
    except Exception as e:
        # para casos de mal manejo de datos
        print("[POSTGRESQL] Error al obtener el último registroID:", e) 
        return None

# -----------------------  OBJETO MENU Y DEF.FUNCIONES RESPECTIVAS -----------------------
class Menu:
    def __init__(self, root):
        self.root = root
        # self.root.title("RAS.v1")
        # self.root.state('zoomed')
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)

        # cargar el archivo de imagen del Favicon
        try:
            icon = PhotoImage(file="FaviconUBB.png") 
            root.iconphoto(True, icon)
            self.menu_image = PhotoImage(file="logo_cimubb.png")
             
        except Exception as e:
            print("[RAS] Error al cargar el icono:", e)
            print("[RAS] Error al cargar la imagen del menú:", e)
            self.menu_image = None
        
        # -----------------------  ESTILO BOTONES -----------------------
        # estilo para botones principales
        self.button_style = {
            "font": ("Cascadia code", 18),          # tipo y tamaño de la fuente
            "bg": "#afc5df",                        # color de fondo del botón
            "fg": "black",                          # color del texto del botón
            "relief": "groove",                     # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                                # ancho del borde
            "width": 25,                            # ancho del botón
            "height": 5                             # altura del botón
        }

        # estilo para boton 'Volver'
        self.volver_style = {
            "font": ("Cascadia code", 42), 
            "bg": "#afc5df",                
            "fg": "black",                  
            "relief": "groove",               
            "bd": 7,                        
            "width": 5,                    
            "height": 2,                   
        }

        # estilo para boton 'Guardar'
        self.estilo_guardar = {
            "font": ("Cascadia code", 16),  # tipo y tamaño de la fuente
            "bg": "#afc5df",                # color de fondo del botón
            "fg": "black",                  # color del texto del botón
            "relief": "groove",             # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                        # ancho del borde
            "width": 6,                     # ancho del botón
            "height": 2,                    # altura del botón
        }

        # estilo para boton 'Registrar QR'
        self.estilo_RegQR = {
            "font": ("Cascadia code", 16),          # tipo y tamaño de la fuente
            "bg": "#afc5df",                        # color de fondo del botón
            "fg": "black",                          # color del texto del botón
            "relief": "groove",                     # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                                # ancho del borde
            "width": 20,                            # ancho del botón
            "height": 2,                            # altura del botón
        }

        # estilo de boton instancia Invitado
        self.estilo_boton_inv = {
        "font": ("Cascadia code", 14),
        "bg": "#afc5df",
        "fg": "black",
        "relief": "groove",
        "bd": 5,
        "width": 14,
        "height": 4
        }

        # -----------------------  GUI  -----------------------
        # creacion de marco para centrar los botones
        self.frame = tk.Frame(self.root, bg="#ebf1f7")
        self.frame.pack(fill="both", expand=True)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # ajusar el grid del root para que el frame este centrado
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # creacion de botones iniciales (decidir si cambiar todos aqui o por intancias)
        self.crear_usuario_btn = tk.Button(self.frame, text="Crear\nUsuario", command=self.crearUsuario, **self.button_style)

        self.registro_asistencia_btn = tk.Button(self.frame, text="Registro\nAsistencia", command=self.registroAsistencia, **self.button_style)

        self.invitado_btn = tk.Button(self.frame, text="Invitado", command=self.invitado, **self.button_style)

        self.alumfunc = tk.Button(self.frame, text="Usuario", command=self.usuario,**self.button_style)

        # boton para volver al menu principal con símbolo
        self.volver_btn = tk.Button(self.frame, text="🏠", command=self.menuPrincipal, **self.volver_style)

        # Reloj en la parte inferior izquierda
        self.reloj_label = tk.Label(self.frame, font=("Cascadia code", 48), bg="#ebf1f7", fg="black", relief="flat", wraplength=500)
        self.qr_label = tk.Label(self.frame, text="QR no detectado", font=("Cascadia code", 24), bg="#ebf1f7", fg="black", relief="flat")
        
        # -----------------------  INICIALIZACION VARS -----------------------
        # inicializar cámara
        # self.inicializarCamara()
        
        # self.capture = cv2.VideoCapture(0)
        # if not self.capture.isOpened():
        #     print("No se pudo abrir la cámara")
        
        self.video_label = tk.Label(self.frame, background="gray")
        
        # inicializar variables para segundo plano y QR
        self.running = False
        self.hilo = None
        self.qr_info = None
        self.qr_date = None
        self.qr_time = None
        self.qrCodeDetector = cv2.QRCodeDetector()
        
        # Mostrar botones en el menú principal
        self.menuPrincipal()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # self.root.protocol("WM_DELETE_WINDOW", self.on_closing)   

    # -----------------------  INSTANCIAS GUI -----------------------
    def menuPrincipal(self):
        if self.running:
            self.detenerCamara()
        # limpiar el frame
        for widget in self.frame.winfo_children():
            widget.grid_forget()
        
        # Asegurarse de que el botón "Volver" no esté visible en el menú principal
        self.volver_btn.grid_forget()

        # ajustar los grid dentro del frame para que los widgets se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Si la imagen está cargada (Logo CIMUBB)
        if self.menu_image:
            self.image_label = tk.Label(self.frame, image=self.menu_image, bg="#afc5df")
            self.image_label.grid(row=1, column=0, padx=10, pady=10, sticky="n")

        # texto bienvenida
        self.texto_label = tk.Label(self.frame, text="Bienvenido al Sistema de\nRegistro de Asitencia CIMUBB",
                                    font=("Cascadia code", 48), bg="#ebf1f7", fg="black", relief="flat")
        self.texto_label.grid(row=2, column=0, padx=10, pady=10, sticky="n")
        
        self.reloj_label.grid(row=3, column=0, padx=10, pady=10)
        self.actualizarReloj()
        
        # botones principales
        self.alumfunc.grid(row=3, column=0, padx=240, pady=10, sticky="nw")
        self.invitado_btn.grid(row=3, column=0, padx=240, pady=10, sticky="ne")

    def usuario(self):
        # limpiar el frame
        for widget in self.frame.winfo_children():
            widget.grid_forget() 

        # ajustar los grid dentro del frame para que los widgets se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # estilo del label para la pregunta de ingreso de credenciales
        self.texto_label = tk.Label(self.frame, text="Por favor, escanee su QR para validar sus credenciales",
                                    font=("Cascadia code", 24), bg="#ebf1f7", fg="black", relief="flat")
        self.texto_label.grid(row=1, column=0, padx=10, pady=10, sticky="s")

        # boton para validar credenciales a traves de QR
        # falta implementar logica de validacion con el QR escaneado
        self.verificarRUT = tk.Button(self.frame, text="Escanear QR", command=self.instanciaQR,**self.estilo_RegQR)
        self.verificarRUT.grid(row=2, column=0, padx=10, pady=10, sticky="s")

        self.reloj_label.grid(row=3, column=0, padx=10, pady=10)        
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")
    
    def invitado(self):
        # limpiar el frame
        for widget in self.frame.winfo_children():
            widget.grid_forget() 

        # ajustar los grid dentro del frame para que los widgets se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # estilo del label para la instancia de pregunta al invitado
        self.texto_datos = tk.Label(self.frame, text="¿Desea ingresar sus datos?",
                                    font=("Cascadia code", 26), bg="#ebf1f7", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_datos.grid(row=1, column=0, padx=10, pady=10, sticky="s")

        # botones para confirmar o rechazar el ingreso de datos
        self.boton_si = tk.Button(self.frame, text="SI", command=self.crearUsuario, **self.estilo_boton_inv) 
        self.boton_si.grid(row=2, column=0, padx=450, pady=10, sticky="sw")
        self.boton_no = tk.Button(self.frame, text="NO", command=self.registroAsistencia, **self.estilo_boton_inv)
        self.boton_no.grid(row=2, column=0, padx=450, pady=10, sticky="se")

        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")
    
    # arreglar y mejorar instancia
    def instanciaQR(self):
        # limpiar el frame
        for widget in self.frame.winfo_children():
            widget.grid_forget() 

        # ajustar los grid dentro del frame para que los widgets se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Crear un Label para mostrar el video en el Frame
        self.video_label.grid(row=2, column=0, padx=10, pady=10, sticky="s")
        self.qr_label.grid(row=1, column=0, padx=10, pady=10, sticky="n")
        self.inicializarCamara()
        self.iniciarCamara()
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")
        
    def crearUsuario(self):
        # limpiar el frame
        for widget in self.frame.winfo_children():
            widget.grid_forget() 

        # ajustar los grid dentro del frame para que los widgets se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # messagebox.showinfo("Crear Usuario", "Función Crear Usuario aún no implementada")
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")

    def registroAsistencia(self):
        # Limpiar los widgets del frame
        for widget in self.frame.winfo_children():
            widget.grid_forget()

        # Configurar el grid dentro del frame para que los widgets se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # estilo del label para la instancia de pregunta al invitado
        self.texto_activdad = tk.Label(self.frame, text="Seleccione la actividad (motivo de ingreso)",
                                    font=("Cascadia code", 28), bg="#ebf1f7", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_activdad.grid(row=0, column=0, padx=10, pady=10, sticky="")

        # lista de opciones
        opciones = ["...", "Practica", "Investigacion", "Trabajo de Titulo", "Asignatura", "Asistencia Tecnica", 
                    "Transferencia Tecnologica", "Salida del Laboratorio"]
        self.variable = tk.StringVar(self.root)
        self.variable.set(opciones[0])

        # Crear menú desplegable usando tk.OptionMenu para mantener el estilo
        self.menu_desplegable = tk.OptionMenu(self.frame, self.variable, *opciones)
        self.menu_desplegable.config(bg="#afc5df", fg="black", font=("Cascadia code", 14), relief="groove", bd=7, height=3, width=120)
        self.menu_desplegable.grid(row=1, column=0, padx=10, pady=10, sticky="n")

         # Acceder al widget del menú desplegable y modificar el estilo
        self.menu = self.menu_desplegable["menu"]
        self.menu.config(font=("Cascadia code", 24))  # cambia el tamaño de la fuente del menú desplegable

        # Botón para guardar la selección
        self.boton_guardar = tk.Button(self.frame, text="💾", command=self.guardarSeleccion, **self.estilo_guardar)
        self.boton_guardar.grid(row=2, column=0, padx=10, pady=10, sticky="n") 
        
        # Botón para iniciar la cámara
        self.boton_camara = tk.Button(self.frame, text="Registrar QR", command=self.validarEIniciarCamara, **self.estilo_RegQR)
        self.boton_camara.grid(row=2, column=0, padx=260, pady=10, sticky="ne")

        self.reloj_label.grid(row=3, column=0, padx=10, pady=10)  
        # Mostrar el botón "Volver" en la parte inferior derecha
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")  # Colocar en la última fila, esquina inferior derecha

    def guardarSeleccion(self):
        seleccion = self.variable.get()
        # Puedes utilizar esta variable según tus necesidades
        print(f"Selección guardada: {seleccion}")
        return seleccion

    # -----------------------  FUNCIONES PARA CONTROL DE CAMARA -----------------------
    def validarEIniciarCamara(self):
        seleccion = self.variable.get()
        if seleccion == "...":
            messagebox.showwarning("Advertencia", "Por favor, seleccione una actividad antes de registrar el QR.")
        else:
            self.iniciarCamara()
    
    def inicializarCamara(self):
        self.capture = cv2.VideoCapture(0, cv2.CAP_DSHOW) # , cv2.CAP_DSHOW
        if not self.capture.isOpened():
            print("[OPENCV] No se pudo abrir la cámara.")
            self.capture = None
            return False
        return True
    
    def iniciarCamara(self):
        if not self.running:
            self.running = True
            self.hilo = threading.Thread(target=self.mostrarVideo)
            self.hilo.start()
        
    def mostrarVideo(self):
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                print("[OPENCV] No se pudo capturar el video")
                break        
            
            frame = cv2.flip(frame, 1)
            frame = imutils.resize(frame, width=640)
            frame = imutils.resize(frame, height=480)
            ImagenCamara = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(ImagenCamara)
            img = ImageTk.PhotoImage(image=im)
            self.video_label.image = img
            self.video_label.configure(image=img)
            
            ret_qr, decoded_info, points, _ = self.qrCodeDetector.detectAndDecodeMulti(frame)
            if ret_qr:
                for info, point in zip(decoded_info, points):
                    if info:
                        self.qr_info = str(info)
                        self.qr_label.config(text=self.qr_info)

        self.running = False
    
    def mostrarVideoYAnalizar(self):
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                print("[OPENCV] No se pudo capturar el video")
                break        

            ret_qr, decoded_info, points, _ = self.qrCodeDetector.detectAndDecodeMulti(frame)
            if ret_qr:
                for info, point in zip(decoded_info, points):
                    if info:
                        now = datetime.now()
                        color = (0, 255, 0)
                        self.qr_info = str(info)
                        self.qr_date = now.strftime('%d-%m-%Y')
                        self.qr_time = now.strftime('%H:%M:%S')
                        self.detenerCamara()
                        messagebox.showinfo("RAS.v1", "QR detectado correctamente")
                    else:
                        color = (0, 0, 255)
                    frame = cv2.polylines(frame, [point.astype(int)], True, color, 8)

            cv2.imshow('[OPENCV] Detector de codigos QR', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.running = False
        cv2.destroyAllWindows()

    def detenerCamara(self):
        self.running = False
        if self.capture and self.capture.isOpened():
            self.capture.release()
    
    def reanudarCamara(self):
        if not self.running:
            self.inicializarCamara()
            self.iniciarCamara()
    
    def on_closing(self):
        if self.running:
            self.running = False
            if self.hilo and self.hilo.is_alive():
                self.hilo.join()

        if self.capture and self.capture.isOpened():
            self.capture.release()

        self.root.destroy()

    def actualizarReloj(self):
        """
        La función `actualizarReloj` actualiza el reloj_label con la hora y fecha actual..
        """
        tiempoActual = time.strftime("%H:%M:%S %d/%m/%Y")  # Formato: Día/Mes/Año Hora:Minuto:Segundo
        self.reloj_label.config(text=tiempoActual)
        self.root.after(1000, self.actualizarReloj)
# -----------------------  MAIN -----------------------
if __name__ == "__main__":
    # Crear la ventana principal
    root = tk.Tk()
    root.configure(bg="#afc5df")
    root.bind("<Escape>", lambda e: root.quit())
    app = Menu(root)

    # Iniciar el bucle principal de la interfaz gráfica
    actualizar_reloj = lambda: app.reloj_label.config(text=datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
    root.mainloop()
    
    # info_QR = app.qr_info
    # rutQR = parametroRut(info_QR)
    # fechaQR = app.qr_date
    # horaQR = app.qr_time

    # print(f"RUT escaneado: {rutQR}")
    # print(f"Fecha registrada: {fechaQR}")
    # print(f"Hora registrada: {horaQR}")

    # # conexion a la BD
    # conexion, cursor = conexionPosgtresql()
    
    # # hacer de esto una funcion
    # if conexion and cursor:
    #     try:
    #         # verificar registros
    #         nuevo_registro = verificarRegistroID(cursor)

    #         # mandar datos del QR a la BD
    #         ins_1 = "INSERT INTO Usuario(RUN, nombre_completo) VALUES (%s, %s)"
    #         ins_2 = "INSERT INTO RegistroQR(registroID, fecha, hora) VALUES (%s, %s, %s)"  
    #         #auxQR = '21456789-4'
    #         cursor.execute(ins_1,(rutQR,"Alumno3"))
    #         cursor.execute(ins_2, (nuevo_registro,fechaQR, horaQR))

    #         #mandar datos ya registrados a la tabla Ingreso 
    #         ins_3 = "INSERT INTO Ingreso (RUN, registroID) VALUES (%s, %s)"
    #         cursor.execute(ins_3, (rutQR,nuevo_registro)) 

    #         # Confirmar los cambios
    #         conexion.commit()
    #         print("Datos guardados correctamente en la base de datos.")
    #     except Exception as e:
    #         print("Error al guardar los datos:", e)
    #     finally:
    #         # Cerrar la conexión
    #         cierreConexion(conexion, cursor)