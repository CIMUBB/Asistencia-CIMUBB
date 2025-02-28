from fastapi import FastAPI, Query, Request, Depends, HTTPException, Form, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, ORJSONResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.websockets import WebSocketState
from starlette.responses import RedirectResponse
from contextlib import asynccontextmanager
from colorama import Fore, Style
from datetime import datetime
import redis
import asyncio
import asyncpg
from PIL import Image
import io
from urllib.parse import urlencode

# Dependencias propias
from app.query import (
    authenticate_user,
    get_filtered_data,
    get_all_data_by_rut,
    listen_postgres
)
from app.auth import (
    create_access_token,
    verify_token
)
from app.security import hash_password
from app.database import db

redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

message_queue = asyncio.Queue()
websockets = set()

async def process_events():
    """Procesa eventos y los envía a WebSockets activos o los guarda en Redis."""
    while True:
        payload = await message_queue.get()  # Obtener el evento desde PostgreSQL
        print(f"enviando a {len(websockets)}")
        print(f"PostgreSQL emitió: {payload}")

        # Limpiar WebSockets desconectados antes de enviar
        disconnected_ws = set()
        for ws in websockets:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected_ws.add(ws)
        
        # Eliminar WebSockets desconectados
        websockets.difference_update(disconnected_ws)

        # Guardar en Redis si no hay WebSockets activos
        if not websockets:
            redis_client.rpush("pending_notifications", payload)

async def validate_image(photo: UploadFile):
    try:
        image_bytes = await photo.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Validar formato de imagen
        if image.format not in ["JPEG", "PNG"]:
            raise HTTPException(status_code=400, detail="Formato inválido. Solo se permiten imágenes JPG o PNG.")

        return image_bytes

    except Exception:
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")

# Ciclo de vida de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    print(f"{Fore.YELLOW}{40 * '='}  Aplicación iniciada  {40 * '='}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t  http://127.0.0.1:8000")
    postgres_task = asyncio.create_task(listen_postgres(message_queue))
    events_task = asyncio.create_task(process_events())
    yield
    
    postgres_task.cancel()
    events_task.cancel()
    await db.disconnect()
    print(f"{Fore.RED}{40 * '='}  Aplicación cerrada  {40 * '='}{Style.RESET_ALL}")

# Inicialización de FastAPI
app = FastAPI(debug=False, lifespan=lifespan)

# Configuración de plantillas y archivos estáticos
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

PROTECTED_ROUTES = ("/dashboard", "/profile", "/register-admin", "/register-user")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path in PROTECTED_ROUTES:
        access_token = request.cookies.get("access_token")
        
        if not access_token or not access_token.startswith("Bearer "):
            response = RedirectResponse(url="/login", status_code=303)
            response.set_cookie(
                key="access_token",
                value="",
                httponly=True,
                max_age=0,
                expires=0,
                path="/",
            )
            return response
        
        try:
            token = access_token[len("Bearer "):]
            verify_token(token)
        except Exception as e:  # Captura cualquier error en la verificación
            response = RedirectResponse(url="/login", status_code=303)
            response.set_cookie(
                key="access_token",
                value="",
                httponly=True,
                max_age=0,
                expires=0,
                path="/",
            )
            return response

    response = await call_next(request)
    if path in PROTECTED_ROUTES:
        response.headers.update({
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        })
    return response


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "page": "index"})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "page": "login"})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "page": "dashboard"})

@app.get("/register-user", response_class=HTMLResponse)
async def register_user_page(request: Request):
    return templates.TemplateResponse("register-user.html", {"request": request, "page": "register-user"})

@app.get("/register-admin", response_class=HTMLResponse)
async def register_user_page(request: Request):
    return templates.TemplateResponse("register-admin.html", {"request": request, "page": "register-admin"})

@app.get("/profile/photo/{rut}")
async def get_profile_photo(rut: str):
    """
    Devuelve la foto de perfil del usuario como una imagen binaria.
    Si no tiene foto, devuelve la imagen por defecto.
    """
    async with db.pool.acquire() as connection:
        query = "SELECT foto_perfil FROM usuario WHERE rut = $1"
        row = await connection.fetchrow(query, rut)

        if row and row["foto_perfil"]:
            return Response(content=row["foto_perfil"], media_type="image/png")
        
        return Response(content=open("app/static/images/defecto.png", "rb").read(), media_type="image/png")

