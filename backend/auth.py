import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, Response
import config

def verify_password(password: str) -> bool:
    """Cek apakah password yang diinput cocok dengan SITE_PASSWORD."""
    return password == config.SITE_PASSWORD

def create_token() -> str:
    """Buat JWT token baru, berlaku sesuai TOKEN_EXPIRE_HOURS."""
    expire = datetime.now(timezone.utc) + timedelta(hours=config.TOKEN_EXPIRE_HOURS)
    payload = {
        "authenticated": True,
        "exp": expire
    }
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return token

def decode_token(token: str) -> dict:
    """
    Verifikasi & decode token. 
    Raises jwt.ExpiredSignatureError kalau kadaluarsa,
    jwt.InvalidTokenError kalau tidak valid/dipalsukan.
    """
    payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    return payload

def set_token_cookie(response: Response, token: str):
    """Simpan token sebagai httpOnly cookie di response."""
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,           # tidak bisa diakses via JavaScript (proteksi XSS)
        secure=not config.IS_DEV,  # wajib HTTPS hanya saat production
        samesite="lax",          # proteksi dasar dari CSRF
        max_age=config.TOKEN_EXPIRE_HOURS * 3600
    )

def verify_token(request: Request):
    """
    Dependency FastAPI untuk proteksi endpoint.
    Dipakai di endpoint yang butuh login, contoh:
    @app.post("/verify", dependencies=[Depends(verify_token)])
    """
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Belum login")

    try:
        decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi sudah kadaluarsa, silakan login ulang")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

    