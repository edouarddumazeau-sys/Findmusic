// Mets ici l'URL du PROXY une fois déployé (ex: https://ton-proxy.onrender.com)
const PROXY_URL = "https://findmusic-proxy.onrender.com"; // dev local

const $ = (id) => document.getElementById(id);

function renderSection(container, items) {
  if (!items || items.length === 0) {
    container.innerHTML = `<div class="status">Aucun résultat.</div>`;
    return;
  }
  container.innerHTML = items.map((s) => `
    <details>
      <summary>
        <strong>${escapeHtml(s.title || "")}</strong> — ${escapeHtml(s.artist || "")}
        ${s.year ? ` (${s.year})` : ""}
        • score: ${Math.round((s.relevance || 0) * 100)}%
        • ${escapeHtml((s.language_original || "").toUpperCase())}
      </summary>
      <div class="snip">${escapeHtml(s.snippet || "(pas d'extrait trouvé)")}</div>
      <div class="meta">
        densité: ${Math.round((s.density||0)*100)}% • centralité: ${Math.round((s.centrality||0)*100)}%
      </div>
    </details>
  `).join("");
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({
    "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
  }[m]));
}

$("go").addEventListener("click", async () => {
  const theme = $("theme").value.trim();
  if (!theme) return;

  $("status").textContent = "Recherche…";
  $("main").innerHTML = "";
  $("secondary").innerHTML = "";

  try {
    const res = await fetch(`${PROXY_URL}/search`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ theme, max_results: 20 })
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    $("status").textContent = `OK • requête: "${data.query}" (${(data.language_query||"").toUpperCase()})`;
    renderSection($("main"), data.results_main);
    renderSection($("secondary"), data.results_secondary);
  } catch (e) {
    $("status").textContent = "Erreur: " + (e.message || e);
  }
});
