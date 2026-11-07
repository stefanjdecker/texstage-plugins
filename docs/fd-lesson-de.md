# Functional Dependencies Lab verwenden

Das experimentelle TeXStage-Plugin unterstützt Attributabschlüsse,
Kandidatenschlüssel und die Implikation funktionaler Abhängigkeiten (FDs).
Eine FD `X -> Y` bedeutet: Stimmen zwei Zeilen in allen Attributen von X überein,
stimmen sie auch in allen Attributen von Y überein. Die FDs sind vorgegebene
fachliche Regeln; Eindeutigkeit in einer Beispieltabelle beweist keine solche Regel.

Das [Beispiel](../examples/functional-dependencies/lesson.tex) verwendet
Workshop-Anmeldungen mit Person, E-Mail, Workshop, Tutor, Raum und Gebäude.
Version 0.4.0 enthält alle drei Unterrichtsmodi, eine englische und deutsche
Oberfläche sowie LaTeX-Ausgaben für Aufgaben und Lösungen.
[English guide](fd-lesson.md) · [Aktueller Kapazitätsbericht](design/functional-dependencies-600-validation.md).

## Installation und Start

Verwenden Sie eine neue Python-Umgebung (Python 3.12+) und das passende
experimentelle TeXStage-Wheel. Bestehende Kursumgebungen bleiben unverändert.
Version 0.4.0 benötigt `actor-slots-v1` aus dem passenden TeXStage-Branch
`codex/600-participant-capacity`. Der frühere veröffentlichte Host-Pin
`34d0c537135f32b0690147dbb66dd8ff155987f8` kann diesen Provider nicht laden.
Das [Release-Verfahren](fd-release.md) erklärt die Prüfung von Quellen und Artefakten.
Der lokal geprüfte Host-Commit ist `a67229a353b5b7bd3e058618ae71dfef619b0f81`;
seine Veröffentlichung und die gehosteten CI-Prüfungen stehen noch aus.
Nach einem Upgrade von 0.3.0 das Bundle neu bauen und eine neue Sitzung starten.
Die Entwicklungsversionsnummer allein identifiziert keinen kompatiblen Build. Für Quell-Builds installieren Sie zuerst
die mit Hashes fixierten Entwicklungsabhängigkeiten und das Wheel dieses Hosts.
Zusätzlich werden pdfLaTeX/latexmk, Beamer, Latin Modern sowie englische und
deutsche Babel-Unterstützung benötigt.

Im Stammverzeichnis von `texstage-plugins`, bei aktivierter Umgebung:

```sh
python maintenance/build_wheels.py --package fd-lab
python -m pip install --no-deps dist/texstage_fd_lab-0.4.0-py3-none-any.whl
texstage plugins --data ./fd-profile inspect io.github.stefanjdecker.fdlab
```

Prüfen Sie das Inventar und ersetzen Sie `<printed-payload>` durch den angezeigten
Digest. Installation und explizite Freigabe sind getrennte Schritte:

```sh
texstage plugins --data ./fd-profile enable io.github.stefanjdecker.fdlab --version 0.4.0 --payload <printed-payload>
texstage plugins --data ./fd-profile lock --output ./fd.lock.json
texstage present examples/functional-dependencies/lesson.tex --activities examples/functional-dependencies/lesson.activities.json --data ./fd-profile --plugins-lock ./fd.lock.json --no-tunnel
```

Weder Folien-Upload noch Style-Datei installieren oder aktivieren Code.
Nach einem Austausch von Host oder Plugin beginnen Sie eine neue Sitzung.
Die Telefone müssen den Präsentationsserver erreichen können. Lassen Sie den
Präsentationsbrowser geöffnet: Sein eingeschränkter Worker wertet Antworten aus.

## Gemeinsamer Unterrichtsablauf

1. Öffnen Sie die Aufgabe und wählen Sie **Antworten öffnen**. Studierende treten
   mit dem üblichen TeXStage-PIN oder Link bei. Änderungen werden erst mit
   **Antwort speichern** übermittelt. Native Schaltflächen sind auch per Tabulator,
   Eingabetaste und Leertaste bedienbar.
2. **Antwort privat ansehen** zeigt eine ausgewählte Antwort nur der Lehrperson.
   **Antworten schließen** verhindert neue Abgaben; bereits angenommene Auswertungen
   dürfen noch abschließen.
