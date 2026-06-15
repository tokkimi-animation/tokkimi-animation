import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "production" / "catalog.json"


def has_batchim(text):
    for character in reversed(text.strip()):
        if "\uac00" <= character <= "\ud7a3":
            return (ord(character) - 0xAC00) % 28 != 0
    return False


def particle(text, with_batchim, without_batchim):
    return with_batchim if has_batchim(text) else without_batchim


def youtube_title(episode):
    lesson = episode["lesson"]
    return (
        f"{episode['title']} | 달토끼 루니 EP.{episode['number']:03d} | "
        f"{lesson}{particle(lesson, '을', '를')} 배워요"
    )


def youtube_description(episode):
    lesson = episode["lesson"]
    return (
        f"{episode['premise']}\n\n"
        f"오늘의 배움은 '{lesson}'{particle(lesson, '이에요', '예요')}.\n"
        "달토끼 루니와 친구들이 함께 생각하고 노래하며 답을 찾아가요.\n\n"
        "#달토끼루니 #어린이애니메이션 #유아교육 #키즈콘텐츠"
    )


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-ready", action="store_true")
    args = parser.parse_args()

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    ready_updates = 0
    for episode in catalog["episodes"]:
        episode["youtube"]["title"] = youtube_title(episode)
        episode["youtube"]["description"] = youtube_description(episode)
        directory = (
            ROOT
            / "production"
            / f"season-{episode['season']:02d}"
            / f"ep{episode['number']:03d}"
        )
        (directory / "youtube.txt").write_text(
            youtube_text(episode),
            encoding="utf-8",
        )
        ready_path = (
            ROOT
            / "ready-to-upload"
            / episode["id"]
            / "youtube.txt"
        )
        if args.update_ready and ready_path.parent.exists():
            ready_path.write_text(youtube_text(episode), encoding="utf-8")
            ready_updates += 1

    CATALOG.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Updated {len(catalog['episodes'])} metadata files; "
        f"ready folders updated: {ready_updates}"
    )


if __name__ == "__main__":
    main()