@app.get("/profile", response_class=ORJSONResponse)
async def profile_page(
    request: Request,
    rut: str = Query(..., min_length=9, max_length=12, regex=r"^\d{7,8}-?[0-9kK]?$")
):
    try:
        registros = await get_all_data_by_rut(rut)

        if not registros:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        usuario = registros[0]

        if isinstance(usuario, asyncpg.Record):
            usuario = dict(usuario)

        # Convertir cualquier campo `bytes` en `str`
        for key, value in usuario.items():
            if isinstance(value, bytes):
                try:
                    usuario[key] = value.decode("utf-8", errors="ignore")
                except Exception:
                    usuario[key] = str(value)

        foto_perfil_url = f"/profile/photo/{usuario['rut']}" if usuario.get("foto_perfil") else "/static/images/defecto.png"

        registros_limpios = []
        for record in registros:
            record_dict = dict(record)
            for key, value in record_dict.items():
                if isinstance(value, bytes):
                    try:
                        record_dict[key] = value.decode("utf-8", errors="ignore")
                    except Exception:
                        record_dict[key] = str(value)
            registros_limpios.append(record_dict)

        response_data = {
            "rut": usuario["rut"],
            "nombre_completo": usuario["nombre_completo"],
            "email": usuario["email"],
            "tipo_usuario": usuario["tipo_usuario"],
            "foto_perfil": foto_perfil_url,
            "registros": registros_limpios
        }

        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse("profile.html", {
                "request": request,
                "page": "profile",
                **response_data
            })
        else:
            return ORJSONResponse(content=response_data)

    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Credenciales inválidas", "page": "login"}
        )

    token = create_access_token({"sub": user["username"]})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=1800,
        path="/",
        secure=True,
        samesite="Lax"
    )
    return response

@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token", path="/")
    print(f"{Fore.YELLOW}CIMUBB:\t {Style.RESET_ALL} Token eliminado correctamente.")
    return response

@app.get("/api/dashboard")
async def dashboard_data(
    year: int = Query(None, ge=2000, le=datetime.now().year),
    month: str = Query(None, regex="^(0?[1-9]|1[0-2])$"),
    day: int = Query(None, ge=1, le=31),
    motivo: str = Query(None, min_length=3, max_length=100),
    rut: str = Query(None, min_length=1, max_length=12, regex=r"^\d{1,8}-?[0-9kK]?$")  # Permite búsquedas parciales
):
    registros = await get_filtered_data(year, month, day, motivo, rut)
    
    pending_notifications = []
    while redis_client.llen("pending_notifications") > 0:
        pending_notifications.append(redis_client.lpop("pending_notifications"))

    return ORJSONResponse(content={
        "registros": [dict(record) for record in registros],
        "notificaciones": pending_notifications
    })

@app.post("/register-user")
async def register_user(
    rut: str = Form(..., regex=r"^\d{7,8}-?[0-9kK]$"),
    nombre_completo: str = Form(""),
    email: str = Form(""),
    photo: UploadFile = File(None)
):
    async with db.pool.acquire() as conn:
        query_check = "SELECT rut FROM Usuario WHERE rut = $1"
        existing_user = await conn.fetchval(query_check, rut)

        if existing_user:
            raise HTTPException(status_code=400, detail="El usuario ya existe")

        if nombre_completo and email and photo:
            tipo_usuario = "registrado"
            photo_bytes = await validate_image(photo)
        else:
            tipo_usuario = "invitado"
            nombre_completo = ""
            email = ""
            photo_bytes = None

        query = """
            INSERT INTO Usuario (rut, nombre_completo, email, tipo_usuario, foto_perfil)
            VALUES ($1, $2, $3, $4, $5)
        """
        await conn.execute(query, rut, nombre_completo, email, tipo_usuario, photo_bytes)

    message = urlencode({"message": "Usuario registrado exitosamente"})
    return RedirectResponse(url=f"/dashboard?{message}", status_code=303)

@app.post("/register-admin")
async def register_admin(
    username: str = Form(...),
    password: str = Form(...),
):
    async with db.pool.acquire() as conn:
        query_check = "SELECT id FROM Login WHERE username = $1"
        existing_admin = await conn.fetchval(query_check, username)

        if existing_admin:
            raise HTTPException(status_code=400, detail="El administrador ya existe")

        hashed_password = hash_password(password)

        query = """
            INSERT INTO Login (username, password)
            VALUES ($1, $2)
        """
        await conn.execute(query, username, hashed_password)

    message = urlencode({"message": "Administrador registrado exitosamente"})
    return RedirectResponse(url=f"/dashboard?{message}", status_code=303)

@app.websocket("/ws/notify")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websockets.add(websocket)
    print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t WebSocket conectado. Total activos: {len(websockets)}")
    try:
        while redis_client.llen("pending_notifications") > 0:
            message = await redis_client.lpop("pending_notifications")
            if message:
                await websocket.send_text(message.decode("utf-8"))

        while True:
            try:
                data = await websocket.receive_text()
                if data == 'ping':
                    continue
            except WebSocketDisconnect:
                print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t Cliente desconectado.")
                break
            except Exception as e:
                print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t Error en WebSocket: {e}")
                break

    except Exception as e:
        print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t WebSocket cerrado inesperadamente: {e}")

    finally:
        websockets.discard(websocket)
        print(f"{Fore.YELLOW}CIMUBB:{Style.RESET_ALL}\t WebSocket eliminado. Total activos: {len(websockets)}")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({"field": error["loc"][-1], "message": error["msg"]})
    return ORJSONResponse(content={"errors": errors}, status_code=400)