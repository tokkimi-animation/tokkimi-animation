import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "ready-to-upload"
CATALOG = ROOT / "production" / "catalog.json"


def file_exists(path):
    return path.exists() and path.stat().st_size > 0


def card(episode):
    number = episode["number"]
    episode_id = episode["id"]
    video_name = "EP001-lost-star.mp4" if number == 1 else f"{episode_id}.mp4"
    folder = READY / episode_id
    links = {
        "Vidéo": f"{episode_id}/{video_name}",
        "Miniature": f"{episode_id}/thumbnail.png",
        "Sous-titres": f"{episode_id}/subtitles-ko.srt",
        "Texte YouTube": f"{episode_id}/youtube.txt",
        "Pack ZIP": f"{episode_id}-upload-pack.zip",
    }
    ready = all(file_exists(READY / value) for value in links.values())
    link_html = "".join(
        f'<a href="{html.escape(value)}">{label}</a>'
        if file_exists(READY / value)
        else f'<span class="missing">{label}</span>'
        for label, value in links.items()
    )
    thumbnail = (
        f'<img loading="lazy" src="{episode_id}/thumbnail.png" '
        f'alt="{html.escape(episode["title"])}">'
        if file_exists(folder / "thumbnail.png")
        else '<div class="placeholder">EN PRODUCTION</div>'
    )
    return f"""
      <article class="episode-card" data-season="{episode['season']}"
        data-search="{html.escape((episode_id + ' ' + episode['title'] + ' ' + episode['lesson']).lower())}">
        <div class="visual">{thumbnail}<span class="status {'ready' if ready else 'working'}">
          {'PRÊT' if ready else 'EN PRODUCTION'}</span></div>
        <div class="content">
          <p class="episode">{episode_id} · Saison {episode['season']}</p>
          <h2>{html.escape(episode['title'])}</h2>
          <p class="lesson">Apprentissage : {html.escape(episode['lesson'])}</p>
          <p class="premise">{html.escape(episode['premise'])}</p>
          <div class="links">{link_html}</div>
        </div>
      </article>"""


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cards = "\n".join(card(episode) for episode in catalog["episodes"])
    ready_count = sum(
        1
        for episode in catalog["episodes"]
        if file_exists(
            READY
            / f"{episode['id']}-upload-pack.zip"
        )
    )
    document = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Luni · 100 épisodes prêts pour YouTube</title>
  <style>
    :root {{ --purple:#6b5aa6; --ink:#30294f; --cream:#fffaf1; --gold:#f3c969;
      --mint:#a9d8d0; --line:#e5dff0; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); font-family:"Segoe UI",Arial,sans-serif;
      background:linear-gradient(180deg,#f1edff,#fffaf1 330px); }}
    header {{ padding:38px 5vw 28px; text-align:center; }}
    .logo {{ width:84px; height:84px; object-fit:contain; border-radius:50%; background:#fff; }}
    h1 {{ margin:12px 0 4px; font-size:clamp(1.8rem,4vw,3rem); }}
    header p {{ margin:5px 0; }}
    .progress {{ display:inline-block; margin-top:14px; padding:9px 16px; border-radius:999px;
      background:var(--gold); font-weight:800; }}
    .controls {{ position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; gap:10px;
      justify-content:center; padding:14px; background:rgba(255,255,255,.94);
      border-block:1px solid var(--line); backdrop-filter:blur(8px); }}
    input,button {{ border:1px solid var(--line); border-radius:12px; padding:11px 14px;
      font:inherit; background:#fff; color:var(--ink); }}
    input {{ min-width:min(420px,85vw); }}
    button {{ cursor:pointer; font-weight:700; }}
    button.active {{ background:var(--purple); color:#fff; }}
    main {{ width:min(1500px,94vw); margin:25px auto 80px; display:grid;
      grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:20px; }}
    .episode-card {{ overflow:hidden; border:1px solid var(--line); border-radius:20px;
      background:#fff; box-shadow:0 12px 35px rgba(69,53,112,.10); }}
    .visual {{ position:relative; aspect-ratio:16/9; background:#ece7f6; }}
    .visual img {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .placeholder {{ height:100%; display:grid; place-items:center; color:#877aa8; font-weight:800; }}
    .status {{ position:absolute; right:12px; top:12px; padding:6px 10px; border-radius:999px;
      color:#fff; font-size:.75rem; font-weight:900; }}
    .status.ready {{ background:#26865e; }} .status.working {{ background:#a7791e; }}
    .content {{ padding:18px; }}
    .episode {{ margin:0; color:var(--purple); font-weight:800; font-size:.82rem; }}
    h2 {{ margin:7px 0; font-size:1.35rem; }}
    .lesson {{ margin:6px 0; font-weight:700; }}
    .premise {{ min-height:3.1em; line-height:1.5; color:#655d7a; }}
    .links {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:15px; }}
    .links a,.missing {{ padding:7px 9px; border-radius:9px; font-size:.78rem;
      text-decoration:none; font-weight:700; }}
    .links a {{ background:#eee9fa; color:var(--purple); }}
    .missing {{ background:#f3f1f5; color:#aaa; }}
    [hidden] {{ display:none!important; }}
  </style>
</head>
<body>
  <header>
    <img class="logo" src="../assets/images/tokkimi-logo.png" alt="Tokkimi">
    <h1>달토끼 루니 · Pack YouTube</h1>
    <p>Tout ce qu’il faut pour publier les 100 épisodes.</p>
    <div class="progress">{ready_count} / 100 packs prêts</div>
  </header>
  <section class="controls">
    <input id="search" type="search" placeholder="Chercher un épisode, un titre ou un apprentissage">
    <button class="active" data-season="all">Toutes</button>
    <button data-season="1">Saison 1</button>
    <button data-season="2">Saison 2</button>
    <button data-season="3">Saison 3</button>
    <button data-season="4">Saison 4</button>
  </section>
  <main>{cards}</main>
  <script>
    const cards=[...document.querySelectorAll('.episode-card')];
    const search=document.querySelector('#search');
    let season='all';
    function filter(){{
      const query=search.value.trim().toLowerCase();
      cards.forEach(card=>{{
        card.hidden=!(season==='all'||card.dataset.season===season)||
          !card.dataset.search.includes(query);
      }});
    }}
    search.addEventListener('input',filter);
    document.querySelectorAll('button[data-season]').forEach(button=>button.addEventListener('click',()=>{{
      season=button.dataset.season;
      document.querySelectorAll('button[data-season]').forEach(item=>item.classList.remove('active'));
      button.classList.add('active'); filter();
    }}));
  </script>
</body>
</html>
"""
    (READY / "OUVRIR-ICI.html").write_text(document, encoding="utf-8")
    print(f"Upload index generated with {ready_count} ready episodes")


if __name__ == "__main__":
    main()
