# Tokkimi Remaster Pipeline

Le pipeline de remasterisation transforme les épisodes existants en montages
plus courts, animés et adaptés à YouTube.

## Un épisode

```text
npm run remaster:episode -- EP001
```

Les fichiers sont écrits dans `remastered/EP001/` :

- `EP001-REMASTERED-YOUTUBE.mp4`
- `EP001-AVANT-APRES.mp4`
- `storyboard.json`
- `subtitles-ko.srt`
- `comparison.json`
- `REGARDER-EP001.html`

## Les 100 épisodes

```text
npm run remaster:all
```

Cette commande traite `EP001` à `EP100` et écrit chaque résultat dans
`remastered/EPxxx/`.

## Règles du moteur

- plans de 3 à 7 secondes ;
- alternance automatique des échelles de plan ;
- deux images-clés minimum par plan pour EP001 ;
- mouvement caméra obligatoire ;
- réactions des personnages pendant les pauses ;
- blancs de dialogue limités à 0,8 seconde ;
- musique continue avec réduction automatique sous les voix ;
- particules, lumière et éléments magiques animés ;
- export 1920 × 1080 à 30 FPS ;
- intro et outro YouTube.
