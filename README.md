# Irrfahrt mit Neustart: der lokale Schnitt – Streamlit-Demo

Demo der Reihe „Irrfahrten auf Netzen: von der Trefferzeit bis zum lokalen Schnitt“ (Bereich Graphentheorie). **Mit Neustart liest man gleich viel. Aber welche Menge
herauskommt, entscheidet nicht der PageRank allein.** Eine **Irrfahrt mit Neustart** (personalisiertes PageRank) misst Nähe zu einem Startplatz; mit dem **Push-Verfahren**
und einem **Sweep** schneidet man daraus eine Menge um den Start. „Gleich viel“ gilt für **wachsende Zufallsgemeinschaften** (Gruppen zu 60, Außengrad 1) bei fester
Einstellung. Welche Menge herauskommt, hängt auch an der Division durch den Grad, der Regel am Sweep und den Parametern.

**Anschluss an die Reihe:** Läuft die Irrfahrt lange, hängt ihr Aufenthaltsort kaum noch vom Start ab und sagt wenig darüber, was nah am Start liegt (auf nicht
bipartiten Netzen oder in der trägen Fassung; auf den bipartiten Gitterhallen bleibt bei der nicht trägen Irrfahrt nur die Parität des Starts erhalten). Diese Demo lässt
sie in jedem Schritt mit einer Sprungwahrscheinlichkeit zum Start zurückspringen und schneidet aus der so entstehenden Gewichtung eine Menge um den Start. Die Demo
„Trefferzeit“ zeigt dieses Vergessen nicht (keine Mischzeit); dazu [Mischzeit exakt](https://sebastianhanisch-mischzeit-exakt-demo.streamlit.app/) und
[Meinungsbildung](https://sebastianhanisch-meinungsbildung-demo.streamlit.app/).

## Warum dieses Problem

Um die Gemeinschaft **eines** Platzes in einem großen Netz zu finden, möchte man nicht das ganze Netz durchrechnen. Die Demo [Spektrale Schnitte](https://sebastianhanisch-spektrale-schnitte-demo.streamlit.app/)
führt Fiedler-Vektor, Sweep und Konduktanz für die beste Zweiteilung des ganzen Netzes ein. Hier geht es von **global zu lokal**: Wie viel muss man lesen, welche Menge
kommt heraus, und wie gut sind einfachere Gegner, wenn man sie fair abstimmt?

## Modell

Einfaches, ungerichtetes, ungewichtetes Netz. In jedem Schritt springt die Irrfahrt mit der **Sprungwahrscheinlichkeit β** zum Start, sonst geht sie zu einem gleich
wahrscheinlich gewählten Nachbarn (nicht träge). In jedem Netz ist eine Menge **gepflanzt**; **F1** vergleicht die gefundene mit ihr, **Treffer** heißt F1 ≥ 0,9. Netze:

- **Handnetz „zwei Hallen“:** Dreiecke {0,1,2} und {3,4,5}, eine Tür 2–3. **Halle mit Sammelpunkt:** dazu Platz 6 mit Verbindungen zu 0, 1, 3, 4, 5. In beiden Netzen ist die Halle gepflanzt, in der der Start liegt (Start: Platz 0 bis 5); der Sammelpunkt 6 gehört zu keiner Halle und ist nicht als Start wählbar.
- **Hallenverbund z×z, Hallen a×a:** Gitter mit Vierernachbarschaft, benachbarte Hallen durch je eine Tür in der mittleren Zeile bzw. Spalte; gepflanzt ist die mittlere Halle. Die Hallen sind eine Kulisse; eine belegte Lagerweg-Anwendung gibt es nicht.
- **Zufallsgemeinschaften:** gleich große Gruppen; innerhalb einer Gruppe jede Verbindung mit Wahrscheinlichkeit 8/(g−1), dazu je Platz Poisson(Außengrad) Anschlüsse, zufällig gepaart (Paare innerhalb einer Gruppe entfallen). Gepflanzt ist die erste Gruppe; der Start liegt in der größten Zusammenhangskomponente. Zusammenhang wird nie durch Neuziehen erzwungen.
- **Mit Sammelpunkten:** Zufallsgemeinschaften (Gruppen zu 60, Außengrad 1) plus Plätze mit sehr vielen Verbindungen.

## Methodik

- **Push** (nicht träge): Solange r(u) ≥ ε·Grad(u): p(u) += β·r(u), der Rest (1−β)·r(u) gleich an die Nachbarn, r(u) = 0; Warteschlange ab dem Start (Teil der Definition). Die träge Fassung von Andersen, Chung und Lang rechnet mit α = β/(2−β) und hat dieselbe Zielgröße; `networkx.pagerank` nennt `alpha` = 1−β.
- **Exaktes PageRank** (für Karten und Anteile): konjugierte Gradienten für (D − (1−β)A)·y = β·e_s mit p = D·y.
- **Sweep:** Plätze nach p/Grad (Gleichstand: Nummer). Regel **„min“**: kleinste Konduktanz = Randkanten / min(Volumen S, Volumen Rest). Regel **„erstes Tal“** mit Schwelle γ: erstes laufendes Minimum ab 5 Plätzen, nach dem die Konduktanz um den Faktor 1+γ steigt, sonst „min“.
- **Gegner:** gierige Erweiterung (größter Anteil der Verbindungen in die Menge, Volumenbudget B) in drei Fassungen: Gleichstand „zuerst entdeckt“, **Nachbarschafts-Start** (Startmenge s samt Nachbarn, dann „zuerst entdeckt“), Gleichstand „kleinerer Grad, dann Nummer“; Breitensuche-Kugel mit Sweep; **Wärmeleitungs-Diffusion** in eigener abgeschnittener Fassung (Reihe bis Rest ≤ 10⁻³, je Schritt Einträge unter δ·Grad verworfen; **nicht** das Verfahren von Kloster und Gleich).
- **Kantenzugriffe:** Summe der Grade aller bearbeiteten Plätze, Wiederholungen mitgezählt. PageRank, Wärmeleitung und Breitensuche zählen Aufbau und Sweep; die gierige Erweiterung nur den Aufbau (die Konduktanz wird mitgeführt).
- **Abstimmung:** auf eigenen Netzen (Zufallsgemeinschaften mit 16 000 Plätzen, Gruppen 30 bis 480, je 8 Netze und Außengrad; Hallenverbund 6×6, Hallenseiten 6, 8, 12, 16, je 16 Startplätze). Raster: 13 Budgets je gieriger Fassung (300 bis 28 000), 8 Budgets Breitensuche, PageRank 6 β × 8 ε, Wärmeleitung 5 t × 5 δ, je 8 Sweep-Regeln. **Auswahlregel:** je Verfahren und Sweep-Familie höchstes mittleres F1 (Zellen gleich gewichtet); innerhalb 0,005 die sparsamste Einstellung. **★** = Haupteinstellung (die auf den Abstimm-Netzen bessere Sweep-Familie).
- **Test:** neue Zufalls-Seeds, Zufallsgemeinschaften Gruppen 20 bis 960 (20 und 960 außerhalb der Abstimmung), je 60 Netze und Außengrad; Hallenverbund 8×8, Hallenseiten 6 bis 20, **alle** Startplätze der mittleren Halle. Um eine innere Halle sind Abstimm- und Testverbund gleich aufgebaut: Für die abgestimmten Hallenseiten ist der Test keine unabhängige Prüfung.
- **Zufall:** SplitMix64 mit ganzzahligen Schwellen (`lsn_zufall.py`); die Netze hängen damit nicht an Gleitkomma-Funktionen der C-Bibliothek. Alle Messreihen: `tools/vorrechnen.py` → `daten/vorgerechnet.json`.
- Alle gierigen Regeln, der Nachbarschafts-Start und „erstes Tal“ entstanden **nach** Blick auf Ergebnisse früherer Probeläufe; die Zahlen hier stammen aus neuen Zufalls-Seeds.

## Befunde (gemessen, keine Behauptungen)

Die Tabellen kommen aus `daten/vorgerechnet.json`; `tests/test_claims.py` verlangt jede Tabellenzeile wörtlich und rechnet Stichproben aus dem Code nach.

### Von Hand

| Frage | Befund |
|---|---|
| Handnetz, β = 1/4, ab Platz 0 | PageRank (244/627, 130/627, 14/57, 5/57, 2/57, 2/57), davon 16/19 in der Starthalle {0,1,2}; Platz 2 hat mehr PageRank als Platz 1, geteilt durch den Grad weniger |
| Push mit ε = 1/20 | 8 Pushes (Plätze 0, 1, 2, 0, 1, 2, 0, 3), 19 Kantenzugriffe (Obergrenze 80); die Invariante p + ppr(r) = ppr(Start) gilt nach jedem Push; Sweep: Halle {0,1,2} mit Konduktanz 1/7 |
| Halle mit Sammelpunkt, β = 1/4 | nach p steht der Sammelpunkt auf Rang 2; Sweep nach p/Grad: {0,1,2} mit 1/3 (kleinste Konduktanz aller Mengen mit Platz 0), nach p: {0,1,2,6} mit 2/5 |
| Konduktanz im Hallenverbund (a = 8) | eine Halle 4/228, zwei Nachbarhallen 6/456, Block 2×2 8/912: größere Blöcke haben die kleinere Konduktanz |
| Gleichstand beim gierigen Verfahren (3×3 Hallen 6×6, Start (2,2) der mittleren Halle, Budget 400, erstes Tal 0,4) | „kleinerer Grad“: 54 Plätze, davon 18 aus der Starthalle; „zuerst entdeckt“: die Halle (36 von 36) |

### Anteil in der Starthalle gegen β

Hallenverbund 8×8, Hallen 8×8, alle 64 Startplätze der mittleren Halle, β = 0,5, 0,25, 0,1, 0,04, 0,015, 0,006, 0,003, 0,0015, 0,00075: Der Anteil des exakten PageRank in der
Starthalle fiel mit jedem kleineren β bei **64 von 64** Startplätzen, im Median von **99,7 % auf 13,4 %**. Kleineres β reicht auf diesem Netz also weiter; für andere Netze ist das nicht gemessen.

### Gleich viel gelesen

Zufallsgemeinschaften, Gruppen zu 60, Außengrad 1, je 40 Netze. Zellen: Kantenzugriffe im Median (Vielfaches von 2m) / Treffer von 40.

| Verfahren | 960 | 4 000 | 16 000 | 64 000 |
|---|---|---|---|---|
| Push (Vorführung) | 15 796 (1,843) / 36 | 11 557 (0,325) / 38 | 10 852 (0,076) / 40 | 11 014 (0,019) / 39 |
| Push träge (ACL) | 28 026 (3,270) / 40 | 23 416 (0,659) / 38 | 24 052 (0,167) / 40 | 23 399 (0,041) / 39 |
| PageRank abgestimmt | 575 924 (67,202) / 40 | 40 188 (1,130) / 38 | 31 944 (0,222) / 40 | 31 350 (0,054) / 39 |
| gierig abgestimmt | 5 004 (0,584) / 40 | 5 003 (0,141) / 39 | 5 004 (0,035) / 40 | 5 004 (0,009) / 40 |
| Wärmeleitung abgestimmt | 57 135 (6,667) / 38 | 46 882 (1,319) / 37 | 46 670 (0,325) / 40 | 46 867 (0,081) / 38 |

„Push (Vorführung)“ ist β = 0,006, ε = 0,0003, „min“; die träge Fassung mit denselben β, ε brauchte das 1,8- bis 2,2-Fache. Der F1-Median ist in jeder Zelle mindestens 0,99. **„Gleich viel“ gilt für wachsende Netze:** Bei 960 Plätzen liest der Push mehr als das ganze Netz, die abgestimmte Einstellung das 67-Fache. Ab 4 000 Plätzen lesen auch die gierige Erweiterung (durch ihr Budget) und die Wärmeleitung fast gleich viel; **das unterscheidet den PageRank nicht**. Die Obergrenze 1/(β·ε) = 555 556 hängt nicht von der Netzgröße ab (Satz).

Hallenverbund (Hallen 8×8, β = 0,006, ε = 0,001, „min“, je 20 Startplätze):

| Verbund | Plätze | Kantenzugriffe (Median) | Treffer |
|---|---|---|---|
| 4×4 | 1 024 | 24 148 | 20 von 20 |
| 8×8 | 4 096 | 24 086 | 20 von 20 |
| 16×16 | 16 384 | 24 211 | 19 von 20 |
| 32×32 | 65 536 | 24 143 | 18 von 20 |

### Durch den Grad teilen

96 Netze je Bauart (16 000 Plätze, Gruppen zu 60, Außengrad 1, β = 0,006). Zellen: F1-Median / F1-Mittel / Netze mit F1 < 0,8. „5 nahe“: je 12 Verbindungen in die Zielgruppe und 300 nach außen; ferne Sammelpunkte ohne Bezug zur Zielgruppe.

| Sammelpunkte | ε | Sweep-Regel | nach p/Grad | nach p |
|---|---|---|---|---|
| 5 nahe | 0,0001 | „min“ | 0,983 / 0,913 / 17 | 0,370 / 0,408 / 96 |
| 5 nahe | 0,0001 | „erstes Tal“ mit Schwelle 0,2 | 0,983 / 0,947 / 8 | 0,307 / 0,323 / 96 |
| 5 nahe | 0,0003 | „min“ | 0,983 / 0,957 / 5 | 0,952 / 0,900 / 14 |
| 5 nahe | 0,0003 | „erstes Tal“ mit Schwelle 0,2 | 0,983 / 0,960 / 4 | 0,296 / 0,404 / 80 |
| 5 nahe | 0,001 | „min“ | 0,950 / 0,927 / 3 | 0,942 / 0,921 / 3 |
| 5 nahe | 0,001 | „erstes Tal“ mit Schwelle 0,2 | 0,950 / 0,927 / 3 | 0,942 / 0,921 / 3 |
| 40 ferne (je 400) | 0,0003 | „min“ | 0,983 / 0,975 / 0 | 0,975 / 0,952 / 4 |
| 40 ferne (je 400) | 0,0003 | „erstes Tal“ mit Schwelle 0,2 | 0,983 / 0,975 / 0 | 0,967 / 0,784 / 24 |
| 200 ferne (je 100) | 0,0003 | „erstes Tal“ mit Schwelle 0,05 | 0,975 / 0,886 / 14 | 0,322 / 0,463 / 69 |
| 200 ferne (je 100) | 0,0003 | „erstes Tal“ mit Schwelle 0,2 | 0,976 / 0,956 / 4 | 0,936 / 0,768 / 29 |
| 200 ferne (je 100) | 0,001 | „erstes Tal“ mit Schwelle 0,05 | 0,933 / 0,774 / 34 | 0,322 / 0,528 / 60 |
| keine | 0,0003 | „min“ | 0,992 / 0,986 / 1 | 0,984 / 0,979 / 1 |
| keine | 0,0003 | „erstes Tal“ mit Schwelle 0,05 | 0,984 / 0,858 / 16 | 0,983 / 0,888 / 17 |

Über alle drei Bauarten mit Sammelpunkten, drei ε und vier Regeln (36 Kombinationen) liegt der Median nach p/Grad in **13** um mehr als 0,05 höher als nach p, in **0** um mehr als 0,05 niedriger. **Wie stark es schadet, hängt an Sweep-Regel und ε:** Bei den fünf nahen Sammelpunkten und ε = 0,001 verschwindet der Unterschied (höchstens 0,008 in allen vier Regeln), bei 200 fernen und „erstem Tal“ 0,05 bleibt er auch dort groß. Die Regel „erstes Tal“ mit Schwelle 0,05 kostet auch ohne Sammelpunkte Mittelwert (letzte Zeile).

### Welche Größe findet man?

**Dieselbe PageRank-Rechnung (β = 0,006), nur Regel oder ε geändert.** Zellen: F1-Median / Treffer / Median der Plätze im Schnitt; rechts die Kantenzugriffe im Median. Hallen: alle Startplätze der mittleren Halle; Zufallsgemeinschaften: 60 neue Netze mit 16 000 Plätzen.

| Fall | ε | „min“ | „erstes Tal“ 0,2 | „erstes Tal“ 0,4 | Kantenzugriffe |
|---|---|---|---|---|---|
| Hallenverbund 8×8, Hallen 8×8 (64 Starts) | 0,001 | 0,99 / 60 / 65 | 0,97 / 38 / 64 | 0,99 / 60 / 65 | 24 087 |
| Hallenverbund 8×8, Hallen 8×8 (64 Starts) | 0,0003 | 0,39 / 27 / 264 | 0,96 / 38 / 62 | 0,99 / 60 / 65 | 93 662 |
| Hallenverbund 8×8, Hallen 8×8 (64 Starts) | 0,0001 | 0,19 / 10 / 602 | 0,97 / 38 / 63 | 0,99 / 60 / 65 | 250 559 |
| Hallenverbund 8×8, Hallen 16×16 (256 Starts) | 0,001 | 0,79 / 24 / 206 | 0,77 / 19 / 192 | 0,79 / 24 / 206 | 24 952 |
| Hallenverbund 8×8, Hallen 16×16 (256 Starts) | 0,0003 | 0,97 / 236 / 273 | 0,96 / 172 / 263 | 0,97 / 236 / 273 | 107 503 |
| Hallenverbund 8×8, Hallen 16×16 (256 Starts) | 0,0001 | 0,98 / 224 / 267 | 0,96 / 160 / 260 | 0,98 / 224 / 267 | 240 334 |
| Zufallsgemeinschaften, Außengrad 3, Gruppen zu 120 (60 Netze) | 0,001 | 0,39 / 0 / 42 | 0,39 / 0 / 42 | 0,39 / 0 / 42 | 1 229 |
| Zufallsgemeinschaften, Außengrad 3, Gruppen zu 120 (60 Netze) | 0,0003 | 0,79 / 8 / 152 | 0,79 / 8 / 152 | 0,79 / 8 / 152 | 5 401 |
| Zufallsgemeinschaften, Außengrad 3, Gruppen zu 120 (60 Netze) | 0,0001 | 0,83 / 13 / 142 | 0,83 / 13 / 142 | 0,83 / 13 / 142 | 16 897 |
| Zufallsgemeinschaften, Außengrad 3, Gruppen zu 480 (60 Netze) | 0,001 | 0,07 / 0 / 25 | 0,07 / 0 / 25 | 0,07 / 0 / 25 | 701 |
| Zufallsgemeinschaften, Außengrad 3, Gruppen zu 480 (60 Netze) | 0,0003 | 0,16 / 0 / 86 | 0,16 / 0 / 86 | 0,16 / 0 / 86 | 3 424 |
| Zufallsgemeinschaften, Außengrad 3, Gruppen zu 480 (60 Netze) | 0,0001 | 0,66 / 0 / 525 | 0,66 / 0 / 525 | 0,66 / 0 / 525 | 15 039 |

Auf den Hallen 8×8 entscheidet bei ε = 0,0003 die Regel („min“ findet im Median 264 Plätze, „erstes Tal 0,4“ 65; die Halle hat 64). Auf den Zufallsgemeinschaften mit Außengrad 3 ändert die Regel in diesen Fällen den Median nicht; dort bewegt ε allein den Median (bei Gruppen zu 480 von 0,07 über 0,16 auf 0,66).

**Bezug: globaler Fiedler-Sweep** (sucht die beste Zweiteilung des ganzen Netzes, eine andere Frage). Auf dem Hallenverbund 8×8 (Hallen 8×8) hat die gefundene Menge zur Starthalle F1 = 0,00; der zweite und dritte Eigenwert liegen nur 2,5·10⁻⁶ auseinander, der Vektor ist schlecht bestimmt (deshalb nennen wir keine Größe der Menge). Auf 20 Zufallsgemeinschaften (16 000 Plätze, Gruppen zu 60, Außengrad 1) lag F1 zur Startgruppe in 19 Netzen unter 0,01, höchstens bei 0,67; keines war ein Treffer.

### Die Gegner

**Gewählte Einstellungen** (Abstimm-Wert = mittleres F1 auf den Abstimm-Netzen; „Rand“: gewählter Wert am Ende seines Rasters):

| Netzfamilie | Verfahren | Einstellung | Abstimm-Wert | Rand |
|---|---|---|---|---|
| Zufallsgemeinschaften, Außengrad 1 | gierig „zuerst entdeckt“ | B = 3 300, „min“ | 0,833 | – |
| Zufallsgemeinschaften, Außengrad 1 | gierig „zuerst entdeckt“ ★ | B = 5 000, „erstes Tal“ mit Schwelle 0,05 | 0,872 | – |
| Zufallsgemeinschaften, Außengrad 1 | gierig Nachbarschafts-Start | B = 3 300, „min“ | 0,807 | – |
| Zufallsgemeinschaften, Außengrad 1 | gierig Nachbarschafts-Start ★ | B = 5 000, „erstes Tal“ mit Schwelle 0,1 | 0,989 | – |
| Zufallsgemeinschaften, Außengrad 1 | gierig „kleinerer Grad“ | B = 10 000, „min“ | 0,837 | – |
| Zufallsgemeinschaften, Außengrad 1 | gierig „kleinerer Grad“ ★ | B = 5 000, „erstes Tal“ mit Schwelle 0,02 | 0,874 | – |
| Zufallsgemeinschaften, Außengrad 1 | PageRank | β = 0,015, ε = 0,0001, „min“ | 0,971 | – |
| Zufallsgemeinschaften, Außengrad 1 | PageRank ★ | β = 0,006, ε = 0,0001, „erstes Tal“ mit Schwelle 0,2 | 0,981 | – |
| Zufallsgemeinschaften, Außengrad 1 | Wärmeleitung | t = 10, δ = 0,00003, „min“ | 0,988 | – |
| Zufallsgemeinschaften, Außengrad 1 | Wärmeleitung ★ | t = 10, δ = 0,00003, „erstes Tal“ mit Schwelle 0,1 | 0,996 | – |
| Zufallsgemeinschaften, Außengrad 1 | Breitensuche | B = 10 000, „min“ | 0,801 | – |
| Zufallsgemeinschaften, Außengrad 1 | Breitensuche ★ | B = 10 000, „erstes Tal“ mit Schwelle 0,2 | 0,828 | – |
| Zufallsgemeinschaften, Außengrad 3 | gierig „zuerst entdeckt“ | B = 5 000, „min“ | 0,618 | – |
| Zufallsgemeinschaften, Außengrad 3 | gierig „zuerst entdeckt“ ★ | B = 5 000, „erstes Tal“ mit Schwelle 0,2 | 0,629 | – |
| Zufallsgemeinschaften, Außengrad 3 | gierig Nachbarschafts-Start | B = 3 300, „min“ | 0,834 | – |
| Zufallsgemeinschaften, Außengrad 3 | gierig Nachbarschafts-Start ★ | B = 6 500, „erstes Tal“ mit Schwelle 0,1 | 0,968 | – |
| Zufallsgemeinschaften, Außengrad 3 | gierig „kleinerer Grad“ | B = 5 000, „min“ | 0,681 | – |
| Zufallsgemeinschaften, Außengrad 3 | gierig „kleinerer Grad“ ★ | B = 5 000, „erstes Tal“ mit Schwelle 0,2 | 0,708 | – |
| Zufallsgemeinschaften, Außengrad 3 | PageRank | β = 0,006, ε = 0,00003, „min“ | 0,857 | – |
| Zufallsgemeinschaften, Außengrad 3 | PageRank ★ | β = 0,015, ε = 0,00003, „erstes Tal“ mit Schwelle 0,1 | 0,860 | – |
| Zufallsgemeinschaften, Außengrad 3 | Wärmeleitung | t = 40, δ = 0,00001, „min“ | 0,983 | delta |
| Zufallsgemeinschaften, Außengrad 3 | Wärmeleitung ★ | t = 20, δ = 0,00001, „erstes Tal“ mit Schwelle 0,2 | 0,991 | delta |
| Zufallsgemeinschaften, Außengrad 3 | Breitensuche ★ | B = 5 000, „min“ | 0,658 | – |
| Zufallsgemeinschaften, Außengrad 3 | Breitensuche | B = 5 000, „erstes Tal“ mit Schwelle 0,2 | 0,658 | – |
| Hallenverbund | gierig „zuerst entdeckt“ | B = 450, „min“ | 0,841 | – |
| Hallenverbund | gierig „zuerst entdeckt“ ★ | B = 1 500, „erstes Tal“ mit Schwelle 0,8 | 0,938 | – |
| Hallenverbund | gierig Nachbarschafts-Start | B = 450, „min“ | 0,810 | – |
| Hallenverbund | gierig Nachbarschafts-Start ★ | B = 1 500, „erstes Tal“ mit Schwelle 0,8 | 0,904 | – |
| Hallenverbund | gierig „kleinerer Grad“ | B = 300, „min“ | 0,520 | B |
| Hallenverbund | gierig „kleinerer Grad“ ★ | B = 1 000, „erstes Tal“ mit Schwelle 0,2 | 0,729 | – |
| Hallenverbund | PageRank | β = 0,006, ε = 0,001, „min“ | 0,899 | eps |
| Hallenverbund | PageRank ★ | β = 0,0015, ε = 0,0005, „erstes Tal“ mit Schwelle 0,4 | 0,995 | – |
| Hallenverbund | Wärmeleitung | t = 40, δ = 0,0001, „min“ | 0,903 | – |
| Hallenverbund | Wärmeleitung ★ | t = 80, δ = 0,00003, „erstes Tal“ mit Schwelle 0,8 | 0,966 | t |
| Hallenverbund | Breitensuche | B = 600, „min“ | 0,632 | – |
| Hallenverbund | Breitensuche ★ | B = 600, „erstes Tal“ mit Schwelle 0,4 | 0,664 | – |

**Test, Zufallsgemeinschaften, Außengrad 1** (je 60 neue Netze mit 16 000 Plätzen; Zellen: F1-Median / F1-Mittel / Treffer; Spalten = Gruppengröße; 20 und 960 außerhalb der Abstimmung; 2m im Median je Zelle 137 349 bis 143 930):

| Verfahren | 20 | 30 | 60 | 120 | 240 | 480 | 960 | Kantenzugriffe (Median je Zelle) |
|---|---|---|---|---|---|---|---|---|
| gierig „zuerst entdeckt“ ★ | 1,00 / 0,94 / 56 | 1,00 / 0,96 / 58 | 1,00 / 0,83 / 50 | 1,00 / 0,87 / 52 | 0,99 / 0,77 / 46 | 0,99 / 0,80 / 48 | 0,73 / 0,61 / 0 | 5 003 bis 5 005 |
| gierig Nachbarschafts-Start ★ | 0,98 / 0,93 / 51 | 0,98 / 0,98 / 59 | 0,99 / 0,99 / 60 | 1,00 / 0,99 / 60 | 0,99 / 0,99 / 60 | 0,99 / 0,98 / 59 | 0,73 / 0,71 / 0 | 5 003 bis 5 006 |
| gierig „kleinerer Grad“ ★ | 1,00 / 0,94 / 56 | 1,00 / 0,97 / 58 | 1,00 / 0,87 / 52 | 1,00 / 0,88 / 53 | 0,99 / 0,77 / 46 | 0,99 / 0,74 / 44 | 0,73 / 0,55 / 0 | 5 003 bis 5 004 |
| PageRank ★ | 1,00 / 1,00 / 60 | 1,00 / 0,99 / 59 | 0,99 / 0,99 / 60 | 0,99 / 0,98 / 60 | 0,98 / 0,97 / 60 | 0,97 / 0,97 / 59 | 0,92 / 0,88 / 36 | 32 318 bis 56 008 |
| PageRank („min“) | 1,00 / 0,90 / 51 | 1,00 / 0,98 / 57 | 0,99 / 0,98 / 59 | 0,99 / 0,96 / 57 | 0,98 / 0,97 / 59 | 0,97 / 0,97 / 59 | 0,91 / 0,85 / 32 | 28 047 bis 46 403 |
| Wärmeleitung ★ | 1,00 / 1,00 / 60 | 1,00 / 1,00 / 60 | 1,00 / 0,95 / 56 | 1,00 / 1,00 / 60 | 1,00 / 0,98 / 59 | 1,00 / 0,98 / 59 | 0,98 / 0,95 / 48 | 41 677 bis 109 504 |
| Breitensuche ★ | 0,95 / 0,95 / 57 | 0,93 / 0,89 / 38 | 0,84 / 0,81 / 15 | 0,86 / 0,82 / 14 | 0,80 / 0,78 / 6 | 0,78 / 0,78 / 1 | 0,67 / 0,68 / 0 | 20 008 bis 20 010 |

**Test, Zufallsgemeinschaften, Außengrad 3** (2m im Median je Zelle 165 942 bis 175 960):

| Verfahren | 20 | 30 | 60 | 120 | 240 | 480 | 960 | Kantenzugriffe (Median je Zelle) |
|---|---|---|---|---|---|---|---|---|
| gierig „zuerst entdeckt“ ★ | 1,00 / 0,85 / 50 | 1,00 / 0,87 / 52 | 0,99 / 0,79 / 47 | 0,99 / 0,77 / 46 | 0,98 / 0,61 / 36 | 0,91 / 0,53 / 32 | 0,55 / 0,34 / 0 | 5 004 bis 5 006 |
| gierig Nachbarschafts-Start ★ | 0,75 / 0,76 / 24 | 0,95 / 0,91 / 52 | 0,98 / 0,98 / 60 | 0,98 / 0,97 / 59 | 0,99 / 0,97 / 59 | 0,98 / 0,93 / 57 | 0,75 / 0,69 / 0 | 6 503 bis 6 506 |
| gierig „kleinerer Grad“ ★ | 1,00 / 0,83 / 49 | 1,00 / 0,84 / 50 | 0,99 / 0,79 / 47 | 0,99 / 0,75 / 45 | 0,98 / 0,65 / 38 | 0,93 / 0,60 / 36 | 0,60 / 0,36 / 0 | 5 004 bis 5 006 |
| PageRank ★ | 0,94 / 0,92 / 46 | 0,95 / 0,95 / 53 | 0,93 / 0,90 / 39 | 0,85 / 0,83 / 15 | 0,85 / 0,84 / 5 | 0,81 / 0,78 / 1 | 0,68 / 0,67 / 0 | 53 240 bis 73 300 |
| PageRank („min“) | 0,93 / 0,87 / 44 | 0,95 / 0,93 / 53 | 0,93 / 0,89 / 40 | 0,87 / 0,83 / 16 | 0,85 / 0,84 / 8 | 0,82 / 0,79 / 1 | 0,69 / 0,68 / 0 | 56 657 bis 80 734 |
| Wärmeleitung ★ | 1,00 / 0,97 / 56 | 1,00 / 0,98 / 58 | 1,00 / 0,99 / 59 | 1,00 / 0,99 / 60 | 0,99 / 0,98 / 59 | 0,98 / 0,98 / 60 | 0,93 / 0,84 / 39 | 169 296 bis 220 406 |
| Breitensuche ★ | 0,90 / 0,88 / 32 | 0,83 / 0,77 / 15 | 0,69 / 0,69 / 0 | 0,73 / 0,72 / 0 | 0,65 / 0,63 / 0 | 0,46 / 0,46 / 0 | 0,28 / 0,27 / 0 | 10 009 bis 10 012 |

Der Erfolg der gierigen Erweiterung ist je Netz oft zweigipflig: Mit „zuerst entdeckt“ liegt der Median in jeder Zelle der Gruppen 30 bis 480 bei mindestens 0,91, während je Zelle 2 bis 28 von 60 Netzen unter F1 0,9 bleiben.

**Test, Hallenverbund 8×8** (alle Startplätze der mittleren Halle, also 36 bis 400 je Zelle; Spalten = Hallenseite a; a = 10 und 20 nicht abgestimmt; 2m: 7 904 bei a = 6 bis 97 504 bei a = 20):

| Verfahren | 6 | 8 | 10 | 12 | 16 | 20 | Kantenzugriffe (Median je Zelle) |
|---|---|---|---|---|---|---|---|
| gierig „zuerst entdeckt“ ★ | 1,00 / 0,94 / 30 | 1,00 / 0,95 / 54 | 1,00 / 0,96 / 89 | 1,00 / 0,95 / 121 | 1,00 / 0,97 / 213 | 0,99 / 0,92 / 329 | 1 500 bis 1 503 |
| gierig Nachbarschafts-Start ★ | 1,00 / 0,90 / 25 | 1,00 / 0,91 / 46 | 1,00 / 0,90 / 70 | 1,00 / 0,90 / 101 | 1,00 / 0,95 / 193 | 0,99 / 0,90 / 309 | 1 500 bis 1 503 |
| gierig „kleinerer Grad“ ★ | 0,67 / 0,75 / 9 | 0,67 / 0,75 / 16 | 0,67 / 0,75 / 25 | 0,67 / 0,75 / 36 | 0,67 / 0,75 / 64 | 0,67 / 0,70 / 0 | 1 001 bis 1 003 |
| PageRank ★ | 1,00 / 0,97 / 32 | 1,00 / 0,98 / 60 | 1,00 / 0,98 / 96 | 1,00 / 0,99 / 140 | 1,00 / 0,99 / 252 | 0,95 / 0,95 / 365 | 138 252 bis 181 395 |
| PageRank („min“) | 0,99 / 0,77 / 23 | 0,99 / 0,97 / 60 | 0,99 / 0,98 / 96 | 0,97 / 0,96 / 132 | 0,79 / 0,79 / 24 | 0,62 / 0,62 / 0 | 23 906 bis 28 282 |
| Wärmeleitung ★ | 1,00 / 1,00 / 36 | 1,00 / 0,99 / 63 | 1,00 / 0,99 / 96 | 0,99 / 0,97 / 132 | 0,86 / 0,88 / 94 | 0,85 / 0,86 / 96 | 56 430 bis 72 169 |
| Breitensuche ★ | 0,57 / 0,60 / 1 | 0,61 / 0,64 / 3 | 0,70 / 0,71 / 1 | 0,71 / 0,71 / 1 | 0,59 / 0,59 / 0 | 0,48 / 0,47 / 0 | 1 202 bis 1 202 |

### Zählung über die 14 Zellen innerhalb der Abstimmbereiche

Zellen: Gruppen 30 bis 480 je Außengrad (10) und Hallenseiten 6, 8, 12, 16 (4). Je Netzfamilie die auf den Abstimm-Netzen beste gierige Einstellung (Zufallsgemeinschaften: Nachbarschafts-Start; Hallen: „zuerst entdeckt“) gegen den abgestimmten PageRank-Schnitt.

| Gegen | sparsamer | Faktor der Zugriffe | Median (zwei Stellen) mindestens so gut | Treffer mindestens so viele | Mittel um > 0,02 vorn / zurück |
|---|---|---|---|---|---|
| PageRank „erstes Tal“ | 14 von 14 | 6,5 bis 121 | 13 von 14 | 9 von 14 (Gemeinschaften 9 von 10, Hallen 0 von 4) | 5 / 5 |
| PageRank „min“ | 14 von 14 | 5,6 bis 19 | 13 von 14 | 11 von 14 (Gemeinschaften 9 von 10, Hallen 2 von 4) | 8 / 1 |

- Die gierige Erweiterung mit passender Start- und Abschneideregel brauchte in allen 14 Zellen weniger als ein Fünftel der Kantenzugriffe beider PageRank-Einstellungen. Wer zuverlässiger war, hängt an der Netzfamilie: auf den Zufallsgemeinschaften meist mindestens so viele Treffer wie PageRank (9 von 10), auf den Hallen hatte PageRank („erstes Tal“) in 4 von 4 Zellen mehr Treffer und las dabei das 2,9- bis 17,5-Fache der Summe aller Grade.
- **Wärmeleitung** (Haupteinstellung) auf den 10 Zellen der Zufallsgemeinschaften (600 Netze), Treffer zusammen: Wärmeleitung 590, gierig 585, PageRank 411. Gegen die gierige Erweiterung hatte die Wärmeleitung in 4 Zellen mehr und in 3 weniger Treffer; gegen PageRank in 8 von 10 Zellen mindestens so viele. In 9 von 10 Zellen las sie von den dreien am meisten, bei Außengrad 3 das 0,96- bis 1,33-Fache der Summe aller Grade (über alle sieben Gruppengrößen).
- **Der ehrliche Befund gegen den PageRank:** Seine zwei abgestimmten Einstellungen („erstes Tal“ und „min“) waren in **keiner** der 14 Zellen das sparsamste Verfahren, verglichen nach den Kantenzugriffen im Median mit den abgestimmten Einstellungen aller Verfahren, ohne Blick auf die Treffer. Das ist eine Aussage über diese zwei Einstellungen, nicht über die feste Push-Einstellung aus der Reihe gegen die Netzgröße (β = 0,006, ε = 0,0003, „min“), für die das „gleich viel“ gemessen ist. Auf den Hallen (a = 6 bis 20) ist die zuverlässige PageRank-Einstellung **nicht lokal** (1,8- bis 17,5-fache Summe aller Grade); die sparsame mit „min“ liest das 0,25- bis 3,02-Fache, hat aber bei a = 6 (23 von 36), a = 16 (24 von 256) und a = 20 (0 von 400) wenige Treffer. Und die Gütezusage ist in dieser Größe leer.
- **Außerhalb der Abstimmbereiche** (Treffer von 60) ist das Bild gemischt: Gruppen zu 960, Außengrad 1: gierig 0, PageRank („erstes Tal“) 36, Wärmeleitung 48; Außengrad 3: 0, 0 und 39. Gruppen zu 20, Außengrad 3: gierig 24, PageRank 46.

### Gütezusage von Andersen, Chung und Lang

Voraussetzungen (Satz 5 der Langfassung): Φ(C) ≤ α/10, vol(C) ≤ ⅔·2m, Start in einer Teilmenge von C mit mindestens halbem Volumen, ε ≤ 1/(10·vol(C)). Der Beweis liefert Φ(Sweep) < √(90·α·ln(30·√vol C)) (die Fassung nennt keine Basis; hier natürlich). Für die Starthalle 8×8 (Φ = 4/228, Volumen 228, α = 10Φ) ergibt das rund **9,8**; die Konduktanz ist nie größer als 1: **die Zusage ist hier leer.** Auf dem Handnetz ist die Voraussetzung unerfüllbar (die kleinste Konduktanz einer Menge mit höchstens zwei Dritteln des Volumens ist 1/7 > 1/10).

## Befunde und Korrekturen

- **Gleichstände sind beim gierigen Verfahren entscheidend:** Allein die Gleichstandsregel macht im Gitter aus der Halle (36 von 36) eine falsche Menge (54 Plätze, 18 aus der Halle).
- **Netzgröße am Reglerrand:** Gruppen zu 960 bei 960 Plätzen ergäben nur eine Gruppe; die Demo nimmt dann zwei Gruppen und sagt es.
- **Wärmeleitung gegen gierig:** Auf den Zufallsgemeinschaften war die Wärmeleitung nur in der Treffersumme vorn (590 gegen 585), nicht in jeder Zelle. Deshalb nennt die Demo kein „zuverlässigstes“ Verfahren, sondern Zählungen.
- **Gradfalle:** Dass der Unterschied bei ε = 0,001 verschwindet, gilt für die fünf nahen Sammelpunkte, nicht für 200 ferne mit „erstem Tal“ 0,05.

## Ehrliche Grenzen

**Annahmen.**
- Einfaches, ungerichtetes, ungewichtetes Netz. Die Irrfahrt springt in jedem Schritt mit Wahrscheinlichkeit β zum Start zurück, sonst geht sie zu einem gleich wahrscheinlich gewählten Nachbarn (nicht träge).
- Der Push arbeitet eine Warteschlange ab (Anfang: Start). Die Reihenfolge gehört zur Definition; deshalb hängen die Push-Werte an der Nummerierung der Plätze.
- Sweep-Ordnung nach Wert geteilt durch Grad, bei Gleichstand nach Nummer. Treffer heißt F1 ≥ 0,9 gegen die gepflanzte Menge.
- Kantenzugriffe: Summe der Grade aller bearbeiteten Plätze. PageRank, Wärmeleitung und Breitensuche zählen Aufbau und Sweep, die gierige Erweiterung nur den Aufbau (sie führt die Konduktanz mit). Auch doppelt gezählt läge sie in den 14 Zellen unter dem PageRank-Schnitt. Warteschlangen- und Heap-Arbeit zählt nicht.

**Grenzen.**
- Alle Zahlen gelten für die synthetischen Netze der Demo (Gitterhallen und Zufallsgemeinschaften) und die genannten Einstellungen. Netze mit Ortsbezug, echte, gewichtete oder gerichtete Netze sind nicht gemessen.
- F1 misst nur gegen die gepflanzte Menge. Eine andere Menge kann nach der Konduktanz besser sein als die gepflanzte (im Hallenverbund mit a = 8 ist die Konduktanz zweier Nachbarhallen und eines Blocks 2×2 kleiner als die einer Halle), sie kann aber auch schlechter sein; beim Schnitt oben stehen deshalb auch Größe und Konduktanz.
- Die gierigen Regeln, der Nachbarschafts-Start und das „erste Tal“ entstanden nach Blick auf Ergebnisse; hier sind sie auf neuen Zufalls-Seeds gemessen, aber nicht auf neuen Netzarten.
- Für die abgestimmten Hallenseiten ist der Test auf den Hallen keine unabhängige Prüfung (um eine innere Halle sind Abstimm- und Testverbund gleich aufgebaut).
- Einige gewählte Einstellungen liegen am Rand ihres Rasters (Wärmeleitung bei Außengrad 3: kleinstes δ; auf den Hallen mit „erstem Tal“: größtes t; PageRank mit „min“ auf den Hallen: größtes ε; gierig „kleinerer Grad“ mit „min“ auf den Hallen: kleinstes B). Andere Rasterwerte könnten das Bild verschieben, vor allem die Zugriffe.
- Nicht gemessen: gierige Erweiterung mit Entfernen von Plätzen, Fluss-Verfahren, Nibble, Louvain oder Leiden von einem Start, hk-relax.

**Bekannte Probleme und Unsicherheiten.**
- Der Erfolg ist je Netz oft zweigipflig (fast ganz richtig oder weit daneben): Ein einzelnes Netz sagt wenig über ein Verfahren.
- Die Wärmeleitung ist eine eigene abgeschnittene Fassung, nicht das Verfahren von Kloster und Gleich.
- Bei sehr kleinem β und ε liest der Push auf den großen Hallennetzen mehrere Millionen Kantenzugriffe; dann dauert ein Lauf einige Sekunden.
- Nicht alle Quellen sind im Original gelesen (siehe „Mathematische Formulierung“).

**Weitere Abgrenzung:** Die Demo „Überdeckungszeit“ benutzt einen festen Rücksprung alle τ Schritte (der Sprung zählt nicht als Schritt); diese Demo benutzt einen zufälligen Neustart. Es sind zwei verschiedene Verfahren; Ergebnisse des einen gelten für den anderen nicht ohne eigene Messung. Gerichtetes PageRank rechnet die Demo nicht ([Zentralität](https://sebastianhanisch-centrality-demo.streamlit.app/), [interne Verlinkung](https://sebastianhanisch-interne-verlinkung-demo.streamlit.app/)); eine Link-Vorhersage ist kein Experiment ([Link-Vorhersage](https://sebastianhanisch-link-prediction-demo.streamlit.app/)); Gemeinschaften für das ganze Netz zeigen [Leiden](https://sebastianhanisch-leiden-demo.streamlit.app/) und das [stochastische Blockmodell](https://sebastianhanisch-stochastic-block-demo.streamlit.app/). Empfehlungen mit Irrfahrten mit Neustart sind für den Betrieb beschrieben (Twitter: Gupta u. a., WWW 2013; Pinterest Pixie: Eksombatchai u. a., WWW 2018); das stützt den Neustart, nicht den lokalen Schnitt.

## Verifikation

- **Handrechnungen** auf Handnetz und Kontrastnetz (alle Brüche oben) in `tests/test_diffusion.py`, `tests/test_sweep.py`, `tests/test_wachsen.py`, `tests/test_netze.py`.
- **Orakel** (`tests/test_oracle_lokaler_schnitt.py`, kleine Zufallsnetze): Push gegen das dichte Gleichungssystem (Invariante, Fehlerschranke 0 ≤ ppr − p ≤ ε·Grad, Arbeitsschranke, nachgezählte Kantenzugriffe); exaktes PageRank gegen `numpy.linalg.solve` und `networkx.pagerank`; träge gegen nicht träge Gleichung; Wärmeleitung ohne Abschneiden gegen `scipy.linalg.expm`; Sweep gegen Neuzählung je Anfangsstück und `networkx.conductance`; gierige Erweiterung gegen eine Zweitfassung, die je Schritt alle Randplätze mit exakten Brüchen neu bewertet.
- **Claims** (`tests/test_claims.py`): jede Tabellenzeile steht wörtlich in der README; Stichproben der Ergebnisdatei werden aus dem Code nachgerechnet (Testzellen, Abstimm-Werte, Gradfalle, Größen-Messungen, Anteil gegen β, Fiedler, Gleichstandsbeispiel, Gütezusage).
- **Messdefinitionen, Netze, Zufall, Karte, Szenarien, Randfälle, Verdikte, Oberfläche:** AppTest (Standard, jedes Preset mit seiner Verdikt-Zeile, jeder Knopf, jedes Netz, jedes Verfahren, Reglerränder, Permalink, alle fünf Experimente), Layout, Footer, Laufzeit-Importe. Für beide Handnetze prüft `tests/test_zielhalle.py` jeden wählbaren Startplatz (gepflanzte Halle, F1, angezeigte Texte; Anteil gegen das dichte Gleichungssystem), `tests/test_konduktanz_satz.py` den Konduktanz-Vergleich gegen networkx.
- **Reproduzierbarkeit:** zwei Prozesse mit verschiedener Hash-Randomisierung liefern dieselben Netze und Schnitte.
- **Testzahl:** 499 Tests.

## Quellen

- R. Andersen, F. Chung, K. Lang, *Using PageRank to Locally Partition a Graph*, Langfassung 2006 ([PDF](https://fanchung.ucsd.edu/wp/localpartfull.pdf)): Push, Sweep, Satz 5 samt Beweis.
- Nur nach Zusammenfassungen wiedergegeben: J. Leskovec, K. Lang, A. Dasgupta, M. Mahoney (arXiv 0810.1355; in über 100 großen Netzen seien kleine Gemeinschaften die nach Konduktanz besten, größere gingen im Kern auf); F. Chen, Y. Zhang, K. Rohe (arXiv 1910.12937; unbereinigtes PageRank bevorzuge im gradkorrigierten Blockmodell hochgradige Knoten außerhalb des Startblocks); K. Kloster, D. Gleich (arXiv 1403.3148; lokale Wärmeleitung).
- P. Gupta u. a., *WTF: The Who to Follow Service at Twitter*, WWW 2013; C. Eksombatchai u. a., *Pixie*, WWW 2018.

Ein eigener Test gegen Literaturwerte fehlt (offen); die Handbeispiele sind eigene Rechnungen.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: gefundene Menge, Kernfragen, fünf Experimente |
| `lsn_netze.py` | Netze: Handnetze, Hallenverbund, Zufallsgemeinschaften, Sammelpunkte |
| `lsn_diffusion.py` | Push (nicht träge und träge), exaktes PageRank, Wärmeleitung |
| `lsn_wachsen.py` | gierige Erweiterung (drei Fassungen), Breitensuche-Kugel |
| `lsn_sweep.py` | Sweep, Regeln, Konduktanz, F1 |
| `lsn_verfahren.py` | alle Verfahren hinter einer Schnittstelle, Kennzahlen |
| `lsn_fiedler.py` | globaler Fiedler-Sweep (Bezug) |
| `lsn_messen.py` | Messreihen: Fälle, Zufalls-Seeds, Raster, Auswahlregel, Zählungen |
| `lsn_daten.py`, `daten/vorgerechnet.json` | vorgerechnete Messwerte |
| `lsn_zufall.py`, `lsn_rng.py` | blockweiser SplitMix64 mit exakten Schwellen, Hausgenerator (Vorlage) |
| `lsn_scenario.py`, `lsn_evaluation.py`, `lsn_karte.py`, `lsn_visualization.py` | Szenarien, Kennzahlen und Verdikte, Karte, Figuren |
| `lsn_constants.py`, `lsn_presets.py`, `lsn_layout.py` | Regler, Presets und Permalink, fester Kopf |
| `tools/vorrechnen.py` | erzeugt `daten/vorgerechnet.json` (in Etappen) |
| `tests/` | siehe „Verifikation“ |
| `requirements.txt`, `requirements-dev.txt` | Laufzeit (streamlit, numpy, scipy, pandas, plotly); Tests zusätzlich pytest und networkx |
| `.github/workflows/tests.yml`, `.gitignore`, `.streamlit/config.toml` | CI, Ausschlüsse, Einstellungen |

## Bewusst nicht umgesetzt

- Gerichtetes oder gewichtetes PageRank, Link-Vorhersage, Gemeinschaften für das ganze Netz (andere Demos, siehe oben).
- Die weiteren Demos der Reihe: „Trefferzeit“, „Etiketten“, „Pendelzeit“, „Widerstand als Netzmaß“, „Überdeckungszeit“, „Streife“.
- Fluss-basierte lokale Verfahren, Nibble, hk-relax; PDF-Export.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Entwickelt mit Python 3.14; die Tests der CI laufen mit Python 3.12.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, SciPy und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Irrfahrten auf Netzen: Trefferzeit bis Schnitt](https://sebastianhanisch.net/konzepte-irrfahrten.html).
