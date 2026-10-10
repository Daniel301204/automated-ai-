import sqlite3
from datetime import datetime,timezone
from pathlib import Path

SCHEMA='''CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, title TEXT, company TEXT, source TEXT, location TEXT, url TEXT, match_score INTEGER, status TEXT NOT NULL DEFAULT 'discovered', seen_at TEXT NOT NULL);'''

def connect(path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(p)); db.execute(SCHEMA); db.commit();return db

def upsert(db, jobs):
    now=datetime.now(timezone.utc).isoformat()
    for j in jobs:
        db.execute('''INSERT INTO jobs(job_id,title,company,source,location,url,match_score,status,seen_at)
          VALUES(?,?,?,?,?,?,?,'discovered',?) ON CONFLICT(job_id) DO UPDATE SET match_score=excluded.match_score, seen_at=excluded.seen_at''',
           (j['job_id'],j['title'],j['company'],j['source'],j['location'],j['url'],j.get('match_score',0),now))
    db.commit()

def set_status(db,job_id,status):
    if status not in ('saved','applied','ignored','discovered'): raise ValueError('Invalid status')
    db.execute('UPDATE jobs SET status=? WHERE job_id=?',(status,job_id));db.commit()
