# 달토끼 루니 · Luni Studio

Projet GitHub d’une série animée **en coréen** pour les enfants de 3 à 7 ans.  
Les documents de pilotage sont rédigés en **français** pour faciliter la production.

![Planche des personnages de 달토끼 루니](assets/images/luni-character-bible.png)

## Langues du projet

- **Coréen** : titres, dialogues, chansons, narration et vidéos YouTube.
- **Français** : bible de production, consignes, organisation et documentation.
- Les noms coréens officiels restent toujours visibles pour garantir la cohérence de la marque.

## Contenu

- 8 personnages officiels et leur univers
- 100 idées d’épisodes uniques réparties en 4 saisons
- site adaptatif prêt pour GitHub Pages
- structure d’un épisode de 3 minutes
- modèle de scénario et prompts de génération visuelle

## Aperçu local

```powershell
py -m http.server 8000
```

Ouvrir ensuite `http://localhost:8000`.

## Publication sur GitHub Pages

1. Créer un nouveau dépôt GitHub.
2. Déposer tous les fichiers de ce dossier à la racine.
3. Ouvrir `Settings > Pages`.
4. Choisir `Deploy from a branch`, puis `main` et `/ (root)`.
5. Enregistrer et ouvrir l’adresse publique fournie par GitHub.

## Documents

- [Bible de production](docs/PRODUCTION_BIBLE.md)
- [Modèle d’épisode](docs/EPISODE_TEMPLATE.md)
- [Prompts visuels IA](docs/AI_PROMPTS.md)

## État du projet

- Les 100 épisodes possèdent leur scénario coréen, leur contrôle français et leur texte YouTube.
- Le moteur de production fabrique automatiquement vidéo, voix, musique, sous-titres, miniature et archive de publication.
- Les rendus terminés sont rangés localement dans `ready-to-upload/`, dossier exclu de GitHub en raison de la taille des vidéos.
- Le site public présente la série en coréen et utilise le logo officiel Tokkimi.

© 2026 Luni Studio.
