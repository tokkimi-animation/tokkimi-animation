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

## Animation articulée

Le test `tools/build_rig_motion_test.py` utilise une marionnette composée de
calques indépendants :

- tête et oreilles ;
- corps, bras et transfert de poids ;
- yeux ouverts et fermés ;
- formes de bouche pilotées par l’amplitude de la voix ;
- respiration, regard et gestes secondaires.

Cette approche doit remplacer le montage de poses fixes pour les personnages
principaux. Adobe Character Animator est la cible recommandée pour finaliser
les rigs, le lip-sync et les gestes réutilisables sur les 100 épisodes.
