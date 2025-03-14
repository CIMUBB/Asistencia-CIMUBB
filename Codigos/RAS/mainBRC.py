import cv2
import tkinter as tk
import threading
import psycopg2
import json
from tkinter import messagebox
from tkinter import ttk
from tkinter import PhotoImage
from datetime import datetime
from PIL import Image, ImageTk
import re
from pathlib import Path


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

def registrar_ingreso(conexion, cursor, id_registro, fecha, hora_ingreso, motivo, rut):
    """
    Objetivo: registrar el ingreso de un usuario en la tabla Registro

    Parametros:
        - conexion: objeto de conexión a la base de datos
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida
        - id_registro: identificador único del registro de ingreso
        - fecha: fecha en que se registra el ingreso
        - hora_ingreso: hora en que se registra el ingreso
        - motivo: motivo por el que ingresa el usuario
        - rut: rut del usuario

    Return: True si el registro se realizó correctamente, False si no se pudo registrar
    """
    try: 
        #consulta para saber si el usuario tiene un registro de ingreso previo (salida pendiente)
        consulta_user_ing = "SELECT * FROM Registro WHERE rut = %s AND hora_salida IS NULL"
        cursor.execute(consulta_user_ing, (rut,))
        if cursor.fetchone():
            return False
        else:
            # consulta para insertar un nuevo registro de ingreso en la tabla Registro
            consulta = "INSERT INTO Registro (id_registro, fecha, hora_ingreso, motivo, rut) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(consulta, (id_registro, fecha, hora_ingreso, motivo, rut))
            conexion.commit()
            return True
    except Exception as e:
        print("Error al registrar el ingreso:", e)

def registrar_salida(conexion, cursor, hora_salida, rut):
    """
    Objetivo: registrar la salida de un usuario en la tabla Registro

    Parametros:
        - cursor: objeto para ejecutar consultas en la base de datos a través de la conexión establecida
        - hora_salida: hora en que se registra la salida
        - id_registro: identificador único del registro de ingreso

    Return: True si el registro se realizó correctamente, False si no se pudo registrar
    """
    try:
        #consulta para obtener el id_registro de la salida pendiente del usuario
        consulta_id_pendiente = "SELECT id_registro FROM Registro WHERE rut = %s AND hora_salida IS NULL"
        cursor.execute(consulta_id_pendiente, (rut,))
        #obtener el id_registo de la salida pendiente
        id_registro = cursor.fetchone()
        if id_registro:
            #consulta para actualizar la hora y fecha de salida del usuario
            consulta = "UPDATE Registro SET hora_salida = %s WHERE id_registro = %s"
            cursor.execute(consulta, (hora_salida, id_registro))
            conexion.commit()
            return True
        else:
            return False
    except Exception as e:
        print("Error al registrar la salida:", e)

def borrar_datos_img(ruta):
        ruta.unlink()

