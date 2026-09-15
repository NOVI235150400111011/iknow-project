document.addEventListener("DOMContentLoaded", async () => {
  // ===== CEK OTENTIKASI SEBELUM MENAMPILKAN HALAMAN =====
  // Mencegah index.html diakses langsung tanpa login
  // (misal dengan mengetik URL-nya manual di address bar).
  try {
    const authCheck = await fetch(`${API_BASE_URL}/check-auth`, {
      method: "GET",
      credentials: "include",
    });
    if (!authCheck.ok) {
      window.location.href = "login.html";
      return;
    }
  } catch (err) {
    window.location.href = "login.html";
    return;
  }

  // Token valid, tampilkan halaman
  document.body.style.visibility = "visible";

  // ===== KODE ASLI (tidak berubah dari sebelumnya) =====
  const fileInput1 = document.getElementById("file-input-1");
  const fileInput2 = document.getElementById("file-input-2");
  const uploadBtn1 = document.getElementById("upload-btn-1");
  const uploadBtn2 = document.getElementById("upload-btn-2");
  const box1 = document.getElementById("box1");
  const box2 = document.getElementById("box2");
  const checkBtn = document.getElementById("check-btn");
  const verifyError = document.getElementById("verify-error");

  const COLOR_MAP = {
    green: "#1e9e5a",
    yellow: "#d4a017",
    red: "#d32f2f"
  };

  let file1 = null;
  let file2 = null;

  uploadBtn1.addEventListener("click", () => fileInput1.click());
  uploadBtn2.addEventListener("click", () => fileInput2.click());

  fileInput1.addEventListener("change", (e) => {
    file1 = e.target.files[0];
    previewImage(box1, file1);
  });

  fileInput2.addEventListener("change", (e) => {
    file2 = e.target.files[0];
    previewImage(box2, file2);
  });

  function previewImage(box, file) {
    if (!file) return;
    const url = URL.createObjectURL(file);
    const img = box.querySelector("img");
    img.src = url;
  }

  checkBtn.addEventListener("click", async () => {
    verifyError.textContent = "";

    if (!file1 || !file2) {
      verifyError.textContent = "Silakan upload kedua foto terlebih dahulu.";
      return;
    }

    checkBtn.disabled = true;
    checkBtn.textContent = "Memproses...";

    const formData = new FormData();
    formData.append("img1", file1);
    formData.append("img2", file2);

    try {
      const res = await fetch(`${API_BASE_URL}/verify`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      if (res.status === 401) {
        window.location.href = "login.html";
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Terjadi kesalahan saat memproses foto.");
      }

      renderResult(data);
    } catch (err) {
      verifyError.textContent = err.message;
    } finally {
      checkBtn.disabled = false;
      checkBtn.textContent = "Periksa Foto";
    }
  });

  function renderResult(data) {
    const conclusionEl = document.getElementById("result-conclusion");
    const noteEl = document.getElementById("result-note");
    const donutEl = document.getElementById("donut-chart");
    const percentageEl = document.getElementById("donut-percentage");

    const percentage = data.similarity_percentage;
    const color = COLOR_MAP[data.conclusion_color] || COLOR_MAP.yellow;

    donutEl.style.background = `conic-gradient(${color} 0% ${percentage}%, #d9dee6 ${percentage}% 100%)`;
    percentageEl.textContent = `${percentage}%`;
    percentageEl.style.color = color;

    conclusionEl.textContent = data.conclusion;
    conclusionEl.className = "result-conclusion";
    conclusionEl.classList.add(`conclusion-${data.conclusion_color}`);

    noteEl.textContent = data.conclusion_note;
  }
});