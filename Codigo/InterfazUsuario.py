import tkinter as tk
import cv2
import psycopg2 as pg4
import json
import imutils
import re
import time
from PIL import Image, ImageTk

fotowidth = int(640 * 0.75) # 480
fotoheight = int(480 * 0.75) # 360

def camaraLoop():
    global capture
    if capture is not None:
        ret, frame = capture.read()
        if ret:
            frame = imutils.resize(frame, width=fotowidth)
            frame = imutils.resize(frame, height=fotoheight)
            ImagenCamara = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            im = Image.fromarray(ImagenCamara)
            img = ImageTk.PhotoImage(image=im)
            lFoto.configure(image=img)
            lFoto.image = img
            lFoto.after(3, camaraLoop)
        else:
            # frame = imutils.resize(frame, width=fotowidth)
            # frame = imutils.resize(frame, height=fotoheight)
            # ImagenCamara = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # im = Image.fromarray(ImagenCamara)
            # img = ImageTk.PhotoImage(image=im)
            # lFoto.configure(image=img)
            # lFoto.image = img
            capture.release()

def iniciarCamara():
    global capture
    capture = cv2.VideoCapture(0)
    if capture is not None:
        print("[OPENCV] Capturando video")
        camaraLoop()

def capturarFoto():
    global capture
    if capture is not None:
        ret, frame = capture.read()
        if ret:
            cv2.imwrite("user_photo.jpg", frame)
            img = Image.open("user_photo.jpg")
            img = img.resize((fotowidth, fotoheight), Image.LANCZOS)
            img = ImageTk.PhotoImage(img)
            lFoto.config(image=img)
            lFoto.image = img
            capture.release()  # Detener la captura de video
            # cv2.destroyAllWindows()

def cerrarCamara():
    global capture
    if capture is not None:
        capture.release()
        cv2.destroyAllWindows()

def iniciarFUsuario(f):
    mostrarFrame(frame=f)
    iniciarCamara()
    
def terminarFUsuario(frame):
    mostrarFrame(frame)
    cerrarCamara()

def cuentaRegresiva(segundos):
    if segundos > 0:
        lContador.config(text=str(segundos))
        ventanaRaiz.after(1000, cuentaRegresiva, segundos-1)
    elif segundos == 0:
        lContador.config(text="¡Listo!")
        cerrarCamara()
        ventanaRaiz.after(1000, cuentaRegresiva, segundos-1)
    else:
        camaraLoop()

def iniciarCaptura():
    global capture
    if capture is None:
        iniciarCamara()
    cuentaRegresiva(3)

# def capturarFoto():
#     cap = cv2.VideoCapture(0)
#     ret, frame = cap.read()
#     if ret:
#         cv2.imwrite("user_photo.jpg", frame)
#         cap.release()
#         cv2.destroyAllWindows()
#         img = Image.open("user_photo.jpg")
#         img = img.resize((fotowidth, fotoheight), Image.LANCZOS)
#         img = ImageTk.PhotoImage(img)
#         lFoto.config(image=img)
#         lFoto.image = img

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
    conexion, cursor = conexionBaseDatos('creds.json')
    cursor.execute("SELECT * FROM USUARIO WHERE RUN = %s", (RUN,))
    usuario = cursor.fetchone()
    cierre_conexion(conexion, cursor)
    return usuario

