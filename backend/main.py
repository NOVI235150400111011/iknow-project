from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

import os
import config
import auth
import face_service


app = FastAPI(title="Face Verification API")


# =========================================================
# CORS
# =========================================================
# Izinkan frontend mengakses API saat development lokal.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODEL
# =========================================================
class LoginRequest(BaseModel):
    password: str


# =========================================================
# ROOT / LOGIN
# =========================================================
@app.get("/")
async def root():
    """
    Saat membuka localhost:8000,
    user diarahkan ke halaman login.
    """
    return RedirectResponse(url="/login.html")


# =========================================================
# HEALTH CHECK
# =========================================================
@app.get("/health")
async def health():
    """
    Endpoint publik untuk mengecek apakah server hidup.
    """
    return {"status": "ok"}


# =========================================================
# LOGIN
# =========================================================
@app.post("/login")
async def login(data: LoginRequest, response: Response):
    """
    Mengecek password.
    Jika benar, buat session token dan simpan
    sebagai HTTP cookie.
    """

    if not auth.verify_password(data.password):
        raise HTTPException(
            status_code=401,
            detail="Password salah"
        )

    token = auth.create_token()

    auth.set_token_cookie(
        response,
        token
    )

    return {
        "message": "Login berhasil"
    }


# =========================================================
# LOGOUT
# =========================================================
@app.post("/logout")
async def logout(response: Response):
    """
    Menghapus session token.
    """

    response.delete_cookie(
        "session_token"
    )

    return {
        "message": "Logout berhasil"
    }


# =========================================================
# FACE VERIFICATION
# =========================================================
@app.post(
    "/verify",
    dependencies=[Depends(auth.verify_token)]
)
async def verify_faces(
    img1: UploadFile = File(...),
    img2: UploadFile = File(...)
):
    """
    Endpoint utama untuk membandingkan dua foto wajah.

    Endpoint ini membutuhkan authentication.
    User harus login terlebih dahulu.
    """

    # -----------------------------------------------------
    # Validasi tipe file
    # -----------------------------------------------------
    if img1.content_type not in config.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Foto 1 harus berformat JPG atau PNG"
        )

    if img2.content_type not in config.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Foto 2 harus berformat JPG atau PNG"
        )


    # -----------------------------------------------------
    # Baca file sebagai bytes
    # Tidak disimpan ke disk
    # -----------------------------------------------------
    img1_bytes = await img1.read()
    img2_bytes = await img2.read()


    # -----------------------------------------------------
    # Validasi ukuran file
    # -----------------------------------------------------
    if len(img1_bytes) > config.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Foto 1 melebihi "
                f"{config.MAX_FILE_SIZE_MB}MB"
            )
        )

    if len(img2_bytes) > config.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Foto 2 melebihi "
                f"{config.MAX_FILE_SIZE_MB}MB"
            )
        )


    # -----------------------------------------------------
    # Face verification
    # -----------------------------------------------------
    try:
        result = face_service.verify_faces(
            img1_bytes,
            img2_bytes
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )

    finally:
        # Bersihkan referensi bytes foto
        # setelah proses selesai.
        del img1_bytes
        del img2_bytes


    return result


# =========================================================
# FRONTEND STATIC FILES
# =========================================================
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "..",
    "frontend"
)


# =========================================================
# STATIC FRONTEND
# =========================================================
# Pastikan route "/" di atas didefinisikan
# sebelum mount StaticFiles.
app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True
    ),
    name="frontend"
)