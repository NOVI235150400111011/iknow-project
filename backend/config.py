import os
from dotenv import load_dotenv

load_dotenv()

# Autentikasi
SITE_PASSWORD = os.getenv("SITE_PASSWORD")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

# Mode development - True selama di lokal, ganti ke False saat production (HTTPS)
IS_DEV = os.getenv("IS_DEV", "true").lower() == "true"

# Face verification
SIMILARITY_THRESHOLD = 0.30

# Upload validation
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]

# Validasi dasar saat startup, biar cepat ketahuan kalau .env belum diisi
if not SITE_PASSWORD:
    raise ValueError("SITE_PASSWORD belum diset di file .env")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET belum diset di file .env")