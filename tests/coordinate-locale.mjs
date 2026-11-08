// SPDX-License-Identifier: Apache-2.0
// The Python test passes an installed wheel resource, never the source module.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const { words, languageTag, pointFeedback } = await import(pathToFileURL(process.argv[2]));
const result = { status: "ok", feedback: "Distance from the origin: 5.00" };
assert.equal(pointFeedback(result, "en-GB"), "Distance from the origin: 5.00");
assert.equal(pointFeedback(result, "de-AT"), "Abstand vom Ursprung: 5,00");
assert.equal(pointFeedback({ ...result, feedback: "Distance from the origin: 1.41" }, "de"), "Abstand vom Ursprung: 1,41");
assert.equal(languageTag("DE-ch"), "de");
assert.equal(words("fr").send, "Send point");
assert.equal(words(undefined).send, "Send point");
assert.equal(pointFeedback({status:"queued"}, "de"), "Punkt empfangen. Warte auf den Präsentationsrechner…");
assert.equal(pointFeedback({status:"timeout"}, "de"), "Die Auswertung hat zu lange gedauert. Bitte versuche es erneut.");
// Neither an unfamiliar summary nor a failure status may be treated as success
// by parsing English text. Correctness still comes from the server on reveal.
assert.equal(pointFeedback({status:"error",feedback:result.feedback}, "de"), words("de").unavailable);
assert.equal(pointFeedback({status:"ok",feedback:"Unexpected engine text"}, "de"), words("de").checked);
assert.ok(words("de").inputPlane.includes("Tastatur"));
console.log("Coordinate language and feedback checks passed against the installed wheel.");
