'''
Bear Notes App Exporter and Sync

This script will export new files from the SQLite database where Bear stores
all notes. It assumes that every note has exactly one tag and uses that as the
filepath in the exported files.

It will additionally sync files that already exist in the database, taking
either the exported or the database version depending on the date they were
last modified.

It will NOT import new files into the database -- please use Bear's built-in
import function for this. Once the file has been imported it can be synced as
normal.
'''

from sqlalchemy import create_engine
import pandas as pd
import os
from datetime import datetime
from time import sleep

os.stat_float_times(True)

MAC_USERNAME = 'yourUsernameHere'
ROOT = '~/Applications/bear-sync/sync/'


def main():
    # Connect to Bear database.
    db = create_engine('sqlite:////Users/' + MAC_USERNAME + '/Library/' +
                       'Containers/net.shinyfrog.bear/Data/Documents/' +
                       'Application Data/database.sqlite')

    # Build list of files in the DB.
    dbNotes = pd.read_sql(
        "SELECT a.Z_PK as NID, a.ZTITLE || '.' || a.Z_PK || '.md' as FILE,\
                a.ZTEXT as CONTENT, CAST(a.ZMODIFICATIONDATE as REAL) as DATE,\
                c.ZTITLE as TAG_PATH, MAX(LENGTH(c.ZTITLE)) AS TAG_LEN,\
                a.ZTRASHED as TRASHED\
            FROM ( SELECT * FROM ZSFNOTE WHERE ZSKIPSYNC = 0 ) a\
            LEFT JOIN Z_5TAGS b ON a.Z_PK = b.Z_5NOTES\
            LEFT JOIN ZSFNOTETAG c ON b.Z_10TAGS = c.Z_PK\
            GROUP BY FILE;",
        db
    ).set_index('NID')
    dbNotes.loc[dbNotes['TAG_PATH'].isnull(), 'TAG_PATH'] = ''
    dbNotes = dbNotes.to_dict(orient='index')

    # Build list of files on the FS.
    fsNotes = {}
    for path, _, files in os.walk(ROOT):
        # Include only .md Markdown files.
        files = [f for f in files if (
            os.path.splitext(f)[1] == '.md' and
            f[0] != '.'
        )]

        # Go through every note in the folder.
        for note in files:
            # Get the unique note ID.
            nid = os.path.splitext(os.path.splitext(note)[0])[1][1:]

            # Test the note ID to make sure it's an integer.
            try:
                int(nid)
            except ValueError:
                # If it's not an integer, skip it.
                continue
            else:
                # Get the contents of the note.
                with open(os.path.join(path, note), encoding='utf-8') as f:
                    content = f.read()

                # Add an entry.
                fsNotes[int(nid)] = {
                    'FILE': note,
                    'CONTENT': content,
                    'DATE': os.path.getmtime(os.path.join(path, note)) +
                                datetime(1970, 1, 1).timestamp() -
                                datetime(2001, 1, 1).timestamp(),
                    'TAG_PATH': os.path.relpath(path, ROOT),
                }

    # Go through every file in the DB and compare it with the current FS
    #   version.
    for nid in dbNotes:
        try:
            fsNotes[nid]
        except KeyError:  # Note doesn't exist on the FS, so create it.
            if dbNotes[nid]['TRASHED'] == 0:
                # Create the tag path.
                try:
                    os.makedirs(os.path.join(ROOT, dbNotes[nid]['TAG_PATH']))
                except OSError as e:
                    pass

                # Make the file.
                with open(
                    os.path.join(
                        ROOT,
                        dbNotes[nid]['TAG_PATH'],
                        dbNotes[nid]['FILE']
                    ),
                    'w', encoding='utf-8'
                ) as f:
                    f.write(dbNotes[nid]['CONTENT'])

                # Update the DB with new time.
                date = os.path.getmtime(
                    os.path.join(
                        ROOT,
                        dbNotes[nid]['TAG_PATH'],
                        dbNotes[nid]['FILE']
                    )
                ) + datetime(1970, 1, 1).timestamp() - datetime(2001, 1, 1).timestamp()
                db.execute(
                    "UPDATE ZSFNOTE\
                        SET ZMODIFICATIONDATE = " + str(date) + "\
                        WHERE Z_PK = " + str(nid) + ";"
                )
        else:  # Note already exists, so compare details.
            # First, make sure the note hasn't been trashed on the DB.
            #   NB: trashing a note from the FS will not work, as it will be
            #   re-added on the next sync. To trash a note you must use Bear.
            if dbNotes[nid]['TRASHED'] != 0:
                try:
                    os.remove(
                        os.path.join(
                            ROOT,
                            fsNotes[nid]['TAG_PATH'],
                            fsNotes[nid]['FILE']
                        )
                    )
                except FileNotFoundError:
                    pass
            else:
                # Next, check if the DB filename or tag path has changed.
                if (
                    dbNotes[nid]['FILE'] != fsNotes[nid]['FILE'] or
                    dbNotes[nid]['TAG_PATH'] != fsNotes[nid]['TAG_PATH']
                ):
                    # Update the FS filename and path to match the DB version.
                    #   NB: to change the path of a note on the FS, update the
                    #   tags inside the note, and wait for the sync with Bear
                    #   to complete.
                    # Create the tag path.
                    try:
                        os.makedirs(os.path.join(ROOT, dbNotes[nid]['TAG_PATH']))
                    except OSError as e:
                        pass

                    os.rename(
                        os.path.join(
                            ROOT,
                            fsNotes[nid]['TAG_PATH'],
                            fsNotes[nid]['FILE']
                        ),
                        os.path.join(
                            ROOT,
                            dbNotes[nid]['TAG_PATH'],
                            dbNotes[nid]['FILE']
                        )
                    )

                    fsNotes[nid]['TAG_PATH'] = dbNotes[nid]['TAG_PATH']
                    fsNotes[nid]['FILE'] = dbNotes[nid]['FILE']

                # Now compare the dates and sync.
                if dbNotes[nid]['DATE'] > fsNotes[nid]['DATE']:
                    # Save DB to FS.
                    with open(
                        os.path.join(
                            ROOT,
                            fsNotes[nid]['TAG_PATH'],
                            fsNotes[nid]['FILE']
                        ),
                        'w',
                        encoding='utf-8'
                    ) as f:
                        f.write(dbNotes[nid]['CONTENT'])
                elif dbNotes[nid]['DATE'] < fsNotes[nid]['DATE']:
                    # Save FS to DB.
                    db.execute(
                        "UPDATE ZSFNOTE\
                            SET ZTEXT = \"" + fsNotes[nid]['CONTENT'] + "\"\
                            WHERE Z_PK = " + str(nid) + ";"
                    )

                # Update the DB with new time.
                date = os.path.getmtime(
                    os.path.join(
                        ROOT,
                        fsNotes[nid]['TAG_PATH'],
                        fsNotes[nid]['FILE']
                    )
                ) + datetime(1970, 1, 1).timestamp() - datetime(2001, 1, 1).timestamp()
                db.execute(
                    "UPDATE ZSFNOTE\
                        SET ZMODIFICATIONDATE = " + str(date) + "\
                        WHERE Z_PK = " + str(nid) + ";"
                )

    # Go back through the FS and remove empty folders.
    for path, folders, files in os.walk(ROOT):
        # Include only .md Markdown files.
        files = [f for f in files if (
            os.path.splitext(f)[1] == '.md' and
            f[0] != '.'
        )]

        if len(files) == 0 and len(folders) == 0:
            os.rmdir(path)


if __name__ == "__main__":
    while True:
        main()
        sleep(10)
