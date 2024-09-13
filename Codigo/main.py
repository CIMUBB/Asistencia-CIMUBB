import cv2
import tkinter as tk
import threading
import psycopg2
import requests
import time
import json
from tkinter import messagebox
from tkinter import ttk
from tkinter import PhotoImage
from datetime import datetime

# ----DEFINCION FUNCIONES----

# funcion para capturar parametro deseado (RUT en este caso)
def parametro_rut(urlC_formato):
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

# funcion para leer credenciales del .json correspondiente
def leer_configuracion():
    try:
        with open('creds.json', 'r') as archivo:
            config = json.load(archivo)
        return config
    except Exception as e:
        print("Error al leer el archivo de configuración:", e)
        return None

# funcion para establecer conexion python - postgreSQL  (verificar credenciales)
def conexion_posgtresql():
    config = leer_configuracion()
    if not config:
        print("No se pudo leer la configuración de la base de datos.")
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

# funcion para capturar ultimo registroID y generar el siguiente respectivo
def verf_registroID(cursor):
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
        print("Error al obtener el último registroID:", e) 
        return None

# objeto Menu
class Menu:
    def __init__(self, root):
        self.root = root
        self.root.title("RAS.v1")
        self.root.state('zoomed')

        # cargar el archivo de imagen del Favicon
        try:
            icon = PhotoImage(file="FaviconUBB.png")  
            root.iconphoto(True, icon)
            self.menu_image = PhotoImage(file="logo_cimubb.png")
            
        except Exception as e:
            print("Error al cargar el icono:", e)
            print("Error al cargar la imagen del menú:", e)
            self.menu_image = None
            
        # estilo para botones
        self.button_style = {
            "font": ("Cascadia code", 18),  # tipo y tamaño de la fuente
            "bg": "#afc5df",                        # color de fondo del botón
            "fg": "black",                          # color del texto del botón
            "relief": "groove",                     # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                                # ancho del borde
            "width": 30,                            # ancho del botón
            "height": 6                             # altura del botón
        }

        # estilo para boton 'Volver'
        self.volver_style = {
            "font": ("Cascadia code", 14), 
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
            "bd": 7,                       # ancho del borde
            "width": 6,                     # ancho del botón
            "height": 2,                    # altura del botón
        }

        # estilo para boton 'Registrar QR'
        self.estilo_RegQR = {
            "font": ("Cascadia code", 16),  # tipo y tamaño de la fuente
            "bg": "#afc5df",                        # color de fondo del botón
            "fg": "black",                          # color del texto del botón
            "relief": "groove",                     # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                                # ancho del borde
            "width": 20,                            # ancho del botón
            "height": 2,                            # altura del botón
        }

        # creacion de marco para centrar los botones
        self.frame = tk.Frame(self.root, bg="#ebf1f7")
        self.frame.pack(fill="both", expand=True)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # ajusar el grid del root para que el frame este centrado
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # creacion de botones iniciales
        self.crear_usuario_btn = tk.Button(self.frame, text="Crear\nUsuario", command=self.crear_usuario, **self.button_style)
        #self.crear_usuario_btn.grid(row=2, column=0, padx=10, pady=10, sticky="nw")

        self.registro_asistencia_btn = tk.Button(self.frame, text="Registro\nAsistencia", command=self.iniciar_registro_asistencia, **self.button_style)
        #self.registro_asistencia_btn.grid(row=2, column=0, padx=10, pady=10, sticky="n")

        self.invitado_btn = tk.Button(self.frame, text="Invitado", command=self.invitado, **self.button_style)
        #self.invitado_btn.grid(row=2, column=0, padx=10, pady=10, sticky="ne")

        # boton para volver al menu principal con símbolo
        self.volver_btn = tk.Button(self.frame, text="↩", command=self.mostrar_menu_principal, **self.volver_style)

        # Mostrar botones en el menú principal
        self.mostrar_menu_principal()
        

        # inicializar cámara
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print("No se pudo abrir la cámara")

        self.running = False
        self.hilo = None
        self.qr_info = None
        self.qr_date = None
        self.qr_time = None
        self.qrCodeDetector = cv2.QRCodeDetector()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)   

    def mostrar_menu_principal(self):
        # Limpiar el frame
        for widget in self.frame.winfo_children():
            widget.grid_forget()

        # Si la imagen está cargada, mostrarla
        if self.menu_image:
            self.image_label = tk.Label(self.frame, image=self.menu_image, bg="#afc5df")
            self.image_label.grid(row=1, column=0, padx=10, pady=10, sticky="n")

        # Agregar un texto en la fila 2
        self.texto_label = tk.Label(self.frame, text="Bienvenido al Sistema de\nRegistro de Asitencia CIMUBB",
                                    font=("Cascadia code", 24, "bold", "italic"), bg="#ebf1f7", fg="black", relief="flat")
        self.texto_label.grid(row=2, column=0, padx=10, pady=10, sticky="n")

        # Volver a colocar los botones en sus posiciones
        self.crear_usuario_btn.grid(row=3, column=0, padx=50, pady=10, sticky="nw")
        self.registro_asistencia_btn.grid(row=3, column=0, padx=10, pady=10, sticky="n")
        self.invitado_btn.grid(row=3, column=0, padx=50, pady=10, sticky="ne")

        # ajustar el grid del frame para que los botones se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Asegurarse de que el botón "Volver" no esté visible en el menú principal
        self.volver_btn.grid_forget()  

    def crear_usuario(self):
        for widget in self.frame.winfo_children():
            widget.grid_forget()

        messagebox.showinfo("Crear Usuario", "Función Crear Usuario aún no implementada")
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")

    def iniciar_registro_asistencia(self):
        # Limpiar los widgets del frame
        for widget in self.frame.winfo_children():
            widget.grid_forget()

        # Configurar el grid dentro del frame para que los widgets se expandan
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Estilo de la etiqueta para seleccionar motivo de ingreso 
        estilo_etiqueta = {
            "text": "Seleccione Actividad (motivo ingreso)",
            "anchor": "center",
            "font": ("Cascadia code", 26, "bold", "italic"),
            "bg": "#ebf1f7",
            "fg": "black",
            "bd": 7,
            "relief": "flat"
        }

        self.etiqueta = tk.Label(self.frame, **estilo_etiqueta)

        self.etiqueta.grid(row=0, column=0, padx=20, pady=20, sticky="")

        # Crear lista de opciones
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
        self.boton_guardar = tk.Button(self.frame, text="💾", command=self.guardar_seleccion, **self.estilo_guardar)
        self.boton_guardar.grid(row=2, column=0, padx=10, pady=10, sticky="n") 
        
        # Botón para iniciar la cámara
        self.boton_camara = tk.Button(self.frame, text="Registrar QR", command=self.validar_y_iniciar_camara, **self.estilo_RegQR)
        self.boton_camara.grid(row=2, column=0, padx=260, pady=10, sticky="ne")

        # Mostrar el botón "Volver" en la parte inferior derecha
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")  # Colocar en la última fila, esquina inferior derecha

    def validar_y_iniciar_camara(self):
        seleccion = self.variable.get()
        if seleccion == "...":
            messagebox.showwarning("Advertencia", "Por favor, seleccione una actividad antes de registrar el QR.")
        else:
            self.iniciar_camara()
    
    def guardar_seleccion(self):
        seleccion = self.variable.get()
        # Puedes utilizar esta variable según tus necesidades
        print(f"Selección guardada: {seleccion}")
        return seleccion

    def invitado(self):
        for widget in self.frame.winfo_children():
            widget.grid_forget()

        # estilo de la etiqueta para la instancia de pregunta al invitado
        estilo_etiquetaINV = {
            "text": "¿Desea ingresar sus datos?",
            "anchor": "center",
            "font": ("Cascadia code", 26, "bold", "italic"),
            "bg": "#ebf1f7",
            "fg": "black",
            "bd": 7,
            "relief": "flat"
        }

        # estilo de botones 
        estilo_boton = {
        "font": ("Cascadia code", 14),
        "bg": "#afc5df",
        "fg": "black",
        "relief": "groove",
        "bd": 5,
        "width": 14,
        "height": 4
        }

        self.etiquetaINV = tk.Label(self.frame, **estilo_etiquetaINV)
        self.etiquetaINV.grid(row=1, column=0, padx=20, pady=20, sticky="s")
        self.boton_si = tk.Button(self.frame, text="SI", command=self.crear_usuario, **estilo_boton) 
        self.boton_si.grid(row=2, column=0, padx=450, pady=10, sticky="sw")
        self.boton_no = tk.Button(self.frame, text="NO", command=self.iniciar_registro_asistencia, **estilo_boton)
        self.boton_no.grid(row=2, column=0, padx=450, pady=10, sticky="se")

        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")

    def iniciar_camara(self):
        if not self.running:
            self.running = True
            self.hilo = threading.Thread(target=self.mostrar_video)
            self.hilo.start()

    def mostrar_video(self):
        while self.running:
            ret, frame = self.capture.read()
            if not ret:
                print("No se pudo capturar el video")
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
                        self.detener_camara()
                        self.mostrar_mensaje(info)
                    else:
                        color = (0, 0, 255)
                    frame = cv2.polylines(frame, [point.astype(int)], True, color, 8)

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
        messagebox.showinfo("RAS.v1", "QR detectado correctamente")

    def on_closing(self):
        if self.running:
            self.running = False
            if self.hilo and self.hilo.is_alive():
                self.hilo.join()

        if self.capture and self.capture.isOpened():
            self.capture.release()

        self.root.destroy()


if __name__ == "__main__":
    # Crear la ventana principal
    root = tk.Tk()
    root.configure(bg="#afc5df")
    app = Menu(root)

    # Iniciar el bucle principal de la interfaz gráfica
    root.mainloop()
    
    info_QR = app.qr_info
    rutQR = parametro_rut(info_QR)
    fechaQR = app.qr_date
    horaQR = app.qr_time

    print(f"RUT escaneado: {rutQR}")
    print(f"Fecha registrada: {fechaQR}")
    print(f"Hora registrada: {horaQR}")

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