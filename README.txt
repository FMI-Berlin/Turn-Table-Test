Beschreibung des "Turn-Table-Tests"
-----------------------------------

gegeben:


In diesem Verzeichnis findest Du 3 "nmea"-Dateien von 3 verschiedenen Receivern,
die auf einem rotierenden runden Tisch montiert sind und sich die gleiche Antenne über
einen Splitter teilen, welche mitrotiert (kreisförmig).

Die 3 Dateien enthalten GGA Positionen.

1. "p23a_continious.nmea": RTK Positionen, P23A_0, mit kontinuierlichen Referenzdaten
2. "p23a_outages.nmea": RTK Positionen, P23A_1, mit ca. 3min kontinuierlichen Referenzdaten und ca. 5min ohne Referenzdaten (outage phase) Zyklus
3. "um980_outages.nmea": RTK Positionen, UM980, mit ca. 3min kontinuierlichen Referenzdaten und ca. 5min ohne Referenzdaten (outage phase) Zyklus


Aufgaben:

a.) Nimm Datei 1 als Referenzergebnis für die wahren Positionen und bestimme den horizontalen Kreisradius R der Antenne und den Drehwinkel über der Zeit.
b.) Plotte die Positionen aus Datei 1 abzüglich des Kreises (horizontal)
c.) Plotte die Positionen aus Datei 2 abzüglich des Kreises (horizontal)
d.) Plotte die Positionen aus Datei 3 abzüglich des Kreises (horizontal)

Plotte alles übereinander in sw, rt, gn und bl, so dass man sieht, welche Positionen horizontal von dem Sollkreis abweichen!

Erstelle dafür ein Python-Programm!

Frage erstmal nach, falls etwas unklar ist, bevor Du damit anfängst!