3. **Lösung auflösen** gibt die Musterlösung und das persönliche Feedback frei.
   Erst danach ist **Ausgewählte Antwort anonym teilen** möglich. Der Projektor
   erhält weder Teilnehmerliste noch Namen. Herleitungen können mit
   **Herleitung beginnen**, **Nächster Schritt** und **Vorheriger Schritt** gezeigt
   werden. Schlüssel und Gegenbeispiele werden als Ganzes angezeigt.
4. Erneutes Öffnen erlaubt Überarbeitungen und entfernt die geteilte Darstellung.
   **Aktivität zurücksetzen** löscht nach Bestätigung die Antworten und beginnt eine
   neue Epoche. Bereits bekannt gewordene Lösungen lassen sich dadurch nicht
   wieder geheim machen.

`feedback: "after-reveal"` hält persönliches Feedback bis zur Auflösung zurück.
`"practice"` zeigt es nach jeder Auswertung, hält aber die Musterlösung weiter zurück.
Ein Auswertungsfehler ist keine falsche mathematische Antwort. Ausstehende Antworten
bleiben gespeichert und warten auf den Präsentationsrechner.

Speichert ein zweites Gerät derselben Person eine andere Antwort, wählen Sie
**Gespeicherte Antwort laden** oder **Meinen Entwurf behalten**. Behalten sendet
nichts automatisch. Unabhängige Aktualisierungen erhalten Eingaben und Fokus;
beim Verlassen der Aufgabe bleiben nur gespeicherte Antworten erhalten.

## Attributabschluss

Beginnen Sie mit der vorgegebenen Startmenge. Fügen Sie FDs in der verwendeten
Reihenfolge hinzu und markieren Sie die endgültige Menge. Ein Schritt ist zulässig,
wenn die ganze linke Seite bekannt ist und mindestens ein neues Attribut hinzukommt.
Die erreichte und die ausgewählte Menge müssen dem vollständigen Abschluss
entsprechen. Unterschiedliche gültige Schrittfolgen werden akzeptiert.
Feedback benennt fehlende Voraussetzungen, unproduktive Schritte, unvollständige
Herleitungen oder eine falsche endgültige Menge.

## Ein oder alle Kandidatenschlüssel

Ein Superschlüssel bestimmt sämtliche Attribute. Ein Kandidatenschlüssel ist
zusätzlich inklusionsminimal: Kein Mitglied lässt sich einzeln entfernen, ohne
die Superschlüsseleigenschaft zu verlieren. „Minimal“ bedeutet nicht „kleinste
Anzahl an Attributen“.

Wählen Sie eine Menge unter **Vorgeschlagenen Schlüssel bilden**, dann
**Diesen Schlüssel verwenden** beziehungsweise **Schlüssel hinzufügen**.
Gespeichert wird die Liste hinzugefügter Schlüssel, nicht eine nur angeklickte
Auswahl. Im Ein-Schlüssel-Modus ersetzt eine neue Menge den bisherigen Vorschlag.
**Schlüssel entfernen** entfernt einen Listeneintrag. Ohne ausgewählte Attribute
steht die Menge ∅ zur Verfügung; fügen Sie sie ausdrücklich hinzu. Eine leere
Schlüsselliste ist etwas anderes als eine Liste mit dem leeren Schlüssel.

Im Workshop-Beispiel sind `{person, workshop}` und `{email, workshop}` die beiden
Kandidatenschlüssel. Für „einen“ genügt einer davon; für „alle“ werden beide benötigt.
Feedback unterscheidet Nicht-Superschlüssel, nichtminimale Superschlüssel und
fehlende Schlüssel. Als entfernbar angezeigte Mitglieder sind **einzeln** entfernbar,
nicht notwendigerweise alle zugleich. Weitere Beispiele zeigen unterschiedlich
große minimale Schlüssel und den leeren Schlüssel bei konstanten Attributen.

## Implikation und Gegenbeispiel

Wählen Sie **Folgt** und geben Sie FD-Schritte an, die von der linken Zielseite
aus alle rechten Zielattribute erreichen. Der vollständige Abschluss ist hier
nicht erforderlich. Eine triviale Ziel-FD kann eine leere Herleitung haben.

Wählen Sie **Folgt nicht**, um zwei symbolische Zeilen zu konstruieren. Markierte
Attribute sind in beiden Zeilen gleich; andere unterscheiden sich. Die Tabelle
zeigt für Zeile 1 Nullen und für Zeile 2 entsprechend Nullen oder Einsen. Sie ist
für schmale Bildschirme vertikal angeordnet. Die Symbole stehen nur für Gleichheit.
Das Paar muss alle gegebenen FDs erfüllen, in der gesamten linken Zielseite
übereinstimmen und sich in mindestens einem rechten Zielattribut unterscheiden.
Jedes gültige Gegenbeispiel wird akzeptiert. Feedback benennt eine verletzte
Voraussetzung oder erklärt, dass das Paar die Ziel-FD nicht verletzt.

