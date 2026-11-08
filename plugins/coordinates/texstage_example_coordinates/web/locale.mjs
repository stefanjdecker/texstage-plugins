// SPDX-License-Identifier: Apache-2.0
export const languageTag = language => String(language || "en").toLowerCase().startsWith("de") ? "de" : "en";

const en = {
  choose: "Choose your point", x: "X coordinate", y: "Y coordinate", send: "Send point",
  sending: "Sending…", queued: "Point received. Waiting for the presenter’s computer…",
  hint: "Tap the plane or enter coordinates, then send your point.",
  checked: "Point checked.", correct: "Correct point!", reference: "Reference",
  distance: "Distance from the origin", reveal: "Reveal point", reset: "Reset responses",
  responses: "responses", controlReference: "reference",
  inputPlane: "Coordinate plane; use the X and Y fields below to enter a point with the keyboard.",
  classPlane: "Coordinate plane with the class responses.",
  syntax: "Enter two valid coordinates.", refused: "This point could not be evaluated.",
  unavailable: "Evaluation is unavailable. Please try again.",
  timeout: "Evaluation took too long. Please try again.",
  sendError: "The point could not be sent. Please try again.",
  controlError: "The action could not be completed. Please try again.",
};
const de = {
  choose: "Wähle deinen Punkt", x: "X-Koordinate", y: "Y-Koordinate", send: "Punkt senden",
  sending: "Wird gesendet…", queued: "Punkt empfangen. Warte auf den Präsentationsrechner…",
  hint: "Tippe auf die Ebene oder gib Koordinaten ein. Sende dann deinen Punkt.",
  checked: "Punkt geprüft.", correct: "Richtiger Punkt!", reference: "Lösungspunkt",
  distance: "Abstand vom Ursprung", reveal: "Punkt auflösen", reset: "Antworten zurücksetzen",
  responses: "Antworten", controlReference: "Lösungspunkt",
  inputPlane: "Koordinatenebene; nutze die Felder für X und Y darunter zur Eingabe mit der Tastatur.",
  classPlane: "Koordinatenebene mit den Antworten der Gruppe.",
  syntax: "Gib zwei gültige Koordinaten ein.", refused: "Dieser Punkt konnte nicht ausgewertet werden.",
  unavailable: "Die Auswertung ist nicht verfügbar. Bitte versuche es erneut.",
  timeout: "Die Auswertung hat zu lange gedauert. Bitte versuche es erneut.",
  sendError: "Der Punkt konnte nicht gesendet werden. Bitte versuche es erneut.",
  controlError: "Die Aktion konnte nicht abgeschlossen werden. Bitte versuche es erneut.",
};

export function words(language) { return languageTag(language) === "de" ? de : en; }

export function pointFeedback(point, language) {
  const t = words(language);
  if (point.status !== "ok") return t[point.status] || t.unavailable;
  // This revision-1 engine exposes a text summary. Translate its known display
  // format only; the structured status and server's coordinate check still
  // determine evaluation and correctness. Never interpret the summary as a grade.
  const distance = /^Distance from the origin: (\d+(?:\.\d+)?)$/.exec(point.feedback || "");
  return distance ? `${t.distance}: ${Number(distance[1]).toLocaleString(languageTag(language),
    { minimumFractionDigits: 2, maximumFractionDigits: 2, useGrouping: false })}` : t.checked;
}
