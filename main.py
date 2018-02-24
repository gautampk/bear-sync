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

MAC_USERNAME = 'gautampk'
ROOT = '/Users/gautampk/Dropbox/Bear/Sync'

def main():
    db = create_engine('sqlite:////Users/' + MAC_USERNAME + '/Library/' +
                       'Containers/net.shinyfrog.bear/Data/Documents/' +
                       'Application Data/database.sqlite')

    # Delete files marked as trashed in the database.
    trashed = pd.read_sql(
        "SELECT a.ZTITLE || '_' || a.Z_PK || '.md' as FILE,\
                c.ZTITLE as TAG_PATH, MAX(LENGTH(c.ZTITLE)) AS TAG_LEN\
            FROM ( SELECT * FROM ZSFNOTE WHERE ZTRASHED = 1 and ZSKIPSYNC = 0 ) a\
            LEFT JOIN Z_5TAGS b ON a.Z_PK = b.Z_5NOTES\
            LEFT JOIN ZSFNOTETAG c ON b.Z_10TAGS = c.Z_PK\
            GROUP BY FILE;",
        db
    )
    trashed.loc[trashed['TAG_PATH'].isnull(), 'TAG_PATH'] = ''

    for index, note in trashed.iterrows():
        try:
            os.remove(os.path.join(ROOT, note['TAG_PATH'], note['FILE']))
        except FileNotFoundError:
            pass

    # Get all the untrashed notes from the database.
    notes = pd.read_sql(
        "SELECT a.Z_PK as ID, a.ZTITLE || '_' || a.Z_PK || '.md' as FILE,\
                a.ZTEXT as CONTENT, CAST(a.ZMODIFICATIONDATE as REAL) as DATE,\
                c.ZTITLE as TAG_PATH, MAX(LENGTH(c.ZTITLE)) AS TAG_LEN\
            FROM ( SELECT * FROM ZSFNOTE WHERE ZTRASHED = 0 and ZSKIPSYNC = 0 ) a\
            LEFT JOIN Z_5TAGS b ON a.Z_PK = b.Z_5NOTES\
            LEFT JOIN ZSFNOTETAG c ON b.Z_10TAGS = c.Z_PK\
            GROUP BY FILE;",
        db
    )
    notes.loc[notes['TAG_PATH'].isnull(), 'TAG_PATH'] = ''

    # Get current Bear database metadata
    dbMeta = {}
    for note in notes.to_dict(orient='records'):
        dbMeta[note.pop('FILE')] = note

    # Get current export folder metadata
    fsMeta = {}
    for path, _, files in os.walk(ROOT):
        files = [f for f in files if f[0] != '.']
        for note in files:
            with open(os.path.join(path, note), encoding='utf-8') as f:
                content = f.read()

            fsMeta[note] = {
                'TAG_PATH': os.path.relpath(path, ROOT),
                'DATE': os.path.getmtime(os.path.join(path, note)) +
                            datetime(1970, 1, 1).timestamp() -
                            datetime(2001, 1, 1).timestamp(),
                'CONTENT': content
            }

    # Create all files that are new in the database.
    for key in dbMeta.keys() - fsMeta.keys():
        # Create the tag path
        try:
            os.makedirs(os.path.join(ROOT, dbMeta[key]['TAG_PATH']))
        except OSError as e:
            print(e)

        # Make the file
        with open(
            os.path.join(ROOT, dbMeta[key]['TAG_PATH'], key),
            'w', encoding='utf-8'
        ) as f:
            f.write(dbMeta[key]['CONTENT'])

        # Update the database with new time
        date = os.path.getmtime(os.path.join(ROOT, dbMeta[key]['TAG_PATH'], key)) + \
                    datetime(1970, 1, 1).timestamp() - datetime(2001, 1, 1).timestamp()
        db.execute(
            "UPDATE ZSFNOTE\
                SET ZMODIFICATIONDATE = " + str(date) + "\
                WHERE Z_PK = " + str(dbMeta[key]['ID']) + ";"
        )

    # Sync all existing files.
    for key in dbMeta.keys() - (dbMeta.keys() - fsMeta.keys()):
        if dbMeta[key]['DATE'] > fsMeta[key]['DATE']:
            # Save to hard drive.
            with open(
                os.path.join(ROOT, dbMeta[key]['TAG_PATH'], key),
                'w', encoding='utf-8'
            ) as f:
                f.write(dbMeta[key]['CONTENT'])
        elif dbMeta[key]['DATE'] < fsMeta[key]['DATE']:
            # Save to database.
            db.execute(
                "UPDATE ZSFNOTE\
                    SET ZTEXT = \"" + fsMeta[key]['CONTENT'] + "\"\
                    WHERE Z_PK = " + str(dbMeta[key]['ID']) + ";"
            )

        # Update the database with new time
        date = os.path.getmtime(os.path.join(ROOT, dbMeta[key]['TAG_PATH'], key)) + \
                    datetime(1970, 1, 1).timestamp() - datetime(2001, 1, 1).timestamp()
        db.execute(
            "UPDATE ZSFNOTE\
                SET ZMODIFICATIONDATE = " + str(date) + "\
                WHERE Z_PK = " + str(dbMeta[key]['ID']) + ";"
        )


if __name__ == "__main__":
    while True:
        main()
        sleep(10)
