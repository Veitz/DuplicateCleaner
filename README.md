# dupcleaner

**dupcleaner** ist ein plattformunabhängiges Python-Tool, um doppelte Dateien zu finden und automatisch die älteren Versionen zu löschen oder zu verschieben.


## Phase

    Phase 1: Scannen und DB-Befüllen

    Phase 2: Kandidaten filtern

    Phase 3: Hashing nur für Verdächtige

    Phase 4: Duplikate löschen (oder verschieben, oder nur anzeigen)


## Features

    SQLite mit files-Tabelle

    Fortschrittsanzeige

    Fehlerbehandlung (PermissionError, FileNotFoundError)

    Hashing blockweise (MD5)

    Dry-Run und Logfile

    Filterung nur nach Größe & Hash

    Sicheres Löschen oder Verschieben  


## Funktionen

- Findet Duplikate anhand von Dateigröße und Hash (MD5)
- Speichert alle Dateien in einer SQLite-Datenbank
- Löscht ältere Duplikate oder verschiebt sie in einen Ordner
- Unterstützt Dry-Run (Testlauf ohne echte Löschung)
- Läuft auf Linux, macOS und Windows


## Verwendung

```bash
# 1. Verzeichnis scannen
python dupcleaner.py /pfad/zum/verzeichnis

# 2. Kandidaten hashen
python dupcleaner.py /pfad/zum/verzeichnis --hash

# 3. Duplikate anzeigen (nur Test)
python dupcleaner.py /pfad/zum/verzeichnis --clean --dry-run

# 4. Duplikate wirklich löschen
python dupcleaner.py /pfad/zum/verzeichnis --clean

# 5. Optional in den Papierkorb/Trash-Ordner verschieben
python dupcleaner.py /pfad/zum/verzeichnis --clean --trash-dir /pfad/zum/papierkorb
```

### Symlinks & Rechte  

    Linux: /proc, /dev, Symlinks manche „Dateien“ lassen sich nicht öffnen. Das Skript ignoriert PermissionError.  

    Windows: Meist weniger Symlinks, aber Zugriffsrechte (z. B. gesperrte Dateien) können auftreten.  

    Evtl. Path(...).is_symlink() prüfen, wenn Symlinks explizit auszuschließen sind.  

	(pip install Send2Trash zur Benutzung des nativen Papierkorbs/Trash-Ordner)  


### pyinstaller

	pyinstaller --onefile --name dupcleaner dupcleaner.py

### by the way
Das geht sequentiell, Dateisystem-Zugriffe sind der Flaschenhals, nicht SQLite.  
SQLite ist einfach: keine Server-Installation.  
SQL-Filter für Gruppierung nach Größe/Name/Datum sind schnell.  
Hash nur auf gleich große Dateien: spart massiv Zeit.  
Dateigröße zuerst filtern, dann optional Dateiname, dann Hash.  
Chunked Hashing: große Dateien Stück für Stück lesen.  
Threads: Paralleles Hashing kann helfen (aber I/O ist meist der Engpass).  
Manche Ordner (/proc, /sys unter Linux) enthalten keine echten Dateien.  
Symbolische Links können Endlosschleifen erzeugen.  
Rechteprobleme (Dateien, die du nicht lesen darfst).  