def conexionBaseDatos(credenciales):
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
            print("[POSTGRESQL] Conexión exitosa a la base de datos")
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
    run = eRun.get()
    if not validarFormatoRun(run):
        return
    conexion, cursor = conexionBaseDatos('creds.json')
    if consultarUsuario(eRun.get()):
        print("[POSTGRESQL] El usuario ya existe")
        return
    cursor.execute("""
        INSERT INTO USUARIO (RUN, PRIMER_NOMBRE, PRIMER_APELLIDO, SEGUNDO_APELLIDO, EMAIL, FOTO)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (eRun.get(), eNombre.get(), eApellido1.get(), eApellido2.get(), eCorreo.get(), pg4.Binary("user_photo.jpg".encode('utf-8'))))
    # Confirmar los cambios
    conexion.commit()
    print("[POSTGRESQL] Usuario creado")

    # Cerrar la conexión
    cursor.close()
    conexion.close()

def clickEntry(event):
    eRun.config(highlightbackground="gray",
                highlightcolor="blue")

if __name__ == "__main__":
    global pantallaWidth, pantallaHeight
    # Configuración de la ventana
    fuente = "Arial"
    tPredefinido = 20
    ventanaRaiz = tk.Tk()
    ventanaRaiz.attributes('-fullscreen', True)
    ventanaRaiz.attributes('-topmost', True)
    ventanaRaiz.bind('<Control-q>', terminarPrograma)  # Cerrar ventana al presionar 'q'

    pantallaW = ventanaRaiz.winfo_screenwidth() # Raspberry 800
    pantallaH = ventanaRaiz.winfo_screenheight() # Raspberry 480
    
    if pantallaW == 1920 and pantallaH == 1080:
        # Frames
        fHome = tk.Frame(ventanaRaiz)
        fUsuario = tk.Frame(ventanaRaiz)
        fRegistro = tk.Frame(ventanaRaiz)
        for frame in (fHome, fUsuario, fRegistro):
            frame.place(x=0, y=0, width=pantallaW, height=pantallaH)

        
        # fHome
        ## Logo UBB
        imagen_original = Image.open("logoUBB.png")
        porcentaje = 0.4
        imagen_redimensionada = imagen_original.resize((int(imagen_original.width * porcentaje), int(imagen_original.height * porcentaje)),
                                                       Image.Resampling.LANCZOS)
        imagen = ImageTk.PhotoImage(imagen_redimensionada)
        lLogoUBB = tk.Label(fHome, image=imagen)
        lLogoUBB.place(x=(1920 - int(imagen_original.width * porcentaje)) / 2,
                       y=100,
                       width=int(imagen_original.width * porcentaje),
                       height=int(imagen_original.height * porcentaje))

        ## Boton Registro
        bRegistro = tk.Button(fHome, text="Registro asistencia", command=lambda: mostrarFrame(fRegistro), wraplength=200)
        bRegistro.config(font=(fuente, tPredefinido))
        bRegistro.place(x=0, y=pantallaH-400, width=400, height=400)

        ## Boton Crear usuario
        bCrear = tk.Button(fHome, text="Crear usuario", command=lambda: iniciarFUsuario(fUsuario), wraplength=200)
        bCrear.config(font=(fuente, tPredefinido))
        bCrear.place(x=pantallaW-400, y=pantallaH-400, width=400, height=400)
        
        
        # fUsuario
        ## Titulo
        lTitulo = tk.Label(fUsuario, text="Ingrese sus datos:")
        lTitulo.config(font=(fuente, tPredefinido+10))
        lTitulo.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 200, y=50, width=400, height=50)
        
        ## Contador
        lContador = tk.Label(fUsuario, text="")
        lContador.config(font=(fuente, tPredefinido+10))
        lContador.place(x=ventanaRaiz.winfo_screenwidth()-200, y=ventanaRaiz.winfo_screenheight() - 475, width=100, height=50)
        
        ## RUN
        lRUN = tk.Label(fUsuario, text="RUN (########-#):", anchor="e")
        lRUN.config(font=(fuente, tPredefinido))
        lRUN.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 250, y=150, width=250, height=50)
        eRun = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
        eRun.config(font=(fuente, tPredefinido))
        eRun.bind("<FocusIn>", clickEntry)
        eRun.place(x=(ventanaRaiz.winfo_screenwidth() // 2), y=150, width=400, height=50)

        ## Primer Nombre
        lNombre = tk.Label(fUsuario, text="Primer Nombre:", anchor="e")
        lNombre.config(font=(fuente, tPredefinido))
        lNombre.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 200, y=200, width=200, height=50)
        eNombre = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
        eNombre.bind("<FocusIn>", clickEntry)
        eNombre.config(font=(fuente, tPredefinido))
        eNombre.place(x=(ventanaRaiz.winfo_screenwidth() // 2), y=200, width=400, height=50)

        ## Primer Apellido
        lApellido1 = tk.Label(fUsuario, text="Primer Apellido:", anchor="e")
        lApellido1.config(font=(fuente, tPredefinido))
        lApellido1.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 200, y=250, width=200, height=50)
        eApellido1 = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
        eApellido1.bind("<FocusIn>", clickEntry)
        eApellido1.config(font=(fuente, tPredefinido))
        eApellido1.place(x=(ventanaRaiz.winfo_screenwidth() // 2), y=250, width=400, height=50)

        ## Segundo Apellido
        lApellido2 = tk.Label(fUsuario, text="Segundo Apellido:", anchor="e")
        lApellido2.config(font=(fuente, tPredefinido))
        lApellido2.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 240, y=300, width=240, height=50)
        eApellido2 = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
        eApellido2.bind("<FocusIn>", clickEntry)
        eApellido2.config(font=(fuente, tPredefinido))
        eApellido2.place(x=(ventanaRaiz.winfo_screenwidth() // 2), y=300, width=400, height=50)

        ## Correo
        lCorreo = tk.Label(fUsuario, text="Correo:", anchor="e")
        lCorreo.config(font=(fuente, tPredefinido))
        lCorreo.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 240, y=350, width=240, height=50)
        eCorreo = tk.Entry(fUsuario, highlightbackground="gray", highlightcolor="blue", highlightthickness=2)
        eCorreo.bind("<FocusIn>", clickEntry)
        eCorreo.config(font=(fuente, tPredefinido))
        eCorreo.place(x=(ventanaRaiz.winfo_screenwidth() // 2), y=350, width=400, height=50)

        ## Foto
        lFoto = tk.Label(fUsuario, background="gray")
        lFoto.config(font=(fuente, tPredefinido))
        lFoto.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 240, y=475, width=fotowidth, height=fotoheight)
        
        ## Boton Capturar Foto
        bFoto = tk.Button(fUsuario, text="Capturar Foto", command=iniciarCaptura)
        bFoto.config(font=(fuente, tPredefinido))
        bFoto.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 200 , y=425, width=400, height=50)

        ## Boton Enviar
        bEnviar = tk.Button(fUsuario, text="Enviar", command=enviarUsuario)
        bEnviar.config(font=(fuente, tPredefinido))
        bEnviar.place(x=ventanaRaiz.winfo_screenwidth() - 400, y=ventanaRaiz.winfo_screenheight()-400, width=400, height=400)
        mostrarFrame(fHome)
        
        ## Boton Home
        bHomeUsuario = tk.Button(fUsuario, text="Volver", command=lambda: terminarFUsuario(fHome))
        bHomeUsuario.config(font=(fuente, tPredefinido))
        bHomeUsuario.place(x=0, y=1080-400, width=400, height=400)
        
        
        # fRegistro
        ## Titulo
        lTituloRegistro = tk.Label(fRegistro, text="Registro de asistencia", anchor="center")
        lTituloRegistro.config(font=(fuente, tPredefinido+10))
        lTituloRegistro.place(x=(ventanaRaiz.winfo_screenwidth() // 2) - 200, y=50, width=400, height=50)
        
        ## Boton Home
        bHomeRegistro = tk.Button(fRegistro, text="Volver", command=lambda: mostrarFrame(fHome))
        bHomeRegistro.config(font=(fuente, tPredefinido))
        bHomeRegistro.place(x=0, y=1080-400, width=400, height=400)
        
        
        # Ventana Principal
        ventanaRaiz.mainloop()
    if pantallaW == 800 and pantallaH == 480:
        pass