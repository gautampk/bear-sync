# Bear Notes App Exporter and Sync

This script will export new files from the SQLite database where Bear stores
all notes. It assumes that every note has exactly one tag and uses that as the
filepath in the exported files.

It will additionally sync files that already exist in the database, taking
either the exported or the database version depending on the date they were
last modified.

It will NOT import new files into the database -- please use Bear's built-in
import function for this. Once the file has been imported it can be synced as
normal.
