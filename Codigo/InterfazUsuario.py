import tkinter as tk
import cv2
import psycopg2 as pg4
import json
import imutils
import re
import time
import threading
from PIL import Image, ImageTk

# Tamaño de la foto logoUBB
fotowidth = int(640 * 0.75) # 480
fotoheight = int(480 * 0.75) # 360

def bucleCamara():
    """
    La función `bucleCamara` actualiza lFoto con el frame que detecta la camara cada 500 ms.
    """
    global capture
    if capture is not None:
        ret, frame = capture.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame = imutils.resize(frame, width=fotowidth)
            frame = imutils.resize(frame, height=fotoheight)
            ImagenCamara = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(ImagenCamara)
            img = ImageTk.PhotoImage(image=im)
            lVideo.configure(image=img)
            lVideo.image = img
            lVideo.after(42, bucleCamara)

def iniciarCamara():
    """
    La función `iniciarCamara` obtiene la señal de activacion de la camara:
        - Si la señal de captura no es 'None' se llama la funcion `bucleCamara`.
    """
    global capture
    capture = cv2.VideoCapture(0)
    if capture is not None:
        print("[OPENCV] Iniciando Camara")
        bucleCamara()

def obtenerFoto():
    """
    La función `obtenerFoto` obtiene la señal de activacion de la camara:
        - Si la señal de captura no es 'None' se obtiene el ultimo frame. Luego se guarda ese frame, se configura y se muestra en el label 'lFoto'.
    """
    global capture
    if capture is not None:
        ret, frame = capture.read()
        if ret:
            cv2.imwrite("fotoUsuario.jpg", cv2.flip(frame, 1)) # Guardamos temporalmente la foto del nuevo usuario
            img = Image.open("fotoUsuario.jpg")
            img = img.resize((fotowidth, fotoheight), Image.LANCZOS)
            img = ImageTk.PhotoImage(img)
            lFoto.config(image=img)
            lFoto.image = img
            # capture.release()  # Detener la captura de video
            print("[OPENCV] Capturando Foto")

def cerrarCamara():
    """
    La función `cerrarCamara` revisa si la señal de captura esta abierta:
        - Si es asi se detiene la captura de video.
    """
    global capture
    if capture and capture.isOpened():
        capture.release()
        print("[OPENCV] Finalizando Camara")

def iniciarFUsuario(f):
    """
    La función `terminarFUsuario` 
    """
    mostrarFrame(frame=f)
    iniciarCamara()
    
def terminarFUsuario():
    """
    La función `terminarFUsuario` 
    """
    mostrarFrame(frame=fInicio)
    eRun.delete(0, tk.END)
    eNombre.delete(0, tk.END)
    eApellido1.delete(0, tk.END)
    eApellido2.delete(0, tk.END)
    eCorreo.delete(0, tk.END)
    lFoto.config(image="")
    cerrarCamara()

def cuentaRegresiva(segundos):
    """
    La función `cuentaRegresiva` actualiza una etiqueta:
        - Muesta una cuenta regresiva cuanto el tiempo es positivo.
        - Muestra "¡Listo!" cuando la cuenta regresiva alcanza 0 y llama a las funciones para obtener la foto.
    """
    if segundos > 0:
        lContador.config(text=str(segundos))
        ventanaRaiz.after(1000, cuentaRegresiva, segundos-1)
    elif segundos == 0:
        lContador.config(text="¡Listo!")
        obtenerFoto()
        ventanaRaiz.after(1000, cuentaRegresiva, segundos-1)

def capturarFoto():
    """
    La función `capturarFoto` verifica que la señal de captura sea 'None':
        - Si lo es, llama a la funcion `iniciarCamara` para obtener señal.
    Luego se llama a la funcion `cuentaRegresiva` para continuar con la captura de la Foto.
    """
    # global capture
    # if capture is None:
    #     iniciarCamara()
    cuentaRegresiva(3)

def terminarPrograma(evento):
    """
    La función `terminarPrograma` verifica si las teclas presionadas son 'ctrl + q' y destruye la ventana de la raíz si es así.
    """
    ventanaRaiz.destroy()

def mostrarFrame(frame):
    """
    La función `mostrarFrame` se usa para poner al frente un frame especifico en la GUI.
    """
    frame.tkraise()

def consultarUsuario(RUN):
    """
    La función `consultarUsuario` se usa para consultar la existencia de un usuario especifico dentro de la BD.
    """
    conexion, cursor = conexionBaseDatos('creds.json')
    cursor.execute("SELECT * FROM USUARIO WHERE RUN = %s", (RUN,))
    usuario = cursor.fetchone()
    cierre_conexion(conexion, cursor)
    return usuario

