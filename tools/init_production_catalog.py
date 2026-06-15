import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_JS = ROOT / "script.js"
PRODUCTION = ROOT / "production"
CATALOG_PATH = PRODUCTION / "catalog.json"

SEASON_NAMES = {
    1: "세상 발견",
    2: "신나는 모험",
    3: "마법의 세계",
    4: "함께 성장",
}

ROW_PATTERN = re.compile(
    r'\[(\d+),"([^"]+)","([^"]+)","([^"]+)"\]',
    re.MULTILINE,
)


def slug_for(number):
    return f"ep{number:03d}"


def has_batchim(text):
    for character in reversed(text.strip()):
        if "\uac00" <= character <= "\ud7a3":
            return (ord(character) - 0xAC00) % 28 != 0
    return False


def particle(text, with_batchim, without_batchim):
    return with_batchim if has_batchim(text) else without_batchim


def youtube_title(number, title, lesson):
    return (
        f"{title} | 달토끼 루니 EP.{number:03d} | "
        f"{lesson}{particle(lesson, '을', '를')} 배워요"
    )


def youtube_description(title, premise, lesson):
    return (
        f"{premise}\n\n"
        f"오늘의 배움은 '{lesson}'{particle(lesson, '이에요', '예요')}.\n"
        "달토끼 루니와 친구들이 함께 생각하고 노래하며 답을 찾아가요.\n\n"
        "#달토끼루니 #어린이애니메이션 #유아교육 #키즈콘텐츠"
    )


def episode_readme(episode):
    status = episode["status"]
    return f"""# EP{episode['number']:03d} · {episode['title']}

- Saison : {episode['season']} · {episode['season_name']}
- Apprentissage : {episode['lesson']}
- Synopsis : {episode['premise']}
- Durée cible : {episode['target_duration']}
- Statut : {status}

## Livrables

- `script-ko-fr.md` : scénario coréen et traduction française de contrôle
- `storyboard.md` : plans, actions, expressions et mouvements
- `subtitles-ko.srt` : sous-titres coréens
- `youtube.txt` : titre, description et réglages de publication
- `thumbnail.png` : miniature YouTube
- `EP{episode['number']:03d}.mp4` : vidéo finale
"""


def youtube_text(episode):
    return f"""TITRE
{episode['youtube']['title']}

DESCRIPTION
{episode['youtube']['description']}

RÉGLAGES
Langue : coréen
Contenu conçu pour les enfants : oui
Catégorie : Film et animation
Playlist : 달토끼 루니 시즌 {episode['season']} | {episode['season_name']}
Visibilité de contrôle : non répertoriée
"""


def main():
    rows = ROW_PATTERN.findall(SCRIPT_JS.read_text(encoding="utf-8"))
    if len(rows) != 100:
        raise RuntimeError(f"100 episodes expected, found {len(rows)}")

    episodes = []
    for number, (season, title, lesson, premise) in enumerate(rows, start=1):
        season = int(season)
        season_dir = PRODUCTION / f"season-{season:02d}"
        episode_dir = season_dir / slug_for(number)
        scripted = (episode_dir / "episode.json").exists()
        episode = {
            "number": number,
            "id": f"EP{number:03d}",
            "slug": slug_for(number),
            "season": season,
            "season_name": SEASON_NAMES[season],
            "title": title,
            "lesson": lesson,
            "premise": premise,
            "target_duration": "5 min pilot" if number == 1 else "3 min",
            "status": (
                "pilot-complete"
                if number == 1
                else "scripted"
                if scripted
                else "planned"
            ),
            "deliverables": {
                "script": number == 1 or scripted,
                "voices": number == 1,
                "animation": number == 1,
                "subtitles": number == 1,
                "thumbnail": number == 1,
                "youtube_pack": number == 1,
            },
            "youtube": {
                "title": youtube_title(number, title, lesson),
                "description": youtube_description(title, premise, lesson),
            },
        }
        episodes.append(episode)

        episode_dir.mkdir(parents=True, exist_ok=True)

        readme_path = episode_dir / "README.md"
        if not readme_path.exists():
            readme_path.write_text(episode_readme(episode), encoding="utf-8")

        youtube_path = episode_dir / "youtube.txt"
        if not youtube_path.exists():
            youtube_path.write_text(youtube_text(episode), encoding="utf-8")

    PRODUCTION.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(
        json.dumps(
            {
                "series": "달토끼 루니",
                "language": "ko",
                "control_language": "fr",
                "episode_count": len(episodes),
                "regular_duration": "3 min",
                "model": "luni-model-preview-v3",
                "episodes": episodes,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Initialized {len(episodes)} episodes in {PRODUCTION}")


if __name__ == "__main__":
    main()
