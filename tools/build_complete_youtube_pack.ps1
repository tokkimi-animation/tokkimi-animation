$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$ready = Join-Path $root "ready-to-upload"
$pack = Join-Path $ready "PACK-YOUTUBE-COMPLET"
$episodes = Join-Path $pack "100-PACKS-EPISODES"

if (Test-Path -LiteralPath $pack) {
    Remove-Item -LiteralPath $pack -Recurse -Force
}
New-Item -ItemType Directory -Path $episodes -Force | Out-Null

1..100 | ForEach-Object {
    $id = "EP{0:D3}-upload-pack.zip" -f $_
    New-Item -ItemType HardLink `
        -Path (Join-Path $episodes $id) `
        -Target (Join-Path $ready $id) | Out-Null
}

Copy-Item -LiteralPath (Join-Path $ready "LUNI-YOUTUBE-PUBLICATION.xlsx") `
    -Destination (Join-Path $pack "LUNI-YOUTUBE-PUBLICATION.xlsx")
Copy-Item -LiteralPath (Join-Path $ready "OUVRIR-ICI.html") `
    -Destination (Join-Path $pack "OUVRIR-ICI.html")
Copy-Item -LiteralPath (Join-Path $ready "CONTROLE-VOIX-PERSONNAGES") `
    -Destination (Join-Path $pack "CONTROLE-VOIX-PERSONNAGES") -Recurse
Copy-Item -LiteralPath (Join-Path $ready "GENERIQUE-INTRO") `
    -Destination (Join-Path $pack "GENERIQUE-INTRO") -Recurse

@"
PACK YOUTUBE COMPLET - 달토끼 루니

Le dossier 100-PACKS-EPISODES contient les 100 packs prêts à publier.

Chaque ZIP contient :
- la vidéo MP4 ;
- la miniature ;
- les sous-titres coréens ;
- le titre et la description YouTube ;
- le script coréen/français.

Ouvrez LUNI-YOUTUBE-PUBLICATION.xlsx pour suivre l'ordre et le calendrier.
Ouvrez CONTROLE-VOIX-PERSONNAGES\ECOUTER-LES-8-VOIX.mp3 pour écouter
les huit voix définitives.

Le dossier GENERIQUE-INTRO contient :
- la version courte de 15 secondes à placer devant chaque épisode ;
- la version complète de présentation des huit personnages.
"@ | Set-Content -LiteralPath (Join-Path $pack "LISEZ-MOI.txt") -Encoding UTF8

Write-Output $pack
