import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from colorama import Fore, Style

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("ERROR: La variable de entorno 'SECRET_KEY' es obligatoria.")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict) -> str:
    """
    Crea un token de acceso JWT con datos y tiempo de expiración.
    """
    if "sub" not in data:
        raise ValueError("El campo 'sub' es obligatorio en los datos del token.")

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print(f"{Fore.YELLOW}CIMUBB:\t {Style.RESET_ALL} Token creado exitosamente.")
        return encoded_jwt
    except Exception as e:
        print(f"ERROR: Error al crear el token: {e}")
        raise ValueError("Error al crear el token JWT.")

def verify_token(token: str) -> dict:
    """
    Verifica y decodifica un token JWT. Lanza una excepción si el token es inválido o expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido: falta el campo 'sub'.")

        print(f"{Fore.YELLOW}CIMUBB:\t {Style.RESET_ALL} Token válido para el usuario {Fore.YELLOW}{username}{Style.RESET_ALL}")
        return payload

    except jwt.ExpiredSignatureError:
        print("ERROR: El token ha expirado.")
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.InvalidTokenError as e:
        print(f"ERROR: Error al decodificar el token: {e}")
        raise HTTPException(status_code=401, detail="Token inválido.")