def conexionBaseDatos(credenciales):
    """
    La función `conexionBaseDatos` se usa para consultar la existencia de un usuario especifico dentro de la BD.
    """
    try:
        with open(credenciales, 'r') as file:
            creds = json.load(file)
        
        conexion = pg4.connect(
            dbname=creds['database'],
            user=creds['user'],
            password=creds['password'],
            host=creds['host'],
            port=creds['port']
        )
        cursor = conexion.cursor()
         # Ejecutar una consulta simple
        cursor.execute("SELECT 1")
        result = cursor.fetchone() # Ejecutar una consulta simple
        if result:
            print("[POSTGRESQL] Consulta ejecutada exitosamente")
        else:
            print("[POSTGRESQL] No se pudo ejecutar la consulta")
        return conexion, cursor
    except (Exception, pg4.Error) as error:
        print("[POSTGRESQL] Error al conectar con PostgreSQL", error)
        return None, None

def cierre_conexion(connection, cursor):
    if cursor:
        cursor.close()
    if connection:
        connection.close()
        print("[POSTGRESQL] Conexion con PostgreSQL cerrada")

def validarFormatoRun(run):
    patron1 = re.compile(r'^\d{7}-\d$')
    patron2 = re.compile(r'^\d{8}-\d$')
    if patron1.match(run) or patron2.match(run):
        eRun.config(highlightbackground="gray", highlightcolor="blue")
        return True
    else:
        eRun.config(highlightbackground="red", highlightcolor="red")
        return False
    
