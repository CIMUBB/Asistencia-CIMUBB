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
from PIL import Image, ImageTk

# -----------------------  DEFINICION FUNCIONES FUNDAMENTALES -----------------------
    
def parametro_rut(urlC_formato):
    """
	Objetivo: capturar el parametro 'RUN' de la URL

	Parametros: 
    
        - urlC_formato: URL con el formato 'http://localhost:5000/?RUN=12345678-9'

	Return: valor del parametro 'RUN' o None si no se encuentra
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

def leer_configuracion():
    """
    Objetivo: leer las credenciales de la base de datos desde un archivo .json

    Return: diccionario con las credenciales de la base de datos o None si no se pudo leer
    """
    try:
        with open('creds.json', 'r') as archivo:
            config = json.load(archivo)
            print("Configuración leída correctamente")
        return config
    except Exception as e:
        print("Error al leer el archivo de configuración:", e)
        return None

def conexion_posgtresql():
    """
    Objetivo: establecer conexión con la base de datos PostgreSQL

    Return: objeto de conexión y cursor para ejecutar consultas o None si no se pudo establecer la conexión
    """
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
        print("Conexión con PostgreSQL establecida")
        return connection, cursor
    except (Exception, psycopg2.Error) as error:
        print("Error al conectar con PostgreSQL", error)
        return None, None

def cierre_conexion(connection, cursor):
    """
    Objetivo: cerrar la conexión con la base de datos PostgreSQL

    Parametros:
        - connection: objeto de conexión a la base de datos
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida
    
    Return: None y mensaje de confirmación si la conexión se cerró correctamente
    """
    if cursor:
        cursor.close()
    if connection:
        connection.close()
        print("Conexion con PostgreSQL cerrada")


def verf_idRegistro(cursor):
    """
    Objetivo: verificar el último id_registro en la tabla Registro y generar el siguiente

    Parametros:
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida

    Return: nuevo id_registro o None si no se pudo obtener el último id_registro
    """
    try:
        # consulta con el ultimo id_registro de la tabla
        consult = "SELECT id_registro FROM Registro ORDER BY id_registro DESC LIMIT 1"
        cursor.execute(consult)
        regID_anterior = cursor.fetchone()
        if regID_anterior:
            ultimo_registro_id = regID_anterior[0]
            # extrae el numero del id_registro
            numero_actual = int(ultimo_registro_id.split('-')[1])
            # genera el proximo id_registro
            nuevo_numero = numero_actual + 1
            nuevo_registro_id = f'REG-{nuevo_numero}'
        else:
            # si no hay registros, comenzar con REG-1
            nuevo_registro_id = 'REG-1'
        return nuevo_registro_id
    except Exception as e:
        # para casos de mal manejo de datos
        print("Error al obtener el último id_registro:", e) 
        return None

def verf_usuario(cursor, rut):
    """
    Objetivo: verificar si un usuario ya se encuentra registrado en la tabla Usuario

    Parametros:
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida
        - rut: RUT del usuario

    Return: True si el usuario ya se encuentra registrado, False si no se encuentra
    """
    try:
        # consulta para verificar si el usuario ya se encuentra registrado
        consulta = "SELECT * FROM Usuario WHERE rut = %s AND tipo_usuario != 'Invitado'"
        cursor.execute(consulta, (rut,))
        if cursor.fetchone():
            return True
        else:
            return False
    except Exception as e:
        print("Error al verificar el usuario:", e)
    
def registrar_usuario(conexion, cursor, rut, nombre_completo, email, tipo_usuario, foto_perfil):
    """
    Objetivo: registrar un nuevo usuario en la tabla Usuario

    Parametros:
        - conexion: objeto de conexión a la base de datos
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida
        - rut: RUT del usuario
        - nombre_completo: nombre completo del usuario
        - email: correo electrónico del usuario
        - tipo_usuario: tipo de usuario (alumno, funcionario, invitado)
        - foto_perfil: ruta de la imagen de perfil del usuario

    Return: True si el registro se realizó correctamente, False si no se pudo registrar
    """
    try:
        #consulta para saber si el usuario ya se encuentra registrado
        consulta_user_reg = "SELECT * FROM Usuario WHERE rut = %s"
        cursor.execute(consulta_user_reg, (rut,))
        if cursor.fetchone():
            return False
        else:
            # consulta para insertar un nuevo usuario en la tabla Usuario
            consulta = "INSERT INTO Usuario (rut, nombre_completo, email, tipo_usuario, foto_perfil) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(consulta, (rut, nombre_completo, email, tipo_usuario, foto_perfil))
            conexion.commit()
            return True
    except Exception as e:
        print("Error al registrar el usuario:", e)

def registrar_ingreso(conexion, cursor, id_registro, fecha_ingreso, hora_ingreso, motivo, rut):
    """
    Objetivo: registrar el ingreso de un usuario en la tabla Registro

    Parametros:
        - conexion: objeto de conexión a la base de datos
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida
        - id_registro: identificador único del registro de ingreso
        - fecha_ingreso: fecha en que se registra el ingreso
        - hora_ingreso: hora en que se registra el ingreso
        - motivo: motivo por el que ingresa el usuario
        - rut: rut del usuario

    Return: True si el registro se realizó correctamente, False si no se pudo registrar
    """
    try: 
        #consulta para saber si el usuario tiene un registro de ingreso previo (salida pendiente)
        consulta_user_ing = "SELECT * FROM Registro WHERE rut = %s AND hora_salida='' AND fecha_salida=''"
        cursor.execute(consulta_user_ing, (rut,))
        if cursor.fetchone():
            return False
        else:
            # consulta para insertar un nuevo registro de ingreso en la tabla Registro
            consulta = "INSERT INTO Registro (id_registro, fecha_ingreso, hora_ingreso, motivo, rut) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(consulta, (id_registro, fecha_ingreso, hora_ingreso, motivo, rut))
            conexion.commit()
            return True
    except Exception as e:
        print("Error al registrar el ingreso:", e)

def registrar_salida(conexion, cursor, fecha_salida, hora_salida, rut):
    """
    Objetivo: registrar la salida de un usuario en la tabla Registro

    Parametros:
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida
        - fecha_salida: fecha en que se registra la salida
        - hora_salida: hora en que se registra la salida
        - id_registro: identificador único del registro de ingreso

    Return: True si el registro se realizó correctamente, False si no se pudo registrar
    """
    try:
        #consulta para obtener el id_registro de la salida pendiente del usuario
        consulta_id_pendiente = "SELECT id_registro FROM Registro WHERE rut = %s AND hora_salida='' AND fecha_salida=''"
        cursor.execute(consulta_id_pendiente, (rut,))
        #obtener el id_registo de la salida pendiente
        id_registro = cursor.fetchone()
        if id_registro:
            #consulta para actualizar la hora y fecha de salida del usuario
            consulta = "UPDATE Registro SET fecha_salida = %s, hora_salida = %s WHERE id_registro = %s"
            cursor.execute(consulta, (fecha_salida, hora_salida, id_registro))
            conexion.commit()
            return True
        else:
            return False
    except Exception as e:
        print("Error al registrar la salida:", e)

# -----------------------  OBJETO MENU Y DEF.FUNCIONES RESPECTIVAS -----------------------
class Menu:
    def __init__(self, root):
        self.root = root
        self.root.title("RASv1")
        self.root.attributes("-fullscreen", True)

        # cargar el archivo de imagen del Favicon
        try:
            icon = PhotoImage(file="FaviconUBB.png")  
            root.iconphoto(True, icon)
            self.menu_image = PhotoImage(file="logo_cimubb.png")
            self.menu_image2 = PhotoImage(file="logoUBB.png")
            
        except Exception as e:
            print("Error al cargar el icono:", e)
            print("Error al cargar la imagen del menú:", e)
            self.menu_image = None
            self.menu_image2 = None
        
        #Establecer conexion con la BD
        self.connection, self.cursor = conexion_posgtresql()

        # -----------------------  ESTILO BOTONES -----------------------
        # estilo para botones principales
        self.button_style = {
            "font": ("Arial", 18),          # tipo y tamaño de la fuente
            "bg": "#91bff8",                      # color de fondo del botón
            "fg": "#ffffff",                          # color del texto del botón
            "relief": "groove",                     # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                                # ancho del borde
            "width": 25,                            # ancho del botón
            "height": 5                             # altura del botón
        }

        # estilo para boton 'Volver'
        self.volver_style = {
            "font": ("Arial", 14), 
            "bg": "#91bff8",                
            "fg": "#ffffff",                  
            "relief": "groove",               
            "bd": 7,                        
            "width": 5,                    
            "height": 2,                   
        }

        # estilo para boton 'Guardar'
        self.estilo_guardar = {
            "font": ("Arial", 16),  # tipo y tamaño de la fuente
            "bg": "#afc5df",                # color de fondo del botón
            "fg": "black",                  # color del texto del botón
            "relief": "groove",             # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                        # ancho del borde
            "width": 6,                     # ancho del botón
            "height": 2,                    # altura del botón
        }

        # estilo para boton 'Registrar QR'
        self.estilo_RegQR = {
            "font": ("Arial", 16),          # tipo y tamaño de la fuente
            "bg": "#afc5df",                        # color de fondo del botón
            "fg": "black",                          # color del texto del botón
            "relief": "groove",                     # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                                # ancho del borde
            "width": 20,                            # ancho del botón
            "height": 2,                            # altura del botón
        }

        # estilo de boton instancia Invitado
        self.estilo_boton_inv = {
        "font": ("Arial", 14),
        "bg": "#afc5df",
        "fg": "black",
        "relief": "groove",
        "bd": 5,
        "width": 14,
        "height": 4
        }

        # -----------------------  GUI  -----------------------
        # creacion de marco para centrar los botones
        self.frame = tk.Frame(self.root, bg="#fafafa")
        self.frame.pack(fill="both", expand=True)
        self.frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        # ajusar el grid del root para que el frame este centrado
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # creacion de botones iniciales (decidir si cambiar todos aqui o por intancias)

        self.registrarIngreso = tk.Button(self.frame, text="Registrar ingreso", command=self.registrar_ingreso, **self.button_style)

        self.registrarSalida = tk.Button(self.frame, text="Registrar salida", command=self.registrar_salida, **self.button_style)

        self.enrolarse = tk.Button(self.frame, text="Enrolarse", command=self.crear_usuario, **self.button_style)
        
        self.volver_btn = tk.Button(self.frame, text="↩", command=self.mostrar_menu_principal, **self.volver_style)

        self.volver_btn_ingreso = tk.Button(self.frame, text="↩", command=self.volver_registrar_ingreso, **self.volver_style)

        # Mostrar botones en el menú principal
        self.mostrar_menu_principal()
        
        # -----------------------  INICIALIZACION VARS -----------------------
        # inicializar cámara
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print("No se pudo abrir la cámara")

        # inicializar variables para segundo plano y QR
        self.running = False
        self.hilo = None
        self.qr_info = None
        self.qr_date = None
        self.qr_time = None
        self.tipo_usario = None
        self.motivo = None
        self.rut = None
        self.nombre_completo = None
        self.email = None
        self.is_registro = None
        self.is_salida = None
        self.qrCodeDetector = cv2.QRCodeDetector()

    # -----------------------  INSTANCIAS GUI -----------------------
    def limpiar_frame(self):
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
    
    def inicializar_vars(self):
        self.qr_info = None
        self.qr_date = None
        self.qr_time = None
        self.tipo_usario = None
        self.motivo = None
        self.rut = None
        self.nombre_completo = None
        self.email = None
        self.is_registro = None
        self.is_salida = None

    def mostrar_menu_principal(self):
        # limpiar el frame
        self.limpiar_frame()

        # inicializar variables
        self.inicializar_vars()

        # Si la imagen está cargada (Logo CIMUBB)
        if self.menu_image:
            # arreglar tamaño
            self.image_label = tk.Label(self.frame, image=self.menu_image2, bg="#ffffff")
            self.image_label.grid(row=0, column=0, padx=10, pady=0, sticky="w")
            self.image_label = tk.Label(self.frame, image=self.menu_image, bg="#ffffff")
            self.image_label.grid(row=1, column=0, padx=10, pady=10, sticky="n")

        #Botones ingreso/salida
        self.registrarIngreso.grid(row=3, column=0, padx=100, pady=10, sticky="nw")
        self.enrolarse.grid(row=3, column=0, padx=10, pady=10, sticky="n")
        self.registrarSalida.grid(row=3, column=0, padx=100, pady=10, sticky="ne")
        self.volver_btn.forget()
    
    def guardar_datos(self, event):
        self.rut = self.entry_rut.get()
        self.nombre_completo = self.entry_nombre.get()
        self.email = self.entry_email.get()
        print(f"RUT: {self.rut}, Nombre: {self.nombre_completo}, Email: {self.email}")
    
    def crear_usuario(self):
        # limpiar el frame
        self.limpiar_frame()

        # RUT
        self.texto_rut = tk.Label(self.frame, text="Rut:",
                                    font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_rut.grid(row=0, column=0, padx=310, pady=10, sticky="w")
        self.entry_rut = tk.Entry(self.frame, font=("Arial", 20), width=60, bg= "#91bff8", fg="#ffffff", relief="groove", justify="center")
        self.entry_rut.grid(row=0, column=0, padx=250, pady=10, sticky="e")
        self.entry_rut.bind("<FocusOut>", self.guardar_datos)
        #establecer un limite de 12 caracteres para el RUT
        self.entry_rut.config(validate="key", validatecommand=(self.entry_rut.register(lambda x: len(x) <= 10), "%P"))

        # Nombre completo
        self.texto_nombre = tk.Label(self.frame, text="Nombre completo:",
                                    font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_nombre.grid(row=1, column=0, padx=220, pady=10, sticky="w")
        self.entry_nombre = tk.Entry(self.frame, font=("Arial", 20), width=55, bg= "#91bff8", fg="#ffffff", relief="groove", justify="center")
        self.entry_nombre.grid(row=1, column=0, padx=250, pady=10, sticky="e")
        self.entry_nombre.bind("<FocusOut>", self.guardar_datos)
        #establecer un limite de 50 caracteres para el nombre

        # Email
        self.texto_email = tk.Label(self.frame, text="Email:",
                                    font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_email.grid(row=2, column=0, padx=290, pady=10, sticky="w")
        self.entry_email = tk.Entry(self.frame, font=("Arial", 20), width=60, bg= "#91bff8", fg="#ffffff", relief="groove", justify="center")
        self.entry_email.grid(row=2, column=0, padx=250, pady=10, sticky="e")
        self.entry_email.bind("<FocusOut>", self.guardar_datos)

        # boton para sacar foto
        self.boton_foto = tk.Button(self.frame, text="Tomar foto", **self.estilo_guardar)
        self.boton_foto.grid(row=3, column=0, padx=10, pady=10, sticky="n")

        # Sacar foto (implementar luego)

        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")       
            
    def guardar_seleccion_usuario(self, seleccion):
        print(f"Seleccionaste tipo de usuario: {seleccion}")
        self.tipo_usuario = seleccion
    
    def guardar_seleccion_motivo(self, seleccion):
        print(f"Seleccionaste motivo de ingreso: {seleccion}")
        self.motivo = seleccion

    def volver_registrar_ingreso(self):
        self.registrar_ingreso()
    
    def marco_camara(self):
        # Crear un Label para mostrar el video en el Frame
            self.label_video = tk.Label(self.frame, bg="#ffffff", relief="flat", height=500, width=700) #cambiar para crear un marco (mejora estetica)
            self.label_video.grid(row=1, column=0, padx=10, pady=10, sticky="s")
            self.iniciar_camara()
    
    def instancia_qr_ingreso(self):
        # limpiar el frame
        self.limpiar_frame()

        # Validar que el usuario haya seleccionado su tipo de usuario y el motivo de ingreso
        tipoUsuario = self.variableUsuario.get()
        motivoIngreso = self.variableMotivo.get()

        if tipoUsuario == "Por favor, seleccione una opción" or motivoIngreso == "Por favor, seleccione una opción":
            messagebox.showwarning("Advertencia", "Por favor, seleccione su tipo de usuario y el motivo de ingreso antes de continuar.")
            self.volver_btn_ingreso.grid(row=3, column=0, padx=10, pady=10, sticky="se")
        else:
            self.marco_camara()
            self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")  

    def registrar_ingreso_bd(self):
        #mandar mensajes de dialogo con las variables pertinentes (borrar luego)
        messagebox.showinfo("variables", f"RUT: {self.rut}\nFecha: {self.qr_date}\nHora: {self.qr_time}\nTipo de usuario: {self.tipo_usuario}\nMotivo de ingreso: {self.motivo}")

        if self.tipo_usuario == "Invitado":
            registrar_usuario(self.connection, self.cursor, self.rut, "", "", self.tipo_usuario, "")
            reg_id = verf_idRegistro(self.cursor)
            reg_ing_inv = registrar_ingreso(self.connection, self.cursor, reg_id, self.qr_date, self.qr_time, self.motivo, self.rut)
            if reg_ing_inv:
                messagebox.showinfo("RASv1", "Registro de invitado exitoso")
                self.mostrar_menu_principal()
            else:
                messagebox.showwarning("RASv1", "Error. El invitado cuenta con una salida pendiente")
                self.mostrar_menu_principal()
        if self.tipo_usuario == "Alumno" or self.tipo_usuario == "Funcionario":
            #verificar si el usuario ya se encuentra registrado en la BD
            user_reg = verf_usuario(self.cursor, self.rut)
            if user_reg:
                reg_id_user = verf_idRegistro(self.cursor)
                reg_ing_user = registrar_ingreso(self.connection, self.cursor, reg_id_user, self.qr_date, self.qr_time, self.motivo, self.rut)
                if reg_ing_user:
                    messagebox.showinfo("RASv1", "Registro de usuario exitoso")
                    self.mostrar_menu_principal()
                else:
                    messagebox.showwarning("RASv1", "Error. El usuario cuenta con una salida pendiente")
                    self.mostrar_menu_principal()
            else:
                messagebox.showwarning("RASv1", "Error. El usuario no se encuentra registrado")
                self.mostrar_menu_principal()

    def registrar_ingreso(self):
        # limpiar el frame
        self.limpiar_frame()

        self.is_registro = True

        self.texto_activdad = tk.Label(self.frame, text="Tipo de usuario:",
                                    font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_activdad.grid(row=1, column=0, padx=280, pady=10, sticky="w")

        opcionesUsuario = ["Alumno", "Funcionario", "Invitado"]
         # Crear menú desplegable con función de callback
        self.variableUsuario = tk.StringVar(self.root)
        self.variableUsuario.set("Por favor, seleccione una opción")
        self.menu_desplegableUsuario = tk.OptionMenu(self.frame, self.variableUsuario, *opcionesUsuario, command=self.guardar_seleccion_usuario)
        self.menu_desplegableUsuario.config(bg="#91bff8", fg="white", font=("Arial", 14), relief="groove", height=2, width=60)
        self.menu_desplegableUsuario.grid(row=1, column=0, padx=250, pady=10, sticky="e")

        # Acceder al widget del menú desplegable y modificar el estilo
        self.menu = self.menu_desplegableUsuario["menu"]
        self.menu.config(font=("Arial", 28))  # cambia el tamaño de la fuente del menú desplegable

        self.texto_motivo = tk.Label(self.frame, text="Motivo de ingreso:",
                                    font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_motivo.grid(row=2, column=0, padx=260, pady=10, sticky="w")

        opcionesMotivo = ["Practica", "Investigacion", "Trabajo de Titulo", "Asignatura", "Asistencia Tecnica", "Transferencia Tecnologica"]
        self.variableMotivo = tk.StringVar(self.root)
        self.variableMotivo.set("Por favor, seleccione una opción")
        self.menu_desplegableMotivo = tk.OptionMenu(self.frame, self.variableMotivo, *opcionesMotivo, command=self.guardar_seleccion_motivo)
        self.menu_desplegableMotivo.config(bg="#91bff8", fg="white", font=("Arial", 14), relief="groove", height=2, width=60)
        self.menu_desplegableMotivo.grid(row=2, column=0, padx=250, pady=10, sticky="e")

        self.registrarQR = tk.Button(self.frame, text="Escanear QR", command=self.instancia_qr_ingreso, **self.estilo_RegQR)
        self.registrarQR.grid(row=3, column=0, padx=10, pady=10)

        # Acceder al widget del menú desplegable y modificar el estilo
        self.menu = self.menu_desplegableMotivo["menu"]
        self.menu.config(font=("Arial", 28))  # cambia el tamaño de la fuente del menú desplegable

        # Mostrar el botón "Volver" en la parte inferior derecha
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")  # Colocar en la última fila, esquina inferior derecha

    def registrar_salida_bd(self):
        reg_sal_user = registrar_salida(self.connection, self.cursor, self.qr_date, self.qr_time, self.rut)
        # print(reg_sal_user)
        if reg_sal_user:
            messagebox.showinfo("RASv1", "Salida registrada correctamente")
            self.mostrar_menu_principal()
        else:
            messagebox.showwarning("RASv1", "Error. El usuario no cuenta con un registro de ingreso pendiente")
            self.mostrar_menu_principal()
    
    def registrar_salida(self):
        # limpiar el frame
        self.limpiar_frame()

        self.is_salida = True

        self.marco_camara()

        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se") 

    # -----------------------  FUNCIONES PARA CONTROL DE CAMARA -----------------------
    def iniciar_camara(self):
        if not self.running:
            self.running = True
            self.hilo = threading.Thread(target=self.mostrar_video)
            self.hilo.start()

    def detener_camara(self):
        if self.running:
            self.running = False
            self.hilo.join()
            self.capture.release()
        
    def mostrar_video(self):
        if self.running:
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.label_video.imgtk = imgtk
                self.label_video.configure(image=imgtk)
                ret_qr, decoded_info, points, _ = self.qrCodeDetector.detectAndDecodeMulti(frame)
                if ret_qr:
                    for info, point in zip(decoded_info, points):
                        if info:
                            now = datetime.now()
                            self.qr_info = str(info)
                            self.rut = parametro_rut(self.qr_info)
                            self.qr_date = now.strftime('%d-%m-%Y')
                            self.qr_time = now.strftime('%H:%M:%S')
                            messagebox.showinfo("RASv1", "QR detectado correctamente")
                            if self.is_registro:
                                self.registrar_ingreso_bd()
                            elif self.is_salida:
                                self.registrar_salida_bd()
                        else:
                            color = (0, 0, 255)
                            frame = cv2.polylines(frame, [point.astype(int)], True, color, 8)
            self.frame.after(10, self.mostrar_video)

# -----------------------  MAIN -----------------------
if __name__ == "__main__":
    # Crear la ventana principal
    root = tk.Tk()
    app = Menu(root)

    # Iniciar el bucle principal de la interfaz gráfica
    root.mainloop()


        

