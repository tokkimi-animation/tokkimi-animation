import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const root = path.resolve(import.meta.dirname, "..");
const catalog = JSON.parse(
  await fs.readFile(path.join(root, "production", "catalog.json"), "utf8"),
);
const outputDir = path.join(root, "ready-to-upload");
const outputPath = path.join(outputDir, "LUNI-YOUTUBE-PUBLICATION.xlsx");

async function exists(filePath) {
  try {
    const stats = await fs.stat(filePath);
    return stats.size > 0;
  } catch {
    return false;
  }
}

const publicationStart = new Date("2026-06-22T12:00:00Z");
const rows = [];
for (const episode of catalog.episodes) {
  const id = episode.id;
  const folder = path.join(outputDir, id);
  const videoName = episode.number === 1 ? "EP001-lost-star.mp4" : `${id}.mp4`;
  const video = path.join(folder, videoName);
  const thumbnail = path.join(folder, "thumbnail.png");
  const subtitles = path.join(folder, "subtitles-ko.srt");
  const metadata = path.join(folder, "youtube.txt");
  const pack = path.join(outputDir, `${id}-upload-pack.zip`);
  const ready = await Promise.all(
    [video, thumbnail, subtitles, metadata, pack].map(exists),
  );
  const date = new Date(publicationStart);
  date.setDate(date.getDate() + (episode.number - 1) * 7);
  rows.push([
    id,
    episode.season,
    episode.title,
    episode.lesson,
    episode.premise,
    `달토끼 루니 시즌 ${episode.season} | ${episode.season_name}`,
    episode.number === 1 ? "5 min" : "3 min",
    ready.every(Boolean) ? "PRÊT" : "EN PRODUCTION",
    `${id}/${videoName}`,
    `${id}/thumbnail.png`,
    `${id}/subtitles-ko.srt`,
    `${id}/youtube.txt`,
    `${id}-upload-pack.zip`,
    date,
    "Non répertoriée",
    "Oui",
    "",
  ]);
}

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Tableau de bord");
const episodes = workbook.worksheets.add("100 épisodes");
const guide = workbook.worksheets.add("Mode d'emploi");
dashboard.showGridLines = false;
episodes.showGridLines = false;
guide.showGridLines = false;

dashboard.getRange("A1:H2").merge();
dashboard.getRange("A1").values = [["달토끼 루니 · Publication YouTube"]];
dashboard.getRange("A1:H2").format = {
  fill: "#6B5AA6",
  font: { bold: true, color: "#FFFFFF", size: 22 },
  verticalAlignment: "center",
  horizontalAlignment: "center",
};
dashboard.getRange("A4:B8").values = [
  ["INDICATEUR", "VALEUR"],
  ["Épisodes prévus", 100],
  ["Packs prêts", null],
  ["Encore en production", null],
  ["Langue de diffusion", "Coréen"],
];
dashboard.getRange("B6").formulas = [[`=COUNTIF('100 épisodes'!$H$2:$H$101,"PRÊT")`]];
dashboard.getRange("B7").formulas = [[`=COUNTIF('100 épisodes'!$H$2:$H$101,"EN PRODUCTION")`]];
dashboard.getRange("A4:B4").format = {
  fill: "#F3C969",
  font: { bold: true, color: "#443A70" },
};
dashboard.getRange("A5:B8").format.borders = {
  preset: "all",
  style: "thin",
  color: "#DDD7EE",
};
dashboard.getRange("A10:B14").values = [
  ["SAISON", "ÉPISODES"],
  ["Saison 1", 25],
  ["Saison 2", 25],
  ["Saison 3", 25],
  ["Saison 4", 25],
];
dashboard.getRange("A10:B10").format = {
  fill: "#A9D8D0",
  font: { bold: true, color: "#443A70" },
};
const seasonChart = dashboard.charts.add("doughnut", dashboard.getRange("A10:B14"));
seasonChart.title = "Répartition des 100 épisodes";
seasonChart.hasLegend = true;
seasonChart.setPosition("D4", "H16");
dashboard.getRange("A4:A14").format.columnWidth = 26;
dashboard.getRange("B4:B14").format.columnWidth = 22;

