import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "ready-to-upload"
CATALOG = ROOT / "production" / "catalog.json"
FINAL_MP4_PACK = READY / "PACK-YOUTUBE-100-MP4-AVEC-INTRO"


def file_exists(path):
    return path.exists() and path.stat().st_size > 0


def episode_ready(episode):
    number = episode["number"]
    episode_id = episode["id"]
    video_name = "EP001-lost-star.mp4" if number == 1 else f"{episode_id}.mp4"
    required = [
        READY / episode_id / video_name,
        READY / episode_id / "thumbnail.png",
        READY / episode_id / "subtitles-ko.srt",
        READY / episode_id / "youtube.txt",
        READY / episode_id / "script-ko-fr.md",
        READY / f"{episode_id}-upload-pack.zip",
    ]
    return all(file_exists(path) for path in required)


def card(episode):
    number = episode["number"]
    episode_id = episode["id"]
    video_name = "EP001-lost-star.mp4" if number == 1 else f"{episode_id}.mp4"
    folder = READY / episode_id
    final_name = f"{episode_id}-YOUTUBE-AVEC-INTRO.mp4"
    final_video = FINAL_MP4_PACK / final_name
    video_url = (
        f"PACK-YOUTUBE-100-MP4-AVEC-INTRO/{final_name}"
        if file_exists(final_video)
        else f"{episode_id}/{video_name}"
    )
    links = {
        "Miniature": f"{episode_id}/thumbnail.png",
        "Sous-titres": f"{episode_id}/subtitles-ko.srt",
        "Texte YouTube": f"{episode_id}/youtube.txt",
        "Pack ZIP": f"{episode_id}-upload-pack.zip",
    }
    ready = episode_ready(episode)
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
        <button class="visual play-video" type="button"
          data-video="{html.escape(video_url)}"
          aria-label="Lire {html.escape(episode_id)}">
          {thumbnail}<span class="play-icon">▶</span>
          <span class="status {'ready' if ready else 'working'}">
          {'PRÊT' if ready else 'EN PRODUCTION'}</span></button>
        <div class="content">
          <p class="episode">{episode_id} · Saison {episode['season']}</p>
          <h2>{html.escape(episode['title'])}</h2>
          <p class="lesson">Apprentissage : {html.escape(episode['lesson'])}</p>
          <p class="premise">{html.escape(episode['premise'])}</p>
          <a class="watch" href="{html.escape(video_url)}" target="_blank"
            rel="noopener">▶ Lire la vidéo</a>
          <a class="watch" href="{html.escape(video_url)}" download>
            Télécharger le MP4 avec générique</a>
          <button class="inline-play play-video" type="button"
            data-video="{html.escape(video_url)}">Ouvrir dans la page</button>
          <div class="links">{link_html}</div>
        </div>
      </article>"""


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cards = "\n".join(card(episode) for episode in catalog["episodes"])
    ready_count = sum(episode_ready(episode) for episode in catalog["episodes"])
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
    .pack-links {{ display:flex; flex-wrap:wrap; justify-content:center; gap:9px; margin-top:14px; }}
    .pack-links a {{ padding:10px 14px; border-radius:11px; color:#fff;
      background:var(--purple); text-decoration:none; font-weight:800; }}
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
    .visual {{ position:relative; width:100%; aspect-ratio:16/9; padding:0; border:0;
      border-radius:0; overflow:hidden; background:#ece7f6; cursor:pointer; }}
    .visual img {{ width:100%; height:100%; object-fit:cover; display:block; }}
    .play-icon {{ position:absolute; left:50%; top:50%; translate:-50% -50%;
      width:64px; height:64px; display:grid; place-items:center; padding-left:4px;
      border-radius:50%; background:rgba(107,90,166,.92); color:#fff;
      font-size:1.55rem; box-shadow:0 8px 25px rgba(48,41,79,.35); }}
    .placeholder {{ height:100%; display:grid; place-items:center; color:#877aa8; font-weight:800; }}
    .status {{ position:absolute; right:12px; top:12px; padding:6px 10px; border-radius:999px;
      color:#fff; font-size:.75rem; font-weight:900; }}
    .status.ready {{ background:#26865e; }} .status.working {{ background:#a7791e; }}
    .content {{ padding:18px; }}
    .episode {{ margin:0; color:var(--purple); font-weight:800; font-size:.82rem; }}
    h2 {{ margin:7px 0; font-size:1.35rem; }}
    .lesson {{ margin:6px 0; font-weight:700; }}
    .premise {{ min-height:3.1em; line-height:1.5; color:#655d7a; }}
    .watch {{ display:block; width:100%; margin-top:10px; padding:12px 14px;
      border-radius:12px; background:var(--purple); color:#fff; text-align:center;
      text-decoration:none; font-weight:900; font-size:1rem; }}
    .inline-play {{ width:100%; margin-top:7px; padding:8px; font-size:.82rem; }}
    .links {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:15px; }}
    .links a,.missing {{ padding:7px 9px; border-radius:9px; font-size:.78rem;
      text-decoration:none; font-weight:700; }}
    .links a {{ background:#eee9fa; color:var(--purple); }}
    .missing {{ background:#f3f1f5; color:#aaa; }}
    dialog {{ width:min(1000px,94vw); padding:0; border:0; border-radius:20px;
      background:#171323; box-shadow:0 25px 90px rgba(0,0,0,.5); }}
    dialog::backdrop {{ background:rgba(20,15,35,.82); }}
    .player-head {{ display:flex; justify-content:space-between; align-items:center;
      padding:10px 14px; color:#fff; }}
    .player-head button {{ border:0; background:#fff; font-weight:900; }}
    #player {{ display:block; width:100%; max-height:78vh; background:#000; }}
    [hidden] {{ display:none!important; }}
  </style>
</head>
<body>
  <header>
    <img class="logo" src="../assets/images/tokkimi-logo.png" alt="Tokkimi">
    <h1>달토끼 루니 · Pack YouTube</h1>
    <p>Tout ce qu’il faut pour publier les 100 épisodes.</p>
    <div class="progress">{ready_count} / 100 packs prêts</div>
    <div class="pack-links">
      <a href="LUNI-YOUTUBE-PUBLICATION.xlsx">Tableau de publication</a>
      <a href="PACK-YOUTUBE-COMPLET/LISEZ-MOI.txt">Pack YouTube complet</a>
      <a href="PACK-YOUTUBE-100-MP4-AVEC-INTRO/">
        100 MP4 finaux avec générique</a>
      <a href="CONTROLE-VOIX-PERSONNAGES/ECOUTER-LES-8-VOIX.mp3">
        Écouter les 8 voix</a>
      <a href="GENERIQUE-INTRO/REGARDER-LE-GENERIQUE.html">
        Voir le générique</a>
    </div>
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
  <dialog id="video-dialog">
    <div class="player-head"><strong>Clique sur ▶ dans la vidéo pour démarrer</strong>
      <button id="close-player" type="button">Fermer</button></div>
    <video id="player" controls playsinline></video>
  </dialog>
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
    const dialog=document.querySelector('#video-dialog');
    const player=document.querySelector('#player');
    document.querySelectorAll('.play-video').forEach(button=>button.addEventListener('click',()=>{{
      player.src=button.dataset.video;
      dialog.showModal();
      player.load();
    }}));
    function closePlayer(){{
      player.pause(); player.removeAttribute('src'); player.load(); dialog.close();
    }}
    document.querySelector('#close-player').addEventListener('click',closePlayer);
    dialog.addEventListener('click',event=>{{ if(event.target===dialog) closePlayer(); }});
  </script>
</body>
</html>
"""
    (READY / "OUVRIR-ICI.html").write_text(document, encoding="utf-8")
    print(f"Upload index generated with {ready_count} ready episodes")


if __name__ == "__main__":
    main()