## Eigene Aufgaben und LaTeX

Kopieren Sie das Beispiel einschließlich Sidecar und JSON-Quellen. Jeder
Sidecar-Eintrag nennt eine ID, den Typ `io.github.stefanjdecker.fdlab.exercise`
und einen Quellpfad relativ zum Hauptdokument. Quellen müssen innerhalb seines
Verzeichnisses bleiben. Das [Quellschema](../plugins/fd-lab/texstage_fd_lab/schemas/lesson-v1.json)
definiert `exercise`, `worked_answer`, zweisprachige Texte und die Feedback-Policy.

Die Aufgabenmodi sind `closure` mit `start`, `keys` mit `require: "one"` oder
`"all"`, und `implication` mit `lhs` und `rhs`. Musterantworten verwenden
Attributnamen und FD-IDs: Abschluss plus Schritte, eine Liste von Schlüsselmengen,
oder `implied: true` plus Schritte beziehungsweise `implied: false` plus `agree`.
Vollständige JSON-Beispiele liegen unter `examples/functional-dependencies/activities/`.

```tex
\usepackage{texstage}
\usepackage{texstage-fd-lab}
% Aufgaben-ID, Breite und Höhe innerhalb eines Frames:
\fdlab{closure}{.96\linewidth}{.78\textheight}
```

Die Vorbereitung prüft die Musterantwort unabhängig und erstellt öffentliche
Daten, private Referenzen sowie Aufgaben- und Lösungsfragmente aus derselben
Quelle. Eine falsche Musterlösung stoppt den Build. Klartext wird für LaTeX
maskiert und nicht als beliebiger TeX-Code ausgeführt. `language: "de"` im
Sidecar wählt deutsche statische Fragmente; Live-Texte folgen der Host-Sprache.
Verwenden Sie kurze, sinnvolle Attribut-IDs und von Ihren PDF-Schriften unterstützte
Zeichen. Prüfen Sie das Layout nach einer Vergrößerung von Aufgaben.

## Statische Ausgaben und Grenzen

`texstage build` erzeugt Live-Bundle und statische PowerPoint-Folien.
`texstage pdf ... --handout` erzeugt Aufgaben, `--solutions` die geprüften Lösungen.
`texstage prepare` nennt direkte pdfLaTeX-Einstiegspunkte. Übergeben Sie jeweils
die gleichen `--activities`- und `--data`-Argumente wie oben; vollständige Befehle
stehen in der englischen Anleitung. Nach Quelländerungen neu vorbereiten, statt
die Aktualitätsprüfung zu umgehen.

Vorbereitungsverzeichnisse und `keys.json` enthalten private Daten. Verteilen Sie
das gewünschte PDF oder lassen Sie TeXStage das Bundle mit seinen Zugriffskontrollen
ausliefern; veröffentlichen Sie nicht pauschal das gesamte Build-Verzeichnis.

Grenzen: 1–8 Attribute, 0–24 FDs, höchstens 8 produktive Schritte und 256
vorgeschlagene Schlüsselmengen. Pro Aufgabe werden bis zu 1.000 aktuelle Antworten
mit je 2 KiB reserviertem Speicher abgelegt; der gemeinsame Zustand hat ein
separates Limit von 160 KiB. **Vorherige Antworten** und **Weitere Antworten**
blättern durch jeweils 100 Antworten. Die Zähler berücksichtigen die ganze Klasse.
Die Speichergrenze ist keine Durchsatzgarantie. Der
[600-Teilnehmer-Bericht](design/functional-dependencies-600-validation.md)
dokumentiert Messwerte und offene Prüfschritte. Frühere F4/F5-Messungen bleiben
für ihre jeweiligen Artefakte gültig.

Verwenden Sie für weitere Prüfungen den oben genannten passenden Host mit den
Last- und Wiederverbindungsänderungen. Ohne Presenter-Auswertung bleiben
Antworten ausstehend. Nach einem erkannten Verbindungsabbruch kann ein neuer
Presenter die ausstehenden Prüfungen übernehmen; verspätete alte Ergebnisse
werden abgewiesen. Ein Dienstausfall gilt nie als fachlich falsche Antwort.
Physische Telefone, vollständige Barrierefreiheit und eine unveränderliche
öffentliche Veröffentlichung bleiben eigene Prüfschritte.
