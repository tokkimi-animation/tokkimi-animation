import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "production" / "catalog.json"

DURATIONS = [10, 9, 8, 10, 10, 9, 10, 8, 10, 10, 11, 10, 10, 13, 10, 10, 22]
FRIENDS = [
    ("별이", "생각을 차근차근 정리해 보자.", "Réfléchissons étape par étape."),
    ("몽이", "실수해도 웃으며 다시 해 보면 돼!", "On peut sourire et recommencer après une erreur."),
    ("콩콩", "내가 먼저 살펴보고 올게!", "Je vais regarder le chemin en premier."),
    ("토리", "새로운 방법을 만들어 보자!", "Inventons une nouvelle méthode."),
    ("밤밤", "마음을 천천히 말해도 괜찮아.", "On peut prendre son temps pour parler de ses émotions."),
    ("루미", "좋은 질문을 하면 길이 보일 거야.", "Une bonne question nous montrera le chemin."),
]

LOCATIONS = [
    "달나라 마을",
    "구름 숲",
    "별빛 호수",
    "무지개 언덕",
    "별빛 기차역",
    "꿈의 정원",
    "마법 도서관",
    "달의 성",
]

ACTIONS = [
    "arrive-and-look",
    "worried",
    "hand-to-heart",
    "point-clues",
    "collect-colors",
    "small-sneeze",
    "kneel-and-point",
    "group-happy",
    "show-three",
    "follow-stream",
    "inspect-stone",
    "audience-search",
    "raise-colors",
    "rainbow-appears",
    "happy-tears",
    "rainbow-pose",
    "ending-dance",
]

POSES = [
    "welcome",
    "worried",
    "encourage",
    "thinking",
    "happy",
    "surprised",
    "point",
    "group-happy",
    "thinking",
    "running",
    "worried",
    "listening",
    "happy",
    "group-cheer",
    "relieved",
    "welcome",
    "dance",
]


def scene(duration, speaker, text, fr, pose, action):
    return {
        "duration": duration,
        "speaker": speaker,
        "voice": "ko-KR-SunHiNeural",
        "text": text,
        "fr": fr,
        "pose": pose,
        "action": action,
    }


def make_scenes(episode):
    number = episode["number"]
    title = episode["title"]
    lesson = episode["lesson"]
    premise = episode["premise"]
    friend, friend_line, friend_fr = FRIENDS[(number - 3) % len(FRIENDS)]
    repeat = f"{lesson}, 우리 함께 천천히 해 보자!"

    lines = [
        ("루니", f"안녕, 친구들! 오늘은 {title} 이야기를 만나 볼 거야.", f"Bonjour les amis ! Aujourd’hui, découvrons l’histoire « {title} »."),
        (friend, f"루니야, 여기 도움이 필요한 일이 생겼어. {premise}", f"Un problème est arrivé : {premise}"),
        ("루니", f"걱정하지 마. 오늘은 {lesson}을 생각하며 함께 답을 찾아보자!", f"Ne t’inquiète pas. Cherchons une réponse en pensant à : {lesson}."),
        (friend, friend_line, friend_fr),
        ("루니", "첫 번째 방법을 해 볼까? 친구들도 우리와 함께 잘 살펴봐 줘.", "Essayons une première méthode. Regardez bien avec nous."),
        ("모두", "하나, 둘, 셋! 천천히 시작해 보자.", "Un, deux, trois ! Commençons doucement."),
        ("루니", "음, 이 방법만으로는 조금 부족한 것 같아. 무엇을 바꾸면 좋을까?", "Cette méthode ne suffit pas. Que pourrions-nous changer ?"),
        (friend, f"{repeat}", f"{lesson} : avançons doucement ensemble."),
        ("루니", "친구들, 화면 속 단서를 찾아 줄래? 작은 것도 놓치지 말자.", "Les amis, trouvez l’indice à l’écran. N’oublions aucun petit détail."),
        ("루니", "찾았다! 이제 두 번째 방법을 해 볼 수 있어.", "Trouvé ! Nous pouvons essayer une deuxième méthode."),
        (friend, "이번에는 서로의 생각을 잘 듣고 힘을 모아 보자.", "Cette fois, écoutons les idées de chacun et unissons nos forces."),
        ("모두", "좋아! 우리 함께하면 할 수 있어!", "Oui ! Ensemble, nous pouvons réussir !"),
        ("루니", f"조금씩 답이 보이기 시작해. {lesson}이 왜 중요한지 알 것 같아.", f"La réponse apparaît. Nous comprenons pourquoi {lesson} est important."),
        ("모두", "마지막으로 한 번 더! 하나, 둘, 셋!", "Une dernière fois ! Un, deux, trois !"),
        (friend, "해냈어! 아까 걱정하던 마음이 이제 편안하고 기뻐졌어.", "Nous avons réussi ! L’inquiétude a laissé place à la joie."),
        ("루니", f"오늘은 {lesson}을 배웠어. 우리 함께 천천히 하면 다시 해낼 수 있어!", f"Aujourd’hui, nous avons appris : {lesson}. Ensemble, nous pouvons recommencer."),
        ("노래", f"{lesson}, 함께 배워요. 마음을 모아 웃어요. 루니 루니 달토끼, 오늘도 함께해요.", f"Apprenons {lesson} ensemble. Luni et ses amis sourient ensemble."),
    ]

    return [
        scene(duration, speaker, text, fr, pose, action)
        for duration, (speaker, text, fr), pose, action in zip(
            DURATIONS, lines, POSES, ACTIONS
        )
    ]


def script_markdown(episode, data):
    transcript = []
    for index, item in enumerate(data["scenes"], start=1):
        transcript.append(
            f"### Plan {index:02d} · {item['duration']} s\n\n"
            f"**{item['speaker']}**  \n{item['text']}\n\n"
            f"*Contrôle français : {item['fr']}*\n"
        )
    return (
        f"# EP{episode['number']:03d} · {episode['title']}\n\n"
        f"- Saison : {episode['season']} · {episode['season_name']}\n"
        f"- Apprentissage : {episode['lesson']}\n"
        f"- Synopsis : {episode['premise']}\n"
        f"- Décor principal : {data['location']}\n"
        f"- Durée cible : 3 minutes\n\n"
        "## Scénario\n\n"
        + "\n".join(transcript)
    )


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    generated = 0
    for episode in catalog["episodes"]:
        number = episode["number"]
        if number < 3:
            continue
        directory = (
            ROOT
            / "production"
            / f"season-{episode['season']:02d}"
            / f"ep{number:03d}"
        )
        spec_path = directory / "episode.json"
        if spec_path.exists():
            continue

        friend = FRIENDS[(number - 3) % len(FRIENDS)][0]
        data = {
            "number": number,
            "title": episode["title"],
            "lesson": episode["lesson"],
            "duration_target": 180,
            "location": LOCATIONS[(number - 1) % len(LOCATIONS)],
            "repeat_phrase": f"{episode['lesson']}, 우리 함께 천천히 해 보자!",
            "characters": ["루니", friend],
            "scenes": make_scenes(episode),
        }
        spec_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (directory / "script-ko-fr.md").write_text(
            script_markdown(episode, data),
            encoding="utf-8",
        )
        episode["status"] = "scripted"
        episode["deliverables"]["script"] = True
        generated += 1

    CATALOG.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {generated} episode specifications")


if __name__ == "__main__":
    main()
