import os
import sys
import sqlite3
import hashlib
from pathlib import Path
import argparse
import shutil
import time
import signal

DB_NAME = "duplicates.db"
CHUNK_SIZE = 8192

# --- Signal-Handling für sauberen Abbruch ---
stop_requested = False
def handle_sigint(signum, frame):
    global stop_requested
    stop_requested = True
    print("\nAbbruch angefordert, warte auf aktuellen Schritt...")

signal.signal(signal.SIGINT, handle_sigint)


def init_db(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        path TEXT UNIQUE,
        size INTEGER,
        mtime REAL,
        hash TEXT
    )
    """)
    conn.commit()


def scan_directory(root_path, conn):
    total = 0
    cursor = conn.cursor()
    cursor.execute("BEGIN")
    for path in Path(root_path).rglob('*'):
        if stop_requested:
            break
        if not path.is_file():
            continue
        try:
            stat = path.stat()
            cursor.execute(
                "INSERT OR IGNORE INTO files (path, size, mtime) VALUES (?, ?, ?)",
                (str(path), stat.st_size, stat.st_mtime)
            )
            total += 1
            if total % 1000 == 0:
                print(f"{total} Dateien erfasst...")
                conn.commit()
        except (PermissionError, FileNotFoundError):
            continue
    conn.commit()
    print(f"Scan abgeschlossen. {total} Dateien gespeichert.")


def get_candidates(conn):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT size FROM files
    GROUP BY size
    HAVING COUNT(*) > 1
    """)
    return [row[0] for row in cursor.fetchall()]


def compute_md5(path):
    h = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(CHUNK_SIZE):
                h.update(chunk)
    except (PermissionError, FileNotFoundError):
        return None
    return h.hexdigest()


def hash_candidates(conn, sizes):
    cursor = conn.cursor()
    for size in sizes:
        cursor.execute("SELECT id, path FROM files WHERE size = ? AND hash IS NULL", (size,))
        rows = cursor.fetchall()
        for row in rows:
            if stop_requested:
                break
            fid, fpath = row
            md5 = compute_md5(fpath)
            if md5:
                cursor.execute("UPDATE files SET hash = ? WHERE id = ?", (md5, fid))
        conn.commit()


def find_duplicates(conn):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT hash FROM files
    WHERE hash IS NOT NULL
    GROUP BY hash
    HAVING COUNT(*) > 1
    """)
    return [row[0] for row in cursor.fetchall()]


def process_duplicates(conn, dry_run=False, trash_dir=None):
    cursor = conn.cursor()
    hashes = find_duplicates(conn)
    total_deleted = 0

    for h in hashes:
        cursor.execute("""
        SELECT id, path, mtime FROM files
        WHERE hash = ?
        ORDER BY mtime DESC
        """, (h,))
        rows = cursor.fetchall()
        keep = rows[0]  # Neuste Datei behalten
        duplicates = rows[1:]  # Rest löschen

        for dup in duplicates:
            _, dup_path, _ = dup
            try:
                if dry_run:
                    print(f"[DRY RUN] Würde löschen: {dup_path}")
                elif trash_dir:
                    target = Path(trash_dir) / Path(dup_path).name
                    shutil.move(dup_path, target)
                    print(f"Verschoben: {dup_path} -> {target}")
                else:
                    os.remove(dup_path)
                    print(f"Gelöscht: {dup_path}")

                total_deleted += 1
            except Exception as e:
                print(f"Fehler bei {dup_path}: {e}")

    print(f"{total_deleted} Duplikate bearbeitet.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="Wurzelverzeichnis zum Scannen")
    parser.add_argument("--hash", action="store_true", help="Kandidaten hashen")
    parser.add_argument("--clean", action="store_true", help="Duplikate bereinigen")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht löschen")
    parser.add_argument("--trash-dir", help="Statt löschen in diesen Ordner verschieben")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_NAME)
    init_db(conn)

    if not args.hash and not args.clean:
        scan_directory(args.root, conn)
        sizes = get_candidates(conn)
        print(f"{len(sizes)} Größen mit möglichen Duplikaten gefunden.")
        print("Starte Skript erneut mit --hash um Hashes zu berechnen.")
    elif args.hash:
        sizes = get_candidates(conn)
        print(f"{len(sizes)} Kandidaten-Cluster werden gehasht...")
        hash_candidates(conn, sizes)
        print("Hashing abgeschlossen. Starte mit --clean um zu bereinigen.")
    elif args.clean:
        process_duplicates(conn, dry_run=args.dry_run, trash_dir=args.trash_dir)

    conn.close()


if __name__ == "__main__":
    main()
