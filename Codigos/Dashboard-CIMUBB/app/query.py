from datetime import datetime, timedelta
from app.database import db
from app.security import verify_password
import asyncio
from colorama import Fore, Style

# Función para obtener los registros filtrados desde la base de datos
async def get_filtered_data(year=None, month=None, day=None, motivo=None, rut=None):
    async with db.pool.acquire() as connection:
        query = """
            SELECT r.id_registro, r.fecha, r.hora_ingreso, r.hora_salida, 
                   r.motivo, r.rut, u.tipo_usuario
            FROM registro r
            JOIN usuario u ON r.rut = u.rut
            WHERE TRUE
        """

        conditions = []
        params = []

        placeholder_index = 1

        if year:
            conditions.append(f"EXTRACT(YEAR FROM r.fecha) = ${placeholder_index}")
            params.append(int(year))
            placeholder_index += 1

        if month and month != "all":
            conditions.append(f"EXTRACT(MONTH FROM r.fecha) = ${placeholder_index}")
            params.append(int(month))
            placeholder_index += 1

        if day is not None and day != "":
            conditions.append(f"EXTRACT(DAY FROM r.fecha) = ${placeholder_index}")
            params.append(int(day))
            placeholder_index += 1
        
        valid_motivos = [
            "asignatura", "asistencia tecnica", "investigacion",
            "practica", "trabajo de titulo", "transferencia tecnologica"
        ]
        if motivo and motivo != "all":
            if motivo.lower() in valid_motivos:
                conditions.append(f"r.motivo ILIKE ${placeholder_index}")
                params.append(motivo.lower())
                placeholder_index += 1
            else:
                raise ValueError(f"Motivo inválido: {motivo}")
        
        if rut and rut != "":
            conditions.append(f"r.rut LIKE ${placeholder_index}")
            params.append(f"{rut}%")  # Coincidir con RUT que comiencen con el valor proporcionado
            placeholder_index += 1

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY r.fecha DESC, r.hora_ingreso DESC"
        
        registros = await connection.fetch(query, *params)

        return [
            {
                "id_registro": registro["id_registro"],
                "fecha": registro["fecha"].isoformat() if registro["fecha"] else None,
                "hora_ingreso": str(registro["hora_ingreso"]),
                "hora_salida": str(registro["hora_salida"]),
                "motivo": registro["motivo"],
                "verificado": "No" if registro["tipo_usuario"] == "invitado" else "Si",
                "rut": registro["rut"]
            }
            for registro in registros
        ]
     
async def get_all_data_by_rut(rut):
    async with db.pool.acquire() as connection:
        query = """
            SELECT r.fecha, r.hora_ingreso, r.hora_salida, r.motivo, r.rut, u.nombre_completo, u.email, u.foto_perfil, u.tipo_usuario
            FROM registro r
            JOIN usuario u ON r.rut = u.rut
            WHERE r.rut = $1
            ORDER BY r.fecha DESC, r.hora_ingreso DESC
        """
        registros = await connection.fetch(query, rut)
        return [
            {
                "fecha": registro["fecha"].isoformat() if registro["fecha"] else None,
                "hora_ingreso": str(registro["hora_ingreso"]),
                "hora_salida": str(registro["hora_salida"]),
                "motivo": registro["motivo"],
                "rut": registro["rut"],
                "nombre_completo": registro["nombre_completo"] or "No disponible",
                "email": registro["email"] or "No disponible",
                "tipo_usuario": registro["tipo_usuario"],
                "foto_perfil": registro["foto_perfil"]
            }
            for registro in registros
        ]

async def authenticate_user(username: str, password: str):
    async with db.pool.acquire() as connection:
        query = """
            SELECT * FROM login WHERE username = $1;
        """
        user = await connection.fetchrow(query, username)
        if user and verify_password(password, user["password"]):
            return user
        return None

async def listen_postgres(queue: asyncio.Queue):
    """Escucha notificaciones en PostgreSQL y las coloca en la cola de mensajes."""
    async with db.pool.acquire() as connection:
        await connection.execute("SET client_encoding = 'UTF8';")

        def callback(conn, pid, channel, payload):
            """Callback para manejar las notificaciones de PostgreSQL."""
            try:
                queue.put_nowait(payload)  # Agregar evento a la cola
            except Exception as e:
                print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t Error decodificando mensaje de PostgreSQL: {e}")

        await connection.add_listener("notify_channel", callback)

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t PostgreSQL Listener cancelado correctamente.")
            
        finally:
            await connection.remove_listener("notify_channel", callback)
            print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t PostgreSQL Listener desconectado.")