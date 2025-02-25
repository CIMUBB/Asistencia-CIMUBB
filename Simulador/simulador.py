import psycopg2
import inquirer
from dotenv import load_dotenv
import os
from itertools import cycle
import random
from faker import Faker
from datetime import datetime, time, timedelta

# Cargar variables del archivo .env
load_dotenv()

# Configura Faker para datos aleatorios
fake = Faker('es_ES')

# Conexión a PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    options="-c client_encoding=UTF8"
)
cur = conn.cursor()

def comprobar_conexion():
    try:
        cur.execute("SELECT 1")
        print("\n✅ Conexión exitosa a la base de datos.")
    except Exception as e:
        print(f"\n❌ Error al conectar a la base de datos: {e}")

# Función para crear un nuevo usuario
def crear_usuario():
    print("\n🧑 Crear nuevo usuario:")
    rut = input("📄 Ingrese RUT (formato 12345678-9): ")

    # Pregunta para seleccionar el tipo de usuario
    tipo_pregunta = [
        inquirer.List(
            "tipo",
            message="Selecciona el tipo de usuario:",
            choices=["registrado", "invitado"],
        )
    ]
    tipo_usuario = inquirer.prompt(tipo_pregunta)["tipo"]

    # Inicializar los valores de nombre_completo y email como None
    nombre_completo = None
    email = None

    # Si el usuario es registrado, solicitar nombre y email
    if tipo_usuario == "registrado":
        nombre_completo = input("📛 Ingrese nombre completo: ")
        email = input("📧 Ingrese email: ")

    try:
        # Insertar los datos en la tabla Usuario
        cur.execute(
            """
            INSERT INTO Usuario (rut, nombre_completo, email, tipo_usuario)
            VALUES (%s, %s, %s, %s)
            """,
            (rut, nombre_completo, email, tipo_usuario)
        )
        conn.commit()
        print("\n✅ Usuario creado exitosamente.")
    except Exception as e:
        print(f"\n❌ Error al crear usuario: {e}")
        conn.rollback()