def enviarUsuario():
    if not validarFormatoRun(eRun.get()):
        return
    conexion, cursor = conexionBaseDatos('creds.json')
    if consultarUsuario(eRun.get()):
        print("[POSTGRESQL] El usuario ya existe")
        lConfirmacion.config(text=f"El usuario \"{eRun.get()}\" ya existe dentro de la BD!", highlightcolor="red")
        terminarFUsuario()
        return
    cursor.execute("""
        INSERT INTO USUARIO (RUN, PRIMER_NOMBRE, PRIMER_APELLIDO, SEGUNDO_APELLIDO, EMAIL, FOTO)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (eRun.get(), eNombre.get(), eApellido1.get(), eApellido2.get(), eCorreo.get(), pg4.Binary("fotoUsuario.jpg".encode('utf-8'))))
    conexion.commit() # Confirmar los cambios
    print("[POSTGRESQL] Usuario creado")
    cursor.close() 
    conexion.close() # Cerrar la conexión
    
    terminarFUsuario()
    lConfirmacion.config(text=f"El usuario \"{eRun.get()}\" ha sido creado con exito!")

def clickEntry(event):
    """
    La función `clickEntry` actualiza la configuracion del entry 'eRun'.
    """
    eRun.config(highlightbackground="gray", highlightcolor="blue")
    
def actualizarReloj1():
    """
    La función `actualizarReloj1` actualiza el lReloj1 con la hora y fecha actual..
    """
    tiempoActual = time.strftime("%H:%M:%S %d/%m/%Y")  # Formato: Día/Mes/Año Hora:Minuto:Segundo
    lReloj1.config(text=tiempoActual)
    ventanaRaiz.after(1000, actualizarReloj1)

def actualizarReloj2():
    """
    La función `actualizarReloj2` actualiza el lReloj2 con la hora y fecha actual..
    """
    tiempoActual = time.strftime("%H:%M:%S %d/%m/%Y")  # Formato: Día/Mes/Año Hora:Minuto:Segundo
    lReloj2.config(text=tiempoActual)
    ventanaRaiz.after(1000, actualizarReloj2)

if __name__ == "__main__":    
    # Configuración de la ventana
    global pantallaWidth, pantallaHeight
    # fuente = "Tipo-UBB"
    fuente = "Arial"
    tPredefinido = 30
    ventanaRaiz = tk.Tk()
    ventanaRaiz.attributes('-fullscreen', True)
    ventanaRaiz.attributes('-topmost', True)
    ventanaRaiz.bind('<Control-q>', terminarPrograma)  # Cerrar ventana al presionar 'q'


    # Informacion de la ventana reducida
    pantallaW = ventanaRaiz.winfo_screenwidth()
    pantallaH = ventanaRaiz.winfo_screenheight()
    
    
    # Frames
    fInicio = tk.Frame(ventanaRaiz)
    fUsuario = tk.Frame(ventanaRaiz)
    fAsistencia = tk.Frame(ventanaRaiz)
    for frame in (fInicio, fUsuario, fAsistencia):
        frame.place(x=0, y=0, width=pantallaW, height=pantallaH)

    
    # fInicio
    ## Logo UBB
    imgO = Image.open("logoUBB.png")
    porcentaje = 0.4
    imgR = imgO.resize((int(imgO.width * porcentaje), int(imgO.height * porcentaje)), Image.Resampling.LANCZOS)
    imagen = ImageTk.PhotoImage(imgR)
    lLogoUBB = tk.Label(fInicio, image=imagen)
    lLogoUBB.place(x=(1920 - int(imgO.width * porcentaje)) / 2, y=100, width=int(imgO.width * porcentaje), height=int(imgO.height * porcentaje))
    
    ## Mensaje Confirmacion
    lConfirmacion = tk.Label(fInicio, text="", anchor="center", highlightthickness=2)
    lConfirmacion.config(font=(fuente, tPredefinido + 10, 'bold'))
    lConfirmacion.pack(anchor='center')
    # lConfirmacion.place(x=(pantallaW // 2) - (lConfirmacion.winfo_width() / 2), y=pantallaH - 540, width=pantallaW, height=50)
    
    ## Boton Registro
    bRegistro = tk.Button(fInicio, text="Registro asistencia", command=lambda: mostrarFrame(fAsistencia), wraplength=250)
    bRegistro.config(font=(fuente, tPredefinido, 'bold'))
    bRegistro.place(x=0, y=pantallaH-400, width=640, height=400)

    ## Label Reloj 
    lReloj1 = tk.Label(fInicio, font=(fuente, tPredefinido*2, 'bold'), wraplength=500)
    lReloj1.place(x=pantallaW//2 - 300, y=pantallaH - 300, width=600, height=200)
    actualizarReloj1()
    
    ## Boton Nuevo usuario
    bNuevo = tk.Button(fInicio, text="Nuevo usuario", command=lambda: iniciarFUsuario(fUsuario), wraplength=200)
    bNuevo.config(font=(fuente, tPredefinido, 'bold'))
    bNuevo.place(x=pantallaW - 640, y=pantallaH - 400, width=640, height=400)
    
    
    # fUsuario
    ## Titulo
    lTitulo = tk.Label(fUsuario, text="Ingrese sus datos:")
    lTitulo.config(font=(fuente, tPredefinido + 10, 'bold'))
    lTitulo.place(x=(pantallaW // 2) - 300, y=25, width=600, height=70)
    
    ## RUN
    lRUN = tk.Label(fUsuario, text="RUN (########-#):", anchor="e")
    lRUN.config(font=(fuente, tPredefinido))
    lRUN.place(x=(pantallaW // 2) - 550, y=150, width=550, height=50)
    eRun = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
    eRun.config(font=(fuente, tPredefinido))
    eRun.bind("<FocusIn>", clickEntry)
    eRun.place(x=(pantallaW // 2), y=150, width=400, height=50)

    ## Primer Nombre
    lNombre = tk.Label(fUsuario, text="Primer Nombre:", anchor="e")
    lNombre.config(font=(fuente, tPredefinido))
    lNombre.place(x=(pantallaW // 2) - 550, y=200, width=550, height=50)
    eNombre = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
    eNombre.bind("<FocusIn>", clickEntry)
    eNombre.config(font=(fuente, tPredefinido))
    eNombre.place(x=(pantallaW // 2), y=200, width=400, height=50)

    ## Primer Apellido
    lApellido1 = tk.Label(fUsuario, text="Primer Apellido:", anchor="e")
    lApellido1.config(font=(fuente, tPredefinido))
    lApellido1.place(x=(pantallaW // 2) - 550, y=250, width=550, height=50)
    eApellido1 = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
    eApellido1.bind("<FocusIn>", clickEntry)
    eApellido1.config(font=(fuente, tPredefinido))
    eApellido1.place(x=(pantallaW // 2), y=250, width=400, height=50)

    ## Segundo Apellido
    lApellido2 = tk.Label(fUsuario, text="Segundo Apellido:", anchor="e")
    lApellido2.config(font=(fuente, tPredefinido))
    lApellido2.place(x=(pantallaW // 2) - 550, y=300, width=550, height=50)
    eApellido2 = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
    eApellido2.bind("<FocusIn>", clickEntry)
    eApellido2.config(font=(fuente, tPredefinido))
    eApellido2.place(x=(pantallaW // 2), y=300, width=400, height=50)

    ## Correo
    lCorreo = tk.Label(fUsuario, text="Correo:", anchor="e")
    lCorreo.config(font=(fuente, tPredefinido))
    lCorreo.place(x=(pantallaW // 2) - 550, y=350, width=550, height=50)
    eCorreo = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
    eCorreo.bind("<FocusIn>", clickEntry)
    eCorreo.config(font=(fuente, tPredefinido))
    eCorreo.place(x=(pantallaW // 2), y=350, width=400, height=50)

    ## Video
    lVideo = tk.Label(fUsuario, background="gray")
    lVideo.config(font=(fuente, tPredefinido))
    lVideo.place(x=(pantallaW // 2) - fotowidth, y=450, width=fotowidth, height=fotoheight)
    
    ## Foto
    lFoto = tk.Label(fUsuario, background="gray")
    lFoto.config(font=(fuente, tPredefinido))
    lFoto.place(x=(pantallaW // 2), y=450, width=fotowidth, height=fotoheight)
    
    ## Contador
    lContador = tk.Label(fUsuario, text="")
    lContador.config(font=(fuente, tPredefinido+30))
    lContador.place(x=(pantallaW // 2) - 150, y=pantallaH - 200, width=300, height=200)
    
    ## Boton Capturar Foto
    bFoto = tk.Button(fUsuario, text="Capturar Foto", command=capturarFoto)
    bFoto.config(font=(fuente, tPredefinido, 'bold'))
    bFoto.place(x=(pantallaW // 2) - (fotowidth/2), y=pantallaH - 250, width=fotowidth, height=50)

    ## Boton Home
    bHomeUsuario = tk.Button(fUsuario, text="Volver", command=lambda: terminarFUsuario())
    bHomeUsuario.config(font=(fuente, tPredefinido, 'bold'))
    bHomeUsuario.place(x=0, y=1080-400, width=480, height=400)
    
    ## Boton Enviar
    bEnviar = tk.Button(fUsuario, text="Enviar", command=enviarUsuario)
    bEnviar.config(font=(fuente, tPredefinido, 'bold'))
    bEnviar.place(x=pantallaW - 480, y=pantallaH - 400, width=480, height=400)
    
    
    # fAsistencia
    ## Titulo
    lTituloRegistro = tk.Label(fAsistencia, text="Registro de asistencia", anchor="center")
    lTituloRegistro.config(font=(fuente, tPredefinido+10))
    lTituloRegistro.place(x=(pantallaW // 2) - 300, y=50, width=600, height=70)
    
    ## Asunto
    lAsunto = tk.Label(fAsistencia, text="Asunto:", anchor="center")
    lAsunto.config(font=(fuente, tPredefinido))
    lAsunto.place(x=50, y=200, width=600, height=70)
    
    ## Boton Asunto Practica
    bP = tk.Button(fAsistencia, text="Práctica", command=lambda: print("Práctica"))
    bP.config(font=(fuente, tPredefinido))
    bP.place(x=320*0, y=pantallaH - 720, width=320, height=320)
    
    ## Boton Asunto Investigacion
    bI = tk.Button(fAsistencia, text="Investigación", command=lambda: print("Investigación"))
    bI.config(font=(fuente, tPredefinido))
    bI.place(x=320*1, y=pantallaH - 720, width=320, height=320)
    
    ## Boton Asunto Trabajo de Titulo
    bTT = tk.Button(fAsistencia, text="Trabajo de Titulo", command=lambda: print("Trabajo de Titulo"), wraplength=300)
    bTT.config(font=(fuente, tPredefinido))
    bTT.place(x=320*2, y=pantallaH - 720, width=320, height=320)
    
    ## Boton Asunto Asignatura
    bA = tk.Button(fAsistencia, text="Asignatura", command=lambda: print("Asignatura"))
    bA.config(font=(fuente, tPredefinido))
    bA.place(x=320*3, y=pantallaH - 720, width=320, height=320)
    
    ## Boton Asunto Asistencia Tecnica
    bAT = tk.Button(fAsistencia, text="Asistencia Técnica", command=lambda: print("Asistencia Técnica"), wraplength=300)
    bAT.config(font=(fuente, tPredefinido))
    bAT.place(x=320*4, y=pantallaH - 720, width=320, height=320)
    
    ## Boton Asunto Transferencia Tecnologica
    bTR = tk.Button(fAsistencia, text="Transferencia Tecnológica", command=lambda: print("hola"), wraplength=300)
    bTR.config(font=(fuente, tPredefinido))
    bTR.place(x=320*5, y=pantallaH - 720, width=320, height=320)
    
    ## Boton Home
    bHomeRegistro = tk.Button(fAsistencia, text="Volver", command=lambda: mostrarFrame(fInicio))
    bHomeRegistro.config(font=(fuente, tPredefinido))
    bHomeRegistro.place(x=0, y=1080-400, width=640, height=400)
    
    ## Label Reloj 
    lReloj2 = tk.Label(fAsistencia, font=(fuente, tPredefinido + 10, 'bold'), wraplength=350)
    lReloj2.place(x=pantallaW//2 - 300, y=pantallaH-300, width=600, height=200)
    actualizarReloj2()

    iniciarCamara()
    cerrarCamara()
    
    # Ventana Principal
    mostrarFrame(fInicio)
    ventanaRaiz.mainloop()