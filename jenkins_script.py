#!/usr/local/bin/python

import sys
import jenkins
import sqlite3

def main(jenkinHost,sqlite_file):
    conn = sqlite3.connect(sqlite_file)
    
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS jenkins_jobs
    (
        job_name TEXT UNIQUE NOT NULL,
        job_status TEXT NOT NULL,
        last_check TIMESTAMP DEFAULT current_timestamp
    );
    
    CREATE TRIGGER IF NOT EXISTS update_jenkins_jobs
    BEFORE UPDATE ON jenkins_jobs
    BEGIN
    UPDATE jenkins_jobs SET last_check = current_timestamp
    WHERE rowid = new.rowid;
    END;
    
    ''')
    
    server = jenkins.Jenkins(jenkinHost)
    
    try:
        jobs = server.get_jobs()
    except jenkins.JenkinsException:
        print 'ERROR: Cannot get jobs from jenkins server at',jenkinHost
        return None
    
    for job in jobs:
        insertOrUpdate(cur,job['name'], job['color'])
    conn.commit()
    conn.close()

def insertOrUpdate(cur,name,status):
    try:
        cur.execute("INSERT INTO jenkins_jobs(job_name,job_status) VALUES (:name,:status)",{'name':name,'status':status})
    except sqlite3.IntegrityError:
        cur.execute("UPDATE jenkins_jobs SET job_status=:status WHERE job_name=:name",{'name':name,'status':status})

if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1],sys.argv[2])
    else:
        print 'ERROR: Arguments are wrong'
        print 'Usage: jenkins_script.py <jenkins_host:port> <sqlite_file>'
 