def imagen_binario(ruta_imagen):
        with open(ruta_imagen, "rb") as file:
            binary_data = file.read()
        return binary_data

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
            "bg":"#91bff8",                      # color de fondo del botón
            "fg": "#ffffff",                          # color del texto del botón
            "relief": "groove",                         # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                                # ancho del borde
            "width": 20,                            # ancho del botón
            "height": 4                             # altura del botón
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
            "bg": "#91bff8",                # color de fondo del botón
            "fg": "#ffffff",                  # color del texto del botón
            "relief": "groove",             # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                        # ancho del borde
            "width": 9,                     # ancho del botón
            "height": 3,                    # altura del botón
        }

        #estilo para boton 'Seleccion'
        self.estilo_seleccion = {
            "font": ("Arial", 14),  # tipo y tamaño de la fuente
            "bg": "#91bff8",                        # color de fondo del botón
            "fg": "#ffffff",                # color del texto del botón
            "relief": "groove",             # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                        # ancho del borde
            "width": 15,                    # ancho del botón
            "height": 4,                    # altura del botón
        }

        #estilo para boton 'Seleccion 2'
        self.estilo_seleccion2 = {
            "font": ("Arial", 14),  # tipo y tamaño de la fuente
            "bg": "#91bff8",                        # color de fondo del botón
            "fg": "#ffffff",                # color del texto del botón
            "relief": "groove",             # estilo del borde (opciones: flat, raised, sunken, groove, ridge)
            "bd": 7,                        # ancho del borde
            "width": 12,                    # ancho del botón
            "height": 3,                    # altura del botón
        }

        # estilo para boton 'Registrar QR'
        self.estilo_RegQR = {
            "font": ("Arial", 16),          # tipo y tamaño de la fuente
            "bg": "#91bff8",                        # color de fondo del botón
            "fg": "#ffffff",                          # color del texto del botón
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
        self.frame = tk.Frame(self.root, bg="#ffffff")
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
        self.tipo_usuario = None
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
        self.tipo_usuario = None
        self.motivo = None
        self.rut = None
        self.rut_enrolar = None
        self.nombre_completo = None
        self.email = None
        self.binary_data_img = None
        self.is_registro = None
        self.is_salida = None
        
    def guardar_datos(self):
            self.rut_enrolar = self.entry_rut_enrolar.get()
            self.nombre_completo = self.entry_nombre.get()
            self.email = self.entry_email.get()
            print(f"RUT: {self.rut_enrolar}, Nombre: {self.nombre_completo}, Email: {self.email}")
    
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
        self.registrarIngreso.grid(row=2, column=0, padx=140, pady=10, sticky="nw")
        self.enrolarse.grid(row=2, column=0, padx=10, pady=10, sticky="n")
        self.registrarSalida.grid(row=2, column=0, padx=140, pady=10, sticky="ne")
        self.volver_btn.forget()
    
    def teclado_pantalla(self, entry_widget):
        # Destruir el teclado existente si ya hay uno
        if hasattr(self, 'frame_teclado') and self.frame_teclado.winfo_exists():
            self.frame_teclado.destroy()
        
        # destruir frames tipos de usuario para mejorar la visualizacion
        if hasattr(self, 'frame_tipo') and self.frame_tipo.winfo_exists() or hasattr(self, 'texto_users') and self.texto_users.winfo_exists():
            self.frame_tipo.destroy()
            self.texto_users.destroy()

        # crear un frame para mostrar el teclado en pantalla
        self.frame_teclado = tk.Frame(self.frame, bg="#ffffff", bd=5, relief="ridge")

        self.frame_teclado.grid(row=3, column=0, padx=30, pady=10, sticky="n")
        self.keys = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'DELETE ALL'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '⌫'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'Ñ', '🡐'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M','@', '.', '    ']
        ]

        for row_index, row in enumerate(self.keys):
            col_index = 0
            for key in row:
                if key == '    ':
                    button = tk.Button(self.frame_teclado, text=key, width=20, height=2, command=lambda k=key: self.key_press(k, entry_widget))
                    button.grid(row=row_index, column=col_index, columnspan=5, padx=5, pady=5)
                    col_index += 5
                elif key == '⌫':
                    button = tk.Button(self.frame_teclado, text=key, width=10, height=2, command=lambda: self.backspace(entry_widget))
                    button.grid(row=row_index, column=col_index, columnspan=2, padx=5, pady=5)
                    col_index += 2
                elif key == '🡐':
                    button = tk.Button(self.frame_teclado, text=key, width=10, height=2, command=lambda: self.enter(entry_widget))
                    button.grid(row=row_index, column=col_index, columnspan=2, padx=5, pady=5)
                    col_index += 2
                elif key == 'DELETE ALL':
                    button = tk.Button(self.frame_teclado, text=key, width=10, height=2, command=lambda: self.delete_all(entry_widget))
                    button.grid(row=row_index, column=col_index, columnspan=2, padx=5, pady=5)
                    col_index += 2
    
                else:
                    button = tk.Button(self.frame_teclado, text=key, width=5, height=2, command=lambda k=key: self.key_press(k, entry_widget))
                    button.grid(row=row_index, column=col_index, padx=5, pady=5)
                    col_index += 1
    
    def teclado_numerico(self, entry_widget):
        # Destruir el teclado existente si ya hay uno
        if hasattr(self, 'frame_teclado') and self.frame_teclado.winfo_exists():
            self.frame_teclado.destroy()

        # destruir frames tipos de usuario para mejorar la visualizacion
        if hasattr(self, 'frame_tipo') and self.frame_tipo.winfo_exists() or hasattr(self, 'texto_users') and self.texto_users.winfo_exists():
            self.frame_tipo.destroy()
            self.texto_users.destroy()

        # crear un frame para mostrar el teclado en pantalla
        self.frame_teclado = tk.Frame(self.frame, bg="#ffffff", bd=5, relief="ridge")

        self.frame_teclado.grid(row=2, column=0, columnspan=3, padx=40, pady=10, sticky="s")
        self.keys = [
        ['7', '8', '9', 'DELETE ALL'],
        ['4', '5', '6', '⌫'],
        ['1', '2', '3', '🡐'],
        ['0', '-', 'k'],
        ]

        for row_index, row in enumerate(self.keys):
            col_index = 0
            for key in row:
                if key == '⌫':
                    button = tk.Button(self.frame_teclado, text=key, width=10, height=2, command=lambda: self.backspace(entry_widget))
                    button.grid(row=row_index, column=col_index, columnspan=2, padx=5, pady=5)
                    col_index += 2
                elif key == '🡐':
                    button = tk.Button(self.frame_teclado, text=key, width=10, height=2, command=lambda: self.enter(entry_widget))
                    button.grid(row=row_index, column=col_index, columnspan=2, padx=5, pady=5)
                    col_index += 2
                elif key == 'DELETE ALL':
                    button = tk.Button(self.frame_teclado, text=key, width=10, height=2, command=lambda: self.delete_all(entry_widget))
                    button.grid(row=row_index, column=col_index, columnspan=2, padx=5, pady=5)
                    col_index += 2
                else:
                    button = tk.Button(self.frame_teclado, text=key, width=5, height=2, command=lambda k=key: self.key_press(k, entry_widget))
                    button.grid(row=row_index, column=col_index, padx=5, pady=5)
                    col_index += 1

    def key_press(self, key, entry_widget):
        if key == '    ':
            entry_widget.insert(tk.END, ' ')
        else:
            entry_widget.insert(tk.END, key)
    
    def delete_all(self, entry_widget):
        entry_widget.delete(0, tk.END)

    def backspace(self, entry_widget):
        current_text = entry_widget.get()
        entry_widget.delete(0, tk.END)
        entry_widget.insert(tk.END, current_text[:-1])
        
    def enter(self, entry_widget):
        # Frame para tipos de usuario
        self.frame_tipo = tk.Frame(self.frame, bg="#ffffff")
        self.frame_tipo.grid(row=2, column=0, padx=0, pady=0, sticky="s")

        # Crear botones para seleccionar el tipo de usuario
        self.texto_users = tk.Label(self.frame, text="Tipo de usuario:", font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", anchor="center")
        self.texto_users.grid(row=2, column=0, padx=200, pady=140, sticky="sw")
        self.boton_alumno = tk.Button(self.frame_tipo, text="Alumno", command=lambda: self.guardar_seleccion_usuario("Alumno"), **self.estilo_seleccion2)
        self.boton_alumno.grid(row=1, column=0, padx=140, pady=115, sticky="sw")
        self.boton_funcionario = tk.Button(self.frame_tipo, text="Funcionario", command=lambda: self.guardar_seleccion_usuario("Funcionario"), **self.estilo_seleccion2)
        self.boton_funcionario.grid(row=1, column=1, padx=10, pady=115)

        self.guardar_datos()
        
        # Destruir el teclado
        self.frame_teclado.destroy()

        # Eliminar el foco del campo de entrada
        self.root.focus_set()

    def crear_usuario(self):
        # limpiar el frame
        self.limpiar_frame()

        def validar_rut():
            rut = self.rut_var.get()
            patron = r'^[1-9]\d*\-(\d|k|K)$' 
            if not re.match(patron, rut):
                messagebox.showerror("Error", "El RUT debe tener el formato XXXXXXXX-X")
                self.entry_rut_enrolar.focus_set()

        def validar_nombre():
            nombre = self.nombre_var.get()
            patron = r'^([A-Za-zÑñÁáÉéÍíÓóÚú]+[\'\-]{0,1}[A-Za-zÑñÁáÉéÍíÓóÚú]+)(\s+([A-Za-zÑñÁáÉéÍíÓóÚú]+[\'\-]{0,1}[A-Za-zÑñÁáÉéÍíÓóÚú]+))*$'
            if not re.match(patron, nombre):
                messagebox.showerror("Error", "El nombre no puede contener este formato")
                self.entry_nombre.focus_set()
            
        def validar_email():
            email = self.email_var.get()
            patron = r'^[a-zA-Z0-9_]+([.][a-zA-Z0-9_]+)*@[a-zA-Z0-9_]+([.][a-zA-Z0-9_]+)*[.][a-zA-Z]{2,5}$'
            if not re.match(patron, email):
                messagebox.showerror("Error", "El email debe tener el formato")
                self.entry_email.focus_set()

        def on_focus_in(event):
            if self.rut_var.get() == "12345678-9":
                self.rut_var.set("")
                self.entry_rut_enrolar.config(fg="black")
            self.teclado_numerico(self.entry_rut_enrolar)

        def on_focus_out(event):
            if not self.rut_var.get():
                self.rut_var.set("12345678-9")
                self.entry_rut_enrolar.config(fg="gray")
            else:
                validar_rut()
        
        def limitar_longitud_rut(*args):
            if len(self.rut_var.get()) > 10:
                self.rut_var.set(self.rut_var.get()[:10])
            
        def limitar_longitud_nombre(*args):
            if len(self.nombre_var.get()) > 50:
                self.nombre_var.set(self.nombre_var.get()[:50])
            
        def onf_focus_in_nombre(event):
            if self.nombre_var.get() == "Juan Fernandez Muñoz":
                self.nombre_var.set("")
                self.entry_nombre.config(fg="black")
            self.teclado_pantalla(self.entry_nombre)

        def on_focus_out_nombre(event):
            if not self.nombre_var.get():
                self.nombre_var.set("Juan Fernandez Muñoz")
                self.entry_nombre.config(fg="gray")
            else:
                validar_nombre()
        
        def limitar_longitud_email(*args):
            if len(self.email_var.get()) > 50:
                self.email_var.set(self.email_var.get()[:50])
                    
        def on_focus_in_email(event):
            if self.email_var.get() == "correo_falso@gmail.com":
                self.email_var.set("")
                self.entry_email.config(fg="black")
            self.teclado_pantalla(self.entry_email)

        def on_focus_out_email(event):
            if not self.email_var.get():
                self.email_var.set("correo_falso@gmail.com")
                self.entry_email.config(fg="gray")
            else: 
                validar_email()

        # Rut
        self.texto_rut = tk.Label(self.frame, text="RUT:", font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", anchor="center")
        self.texto_rut.grid(row=0, column=0, padx=310, pady=40, sticky="w")
        self.rut_var = tk.StringVar()
        self.rut_var.trace_add("write", limitar_longitud_rut)
        self.entry_rut_enrolar = tk.Entry(self.frame, font=("Arial", 20), bg="#91bff8", fg="black", relief="groove", width=40, textvariable=self.rut_var)
        self.entry_rut_enrolar.grid(row=0, column=0, padx=10, pady=40)
        self.rut_var.set("12345678-9")
        self.entry_rut_enrolar.config(fg="gray")
        self.entry_rut_enrolar.bind("<FocusIn>", on_focus_in)
        self.entry_rut_enrolar.bind("<FocusOut>", on_focus_out)

        # Nombre
        self.texto_nombre = tk.Label(self.frame, text="Nombre completo:", font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", anchor="center")
        self.texto_nombre.grid(row=1, column=0, padx=160, pady=10, sticky="nw")
        self.nombre_var = tk.StringVar()
        self.nombre_var.trace_add("write", limitar_longitud_nombre)
        self.entry_nombre = tk.Entry(self.frame, font=("Arial", 20), bg="#91bff8", fg="black", relief="groove", width=40, textvariable=self.nombre_var)
        self.entry_nombre.grid(row=1, column=0, padx=10, pady=10, sticky="n")
        self.nombre_var.set("Juan Fernandez Muñoz")
        self.entry_nombre.config(fg="gray")
        self.entry_nombre.bind("<FocusIn>", onf_focus_in_nombre)
        self.entry_nombre.bind("<FocusOut>", on_focus_out_nombre)

        # Email
        self.texto_email = tk.Label(self.frame, text="Email:", font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", anchor="center")
        self.texto_email.grid(row=2, column=0, padx=310, pady=10, sticky="nw")
        self.email_var = tk.StringVar()
        self.email_var.trace_add("write", limitar_longitud_email)
        self.entry_email = tk.Entry(self.frame, font=("Arial", 20), bg="#91bff8", fg="black", relief="groove", width=40, textvariable=self.email_var)
        self.entry_email.grid(row=2, column=0, padx=10, pady=10, sticky="n")
        self.email_var.set("correo_falso@gmail.com")
        self.entry_email.config(fg="gray")
        self.entry_email.bind("<FocusIn>", on_focus_in_email)
        self.entry_email.bind("<FocusOut>", on_focus_out_email)

        # Frame para tipos de usuario
        self.frame_tipo = tk.Frame(self.frame, bg="#ffffff")
        self.frame_tipo.grid(row=2, column=0, padx=0, pady=0, sticky="s")

        # Crear botones para seleccionar el tipo de usuario
        self.texto_users = tk.Label(self.frame, text="Tipo de usuario:", font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", anchor="center")
        self.texto_users.grid(row=2, column=0, padx=200, pady=140, sticky="sw")
        self.boton_alumno = tk.Button(self.frame_tipo, text="Alumno", command=lambda: self.guardar_seleccion_usuario("Alumno"), **self.estilo_seleccion2)
        self.boton_alumno.grid(row=1, column=0, padx=40, pady=115, sticky="sw")
        self.boton_funcionario = tk.Button(self.frame_tipo, text="Funcionario", command=lambda: self.guardar_seleccion_usuario("Funcionario"), **self.estilo_seleccion2)
        self.boton_funcionario.grid(row=1, column=1, padx=40, pady=115, sticky="se")

        # Boton para sacar foto
        self.boton_foto = tk.Button(self.frame, text="Tomar foto", command=self.marco_foto, **self.estilo_guardar)
        self.boton_foto.grid(row=3, column=0, padx=10, pady=10)
        
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")
    
    def guardar_seleccion_usuario(self, seleccion):
        print(f"Seleccionaste tipo de usuario: {seleccion}")
        self.tipo_usuario = seleccion

        # Define un mapeo entre el texto y el botón correspondiente
        botones = {
            "Alumno": self.boton_alumno,
            "Funcionario": self.boton_funcionario
        }
        # Agrega el botón invitado si existe
        if hasattr(self, 'boton_invitado'):
            botones["Invitado"] = self.boton_invitado

        # Primero restablece todos los botones a su color original:
        for boton in botones.values():
            boton.config(bg="#91bff8", fg="#ffffff")

        # Luego cambia el color del botón seleccionado:
        if seleccion in botones:
            botones[seleccion].config(bg="#e4e6e9", fg="black")
        
    def guardar_seleccion_motivo(self, seleccion):
        print(f"Seleccionaste motivo de ingreso: {seleccion}")
        self.motivo = seleccion

        botones_motivo = {
            "Practica": self.boton_practica,
            "Investigacion": self.boton_investigacion,
            "Trabajo de Titulo": self.boton_trabajo_titulo,
            "Asignatura": self.boton_asignatura,
            "Asistencia Tecnica": self.boton_asistencia_tecnica,
            "Transferencia Tecnologica": self.boton_transferencia_tecnologica
        }

        # Restablece el color en todos los botones
        for boton in botones_motivo.values():
            boton.config(bg="#91bff8", fg="#ffffff")

        # Resalta el botón seleccionado
        if seleccion in botones_motivo:
            botones_motivo[seleccion].config(bg="#e4e6e9", fg="black")

    def volver_registrar_ingreso(self):
        self.registrar_ingreso()

    def actualizar_temporizador(self, tiempo_restante):
        if tiempo_restante > 0:
            self.label_temporizador.config(text=str(tiempo_restante))
            self.frame.after(1000, self.actualizar_temporizador, tiempo_restante - 1)
        else:
            self.label_temporizador.config(text="¡Sonríe!")
            self.frame.after(1000, self.tomar_foto)
    
    def instancia_qr_ingreso(self):
        # limpiar el frame
        self.limpiar_frame()

        # Validar que el usuario haya seleccionado su tipo de usuario y el motivo de ingreso
        if self.tipo_usuario == None or self.motivo == None:
            messagebox.showwarning("Advertencia", "Por favor, seleccione su tipo de usuario y el motivo de ingreso antes de continuar.")
            self.registrar_ingreso()
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
        self.texto_activdad.grid(row=1, column=0, padx=180, pady=10, sticky="w")

        #Crear un frame para los botones de tipo de usuario
        self.frame_tipo_usuario = tk.Frame(self.frame, bg="#ffffff")
        self.frame_tipo_usuario.grid(row=1, column=0, padx=300, pady=10, sticky="e")

        # Crear botones para seleccionar el tipo de usuario
        self.boton_alumno = tk.Button(self.frame_tipo_usuario, text="Alumno", command=lambda: self.guardar_seleccion_usuario("Alumno"), **self.estilo_seleccion)
        self.boton_alumno.grid(row=0, column=0, padx=45, pady=10)
        self.boton_funcionario = tk.Button(self.frame_tipo_usuario, text="Funcionario", command=lambda: self.guardar_seleccion_usuario("Funcionario"), **self.estilo_seleccion)
        self.boton_funcionario.grid(row=0, column=1, padx=45, pady=10)
        self.boton_invitado = tk.Button(self.frame_tipo_usuario, text="Invitado", command=lambda: self.guardar_seleccion_usuario("Invitado"), **self.estilo_seleccion)
        self.boton_invitado.grid(row=0, column=2, padx=45, pady=10)
        
        self.texto_motivo = tk.Label(self.frame, text="Motivo de ingreso:",
                                    font=("Arial", 20), bg="#ffffff", fg="black", relief="flat", 
                                    anchor="center")
        self.texto_motivo.grid(row=2, column=0, padx=154, pady=10, sticky="w")

        # Crear un frame para los botones de motivo de ingreso
        self.frame_motivo_ingreso = tk.Frame(self.frame, bg="#ffffff")
        self.frame_motivo_ingreso.grid(row=2, column=0, padx=300, pady=10, sticky="e")

        # Crear botones para seleccionar el motivo de ingreso
        self.boton_practica = tk.Button(self.frame_motivo_ingreso, text="Practica", command=lambda: self.guardar_seleccion_motivo("Practica"), **self.estilo_seleccion)
        self.boton_practica.grid(row=0, column=0, padx=45, pady=20)
        self.boton_investigacion = tk.Button(self.frame_motivo_ingreso, text="Investigacion", command=lambda: self.guardar_seleccion_motivo("Investigacion"), **self.estilo_seleccion)
        self.boton_investigacion.grid(row=0, column=1, padx=45, pady=20)
        self.boton_trabajo_titulo = tk.Button(self.frame_motivo_ingreso, text="Trabajo de Titulo", command=lambda: self.guardar_seleccion_motivo("Trabajo de Titulo"), **self.estilo_seleccion)
        self.boton_trabajo_titulo.grid(row=0, column=2, padx=45, pady=20)
        self.boton_asignatura = tk.Button(self.frame_motivo_ingreso, text="Asignatura", command=lambda: self.guardar_seleccion_motivo("Asignatura"), **self.estilo_seleccion)
        self.boton_asignatura.grid(row=1, column=0, padx=45, pady=20)
        self.boton_asistencia_tecnica = tk.Button(self.frame_motivo_ingreso, text="Asistencia Tecnica", command=lambda: self.guardar_seleccion_motivo("Asistencia Tecnica"), **self.estilo_seleccion)
        self.boton_asistencia_tecnica.grid(row=1, column=1, padx=45, pady=20)
        self.boton_transferencia_tecnologica = tk.Button(self.frame_motivo_ingreso, text="Transf Tecnologica", command=lambda: self.guardar_seleccion_motivo("Transferencia Tecnologica"), **self.estilo_seleccion)
        self.boton_transferencia_tecnologica.grid(row=1, column=2, padx=45, pady=20)

        # opcionesMotivo = ["Practica", "Investigacion", "Trabajo de Titulo", "Asignatura", "Asistencia Tecnica", "Transferencia Tecnologica"]

        self.registrarQR = tk.Button(self.frame, text="Escanear QR", command=self.instancia_qr_ingreso, **self.estilo_RegQR)
        self.registrarQR.grid(row=3, column=0, padx=10, pady=10)

        # Mostrar el botón "Volver" en la parte inferior derecha
        self.volver_btn.grid(row=3, column=0, padx=10, pady=10, sticky="se")  # Colocar en la última fila, esquina inferior derecha

    def registrar_salida_bd(self):
        reg_sal_user = registrar_salida(self.connection, self.cursor, self.qr_time, self.rut)
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

    def validar_foto(self):
        if not self.rut_enrolar or not self.nombre_completo or not self.email or self.rut_enrolar == "12345678-9" or self.nombre_completo == "Juan Fernandez Muñoz" or self.email == "correo_falso@gmail.com" or self.tipo_usuario == None:
            messagebox.showwarning("Advertencia", "Por favor, complete todos los campos antes de tomar la foto.")
            return False
        return True
        
    def marco_foto(self):
        # Validar que se tengan los datos necesarios antes de tomar la foto
        if not self.validar_foto():
            return

        # limpiar el frame
        self.limpiar_frame()

        # Crear un Label para mostrar el video en el Frame
        self.label_video = tk.Label(self.frame, bg="#ffffff", relief="groove", height=500, width=700) 
        self.label_video.grid(row=1, column=0, padx=10, pady=10, sticky="s")
        self.iniciar_camara()

        # Mostrar el temporizador en la pantalla
        self.label_temporizador = tk.Label(self.frame, text="5", font=("Arial", 40), bg="#ffffff", fg="red")
        self.label_temporizador.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        # Iniciar el temporizador de 5 segundos
        self.actualizar_temporizador(5)        

    def marco_camara(self):
        # Crear un Label para mostrar el video en el Frame
            self.label_video = tk.Label(self.frame, bg="#ffffff", relief="groove", height=500, width=700) 
            self.label_video.grid(row=1, column=0, padx=10, pady=10, sticky="s")
            self.iniciar_camara()

    def tomar_foto(self):
        ret, frame = self.capture.read()
        if ret:
            # Guardar la imagen capturada en la carpeta especificada
            ruta_foto = Path("foto_capturada.png")
            cv2.imwrite(str(ruta_foto), frame)
            messagebox.showinfo("Foto", f"Foto tomada correctamente y guardada en {ruta_foto}")

            # pasar a binario la imagen
            self.binary_data_img = imagen_binario(ruta_foto)

            #registrar usuario en la BD
            if registrar_usuario(self.connection, self.cursor, self.rut_enrolar, self.nombre_completo, self.email, "Funcionario", self.binary_data_img):
                messagebox.showinfo("RASv1", "Usuario registrado correctamente")
                borrar_datos_img(ruta_foto)
                self.mostrar_menu_principal()
            else:
                messagebox.showwarning("RASv1", "Error al registrar el usuario")
                borrar_datos_img(ruta_foto)
                self.crear_usuario()
        else:
            messagebox.showerror("Error", "No se pudo capturar la foto")
        self.mostrar_menu_principal()
        
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


        

