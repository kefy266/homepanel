const $ = (id) => document.getElementById(id);
const fmt = (n) => {
  const gb = n / (1024 ** 3);
  return gb >= 1 ? gb.toFixed(1) + " GB" : (n / (1024 ** 2)).toFixed(0) + " MB";
};
function setMetric(id, barId, value) {
  $(id).textContent = `${Math.round(value)}%`;
  $(barId).style.width = `${Math.max(0, Math.min(100, value))}%`;
}
async function refresh() {
  try {
    const response = await fetch("/api/stats", {cache: "no-store"});
    if (response.status === 401) { location.href = "/login"; return; }
    if (!response.ok) throw new Error("API error");
    const d = await response.json();
    setMetric("cpu", "cpu-bar", d.cpu.usage);
    $("cores").textContent = `${d.cpu.logical_cores} mantıksal çekirdek`;
    setMetric("ram", "ram-bar", d.memory.percent);
    $("ram-detail").textContent = `${fmt(d.memory.used)} / ${fmt(d.memory.total)}`;
    setMetric("disk", "disk-bar", d.disk.percent);
    $("disk-detail").textContent = `${fmt(d.disk.used)} / ${fmt(d.disk.total)} · /`;
    if (d.gpu.available) {
      $("gpu").textContent = `${Math.round(d.gpu.usage)}%`;
      $("gpu-bar").style.width = `${d.gpu.usage}%`;
      $("gpu-detail").textContent = `${d.gpu.name} · ${Math.round(d.gpu.temperature_c)}°C · ${Math.round(d.gpu.memory_used_mb)}/${Math.round(d.gpu.memory_total_mb)} MB`;
    } else {
      $("gpu").textContent = "N/A"; $("gpu-bar").style.width = "0%";
      $("gpu-detail").textContent = "NVIDIA GPU bulunamadı";
    }
    $("updated").textContent = "Son güncelleme: " + new Date().toLocaleTimeString("tr-TR");
  } catch (_) { $("updated").textContent = "Sistem verisi alınamadı"; }
}
refresh(); setInterval(refresh, 2500);
$("create-transfer").addEventListener("click", async () => {
  const btn = $("create-transfer"); btn.disabled = true; btn.textContent = "Hazırlanıyor…";
  try {
    const response = await fetch("/api/transfer/new", {method: "POST"});
    if (!response.ok) throw new Error("QR oluşturulamadı");
    const data = await response.json();
    const token = new URL(data.url).pathname.split("/").pop();
    $("qr-area").innerHTML = `<img class="qr-image" src="/api/transfer/qr/${encodeURIComponent(token)}.png" alt="Dosya aktarım QR kodu"><a class="upload-link" href="${data.url}" target="_blank" rel="noopener">Aktarım sayfasını aç ↗</a>`;
    $("transfer-status").textContent = "QR hazır · 10 dakika geçerli · Tek kullanımlık";
  } catch (e) { $("transfer-status").textContent = "Bir hata oluştu. Tekrar dene."; }
  finally { btn.disabled = false; btn.innerHTML = 'QR kod oluştur <span>↗</span>'; }
});