const headers = [
  "Épisode",
  "Saison",
  "Titre coréen",
  "Apprentissage",
  "Synopsis coréen",
  "Playlist YouTube",
  "Durée",
  "Statut",
  "Vidéo",
  "Miniature",
  "Sous-titres",
  "Métadonnées",
  "Pack ZIP",
  "Date conseillée",
  "Visibilité initiale",
  "Conçu pour les enfants",
  "Lien YouTube publié",
];
episodes.getRange("A1:Q1").values = [headers];
episodes.getRange("A2:Q101").values = rows;
episodes.getRange("A1:Q1").format = {
  fill: "#6B5AA6",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
  verticalAlignment: "center",
};
episodes.getRange("A1:Q101").format.borders = {
  preset: "all",
  style: "thin",
  color: "#E7E2F1",
};
episodes.getRange("A2:Q101").format.verticalAlignment = "top";
episodes.getRange("C2:F101").format.wrapText = true;
episodes.getRange("I2:Q101").format.wrapText = true;
episodes.getRange("N2:N101").format.numberFormat = "yyyy-mm-dd";
episodes.getRange("A1:Q101").conditionalFormats.add("containsText", {
  text: "PRÊT",
  format: { fill: "#D9F2E6", font: { bold: true, color: "#237A57" } },
});
episodes.getRange("A1:Q101").conditionalFormats.add("containsText", {
  text: "EN PRODUCTION",
  format: { fill: "#FFF0CC", font: { bold: true, color: "#8A6417" } },
});
episodes.freezePanes.freezeRows(1);
episodes.freezePanes.freezeColumns(2);
episodes.tables.add("A1:Q101", true, "EpisodesLuni").style = "TableStyleMedium4";
const widths = [12, 9, 28, 17, 50, 35, 10, 17, 24, 24, 25, 24, 29, 17, 20, 23, 34];
widths.forEach((width, index) => {
  episodes.getRangeByIndexes(0, index, 101, 1).format.columnWidth = width;
});
episodes.getRange("1:1").format.rowHeight = 34;
episodes.getRange("2:101").format.rowHeight = 45;

guide.getRange("A1:F2").merge();
guide.getRange("A1").values = [["Guide rapide de mise en ligne"]];
guide.getRange("A1:F2").format = {
  fill: "#6B5AA6",
  font: { bold: true, color: "#FFFFFF", size: 20 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
guide.getRange("A4:B11").values = [
  ["ÉTAPE", "ACTION"],
  ["1", "Ouvrir YouTube Studio puis Créer > Importer des vidéos."],
  ["2", "Choisir le fichier indiqué dans la colonne Vidéo."],
  ["3", "Copier le titre et la description depuis youtube.txt."],
  ["4", "Ajouter thumbnail.png comme miniature personnalisée."],
  ["5", "Ajouter subtitles-ko.srt dans Sous-titres > Coréen."],
  ["6", "Sélectionner Oui, cette vidéo est conçue pour les enfants."],
  ["7", "Choisir la playlist indiquée et publier d’abord en Non répertoriée."],
];
guide.getRange("A4:B4").format = {
  fill: "#F3C969",
  font: { bold: true, color: "#443A70" },
};
guide.getRange("A4:B11").format.borders = {
  preset: "all",
  style: "thin",
  color: "#DDD7EE",
};
guide.getRange("B5:B11").format.wrapText = true;
guide.getRange("A4:A11").format.columnWidth = 12;
guide.getRange("B4:B11").format.columnWidth = 78;
guide.getRange("5:11").format.rowHeight = 38;

await fs.mkdir(outputDir, { recursive: true });
const preview = await workbook.render({
  sheetName: "Tableau de bord",
  range: "A1:H17",
  scale: 1.5,
  format: "png",
});
await fs.writeFile(
  path.join(outputDir, "LUNI-YOUTUBE-PUBLICATION-preview.png"),
  new Uint8Array(await preview.arrayBuffer()),
);
const inspect = await workbook.inspect({
  kind: "table",
  range: "100 épisodes!A1:Q8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 17,
});
console.log(inspect.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "formula errors",
});
console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
