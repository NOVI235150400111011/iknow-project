import cv2
import numpy as np
from insightface.app import FaceAnalysis
import config

# Load model SEKALI saat modul ini pertama kali diimport (bukan tiap request)
print("Loading InsightFace model (buffalo_l)...")
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=-1)  # ctx_id=-1 = pakai CPU. Ganti ke 0 kalau nanti pakai GPU (CUDA)
print("Model loaded.")


def decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode bytes gambar jadi numpy array, langsung di memory (tidak ditulis ke disk)."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Gagal decode gambar. Pastikan file yang diupload adalah gambar valid (jpg/png).")
    return img


def extract_embedding(img: np.ndarray):
    """
    Deteksi wajah dan ekstrak embedding dari satu gambar.
    Return None kalau tidak ada wajah terdeteksi.
    """
    faces = face_app.get(img)
    if len(faces) == 0:
        return None
    if len(faces) > 1:
        faces = sorted(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)
    return faces[0].embedding


def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Hitung cosine similarity antara dua embedding."""
    return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))


def _build_conclusion(similarity: float, threshold: float, is_same_person: bool) -> dict:
    """
    Buat kesimpulan (label, notes, warna) berdasarkan seberapa jauh
    similarity dari threshold.
    """
    margin = abs(similarity - threshold)

    if is_same_person:
        if margin > 0.1:
            return {
                "label": "ORANG YANG SAMA",
                "note": "Hasil menunjukkan tingkat kemiripan yang tinggi. Sangat diyakini kedua foto adalah orang yang sama.",
                "color": "green"
            }
        else:
            return {
                "label": "MUNGKIN ORANG YANG SAMA",
                "note": "Cenderung orang yang sama, namun tingkat kemiripan di ambang batas. Terdapat perbedaan yang mungkin disebabkan oleh rendahnya kualitas foto,  pencahayaan dan perbedaan usia pada foto. Disarankan untuk memverifikasi kembali.",
                "color": "yellow"
            }
    else:
        if margin > 0.1:
            return {
                "label": "ORANG YANG BERBEDA",
                "note": "Hasil menunjukkan tingkat kemiripan yang sangat rendah. Sangat diyakini kedua foto adalah orang yang berbeda.",
                "color": "red"
            }
        else:
            return {
                "label": "MUNGKIN ORANG YANG BERBEDA",
                "note": "Cenderung orang yang berbeda, namun tingkat kemiripan di ambang batas. Tingkat kemiripan mungkin disebabkan  hubugan kekerabatan (anak/saudara), riasan wajah, atau adanya kerusakan foto. Disarankan untuk memverifikasi kembali.",
                "color": "yellow"
            }


def verify_faces(img1_bytes: bytes, img2_bytes: bytes) -> dict:
    """
    Fungsi utama: terima 2 gambar (bytes), return hasil perbandingan.
    Tidak ada langkah yang menulis ke disk di mana pun dalam fungsi ini.
    """
    img1 = decode_image(img1_bytes)
    img2 = decode_image(img2_bytes)

    emb1 = extract_embedding(img1)
    if emb1 is None:
        raise ValueError("Wajah tidak terdeteksi di foto pertama.")

    emb2 = extract_embedding(img2)
    if emb2 is None:
        raise ValueError("Wajah tidak terdeteksi di foto kedua.")

    similarity = cosine_similarity(emb1, emb2)
    is_same_person = similarity > config.SIMILARITY_THRESHOLD

    similarity_percentage = round(max(0, min(similarity, 1)) * 100, 2)

    conclusion_data = _build_conclusion(similarity, config.SIMILARITY_THRESHOLD, is_same_person)

    del img1, img2, emb1, emb2

    return {
        "similarity": round(similarity, 4),
        "similarity_percentage": similarity_percentage,
        "threshold": config.SIMILARITY_THRESHOLD,
        "is_same_person": is_same_person,
        "conclusion": conclusion_data["label"],
        "conclusion_note": conclusion_data["note"],
        "conclusion_color": conclusion_data["color"]
    }