# Función para registrar la entrada y salida de un usuario
def registrar_ingreso():
    print("\n📝 Registrar ingreso:")
    cur.execute("SELECT rut, nombre_completo FROM Usuario")
    usuarios = cur.fetchall()

    if not usuarios:
        print("\n⚠️ No hay usuarios disponibles.")
        return

    # Seleccionar un usuario
    rut_pregunta = [
        inquirer.List(
            "rut",
            message="Selecciona el RUT del usuario",
            choices=[f"{usuario[0]} - {usuario[1]}" for usuario in usuarios],
        )
    ]
    rut_seleccionado = inquirer.prompt(rut_pregunta)["rut"].split(" - ")[0]

    # Ingresar detalles del registro
    fecha = input("📅 Ingresa la fecha de ingreso (YYYY-MM-DD) o presiona Enter para usar la fecha actual: ")
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            fecha = datetime.strptime(fecha, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            print("❌ Formato de fecha incorrecto. Usando la fecha actual.")
            fecha = datetime.now().strftime("%Y-%m-%d")

    hora_ingreso = input("🕒 Ingresa la hora de ingreso (HH:MM:SS): ")

    motivo_pregunta = [
        inquirer.List(
            "motivo",
            message="Selecciona el motivo del ingreso:",
            choices=["asignatura", "asistencia tecnica", "investigacion", "practica profesional", "trabajo de titulo", "transferencia tecnologica"],
        )
    ]
    motivo = inquirer.prompt(motivo_pregunta)["motivo"]

    # Generar ID incremental
    cur.execute("SELECT COUNT(*) FROM Registro")
    total_registros = cur.fetchone()[0]
    id_registro = f"REG{total_registros + 1:04d}"

    try:
        cur.execute(
            """
            INSERT INTO Registro (id_registro, fecha, hora_ingreso, motivo, rut)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_registro, fecha, hora_ingreso, motivo, rut_seleccionado)
        )
        conn.commit()
        print(f"\n✅ Registro creado exitosamente. ID del registro: {id_registro}")
    except Exception as e:
        print(f"\n❌ Error al crear registro: {e}")
        conn.rollback()


# Función para registrar la salida de un usuario
# Función para registrar la salida de un usuario
def registrar_salida():
    print("\n🚪 Registrar salida:")
    
    # Consulta los registros que tienen fecha y hora de salida como cadenas vacías
    cur.execute("""
        SELECT id_registro, rut, fecha, hora_ingreso
        FROM Registro
        WHERE hora_salida IS NULL
    """)
    registros = cur.fetchall()

    if not registros:
        print("\n⚠️ No hay registros pendientes de salida.")
        return

    # Seleccionar un registro pendiente de salida
    registro_pregunta = [
        inquirer.List(
            "id_registro",
            message="Selecciona el registro para marcar la salida:",
            choices=[f"{registro[0]} - {registro[1]} - {registro[2]} {registro[3]}" for registro in registros],
        )
    ]
    registro_seleccionado = inquirer.prompt(registro_pregunta)["id_registro"].split(" - ")[0]

    # Usar la fecha y hora actuales para la salida
    hora_salida = input("🕒 Ingresa la hora de ingreso (HH:MM:SS): ")

    try:
        # Actualizar el registro con la fecha y hora de salida
        cur.execute(
            """
            UPDATE Registro
            SET hora_salida = %s
            WHERE id_registro = %s
            """,
            (hora_salida, registro_seleccionado)
        )
        conn.commit()
        print(f"\n✅ Salida registrada exitosamente para el registro {registro_seleccionado}.")
    except Exception as e:
        print(f"\n❌ Error al registrar la salida: {e}")
        conn.rollback()

def generar_usuarios_aleatorios():
    print("\n🎲 Generar usuarios aleatorios")
    try:
        m = int(input("¿Cuántos usuarios deseas generar? "))
    except ValueError:
        print("❌ Debes ingresar un número válido")
        return

    for _ in range(m):
        # Generar RUT válido chileno
        num = random.randint(1000000, 25000000)
        cuerpo_rut = f"{num}"
        verificador = calcular_digito_verificador(num)
        rut = f"{cuerpo_rut}-{verificador}"

        # Alternar entre tipos de usuario
        tipo = "registrado" if random.choice([True, False]) else "invitado"
        nombre = fake.name() if tipo == "registrado" else None
        email = fake.email() if tipo == "registrado" else None

        try:
            cur.execute(
                """INSERT INTO Usuario (rut, nombre_completo, email, tipo_usuario)
                VALUES (%s, %s, %s, %s)""",
                (rut, nombre, email, tipo)
            )
            conn.commit()
        except Exception as e:
            print(f"❌ Error al crear usuario {rut}: {e}")
            conn.rollback()

    print(f"\n✅ {m} usuarios aleatorios creados exitosamente!")

def calcular_digito_verificador(numero):
    reversed_digits = map(int, reversed(str(numero)))
    factors = cycle(range(2, 8))
    s = sum(d * f for d, f in zip(reversed_digits, factors))
    mod = (-s) % 11
    return 'K' if mod == 10 else str(mod)

def generar_registros_aleatorios():
    print("\n📊 Generar registros aleatorios")
    try:
        n = int(input("¿Cuántos registros deseas generar? "))
    except ValueError:
        print("❌ Debes ingresar un número válido")
        return

    cur.execute("SELECT rut FROM Usuario")
    ruts = [rut[0] for rut in cur.fetchall()]
    
    if not ruts:
        print("⚠️ Primero debe crear usuarios!")
        return

    motivos = ["asignatura", "asistencia tecnica", "investigacion", 
               "practica profesional", "trabajo de titulo", "transferencia tecnologica"]

    # Configurar rango de fechas para 2025
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)

    for _ in range(n):
        rut = random.choice(ruts)
        
        # Generar fecha en 2025
        fecha = fake.date_between_dates(date_start=start_date, date_end=end_date)
        
        # Generar hora de ingreso entre 8:00 y 20:00
        hora_ingreso = time(
            hour=random.randint(8, 19),  # 8 AM a 7:59 PM
            minute=random.choice([0, 15, 30, 45]),
            second=random.randint(0, 59)
        )
        
        # 80% de probabilidad de hora de salida
        hora_salida = None
        if random.random() < 0.8:
            # Duración entre 30 minutos y 8 horas
            delta = timedelta(
                hours=random.randint(0, 7),
                minutes=random.randint(30, 59)
            )
            hora_salida = (datetime.combine(fecha, hora_ingreso) + delta).time()

        motivo = random.choice(motivos)

        # Generar ID incremental
        cur.execute("SELECT COUNT(*) FROM Registro")
        total_registros = cur.fetchone()[0]
        id_registro = f"REG{total_registros + 1:04d}"
        try:
            cur.execute(
                """
                INSERT INTO Registro (id_registro, fecha, hora_ingreso, hora_salida, motivo, rut)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    id_registro,
                    fecha.strftime("%Y-%m-%d"),
                    hora_ingreso.strftime("%H:%M:%S"),
                    hora_salida.strftime("%H:%M:%S") if hora_salida else None,
                    motivo,
                    rut
                )
            )
            conn.commit()
        except Exception as e:
            print(f"❌ Error al crear registro: {str(e).split('CONTEXT')[0]}")
            conn.rollback()

    print(f"\n✅ {n} registros aleatorios creados exitosamente!")

# --- Actualiza el menú principal ---
def menu_principal():
    while True:
        print("\n📋 Menú Principal")
        preguntas = [
            inquirer.List(
                "opcion",
                message="Selecciona una opción",
                choices=[
                    "1. Crear nuevo usuario",
                    "2. Registrar ingreso de usuario",
                    "3. Registrar salida de usuario",
                    "4. Generar usuarios aleatorios",  # Nueva opción
                    "5. Generar registros aleatorios",  # Nueva opción
                    "6. Salir"
                ],
            )
        ]
        respuesta = inquirer.prompt(preguntas)["opcion"]

        if respuesta.startswith("1"): crear_usuario()
        elif respuesta.startswith("2"): registrar_ingreso()
        elif respuesta.startswith("3"): registrar_salida()
        elif respuesta.startswith("4"): generar_usuarios_aleatorios()
        elif respuesta.startswith("5"): generar_registros_aleatorios()
        elif respuesta.startswith("6"):
            print("\n👋 Saliendo...")
            break

# ... (resto del código existente)

# Ejecutar el menú principal
comprobar_conexion()
menu_principal()

# Cerrar la conexión a la base de datos
cur.close()
conn.close()
