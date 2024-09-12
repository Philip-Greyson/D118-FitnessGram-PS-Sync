"""Script to send the student PE info to FitnessGram via SFTP.

https://github.com/Philip-Greyson/D118-FitnessGram-PS-Sync


Needs oracledb, pysftp: pip install oracledb pysftp --upgrade
"""

# importing module
import datetime  # used to get current date for course info
import os  # needed to get environement variables
import sys
from datetime import *

import oracledb
import pysftp

DB_UN = os.environ.get('POWERSCHOOL_READ_USER')  # username for read-only database user
DB_PW = os.environ.get('POWERSCHOOL_DB_PASSWORD')  # the password for the database account
DB_CS = os.environ.get('POWERSCHOOL_PROD_DB')  # the IP address, port, and database name to connect to

#set up sftp login info, stored as environment variables on system
SFTP_UN = os.environ.get('')  # the username provided by FitnessGram to log into the SFTP server
SFTP_PW = os.environ.get('')  # the password provided by FitnessGram to log in using the username above
SFTP_HOST = os.environ.get('')  # the URL/server IP provided by FitnessGram

print(f"DBUG: DB Username: {DB_UN} |DB Password: {DB_PW} |DB Server: {DB_CS}")  # debug so we can see where oracle is trying to connect to/with
# print(f"DBUG: SFTP Username: {SFTP_UN} |SFTP Password: {SFTP_PW} |SFTP Server: {SFTP_HOST}")  # debug so we can see what FTP info is trying to be used

PE_CLASS_NUMBERS = ['PEKA','PEKP','PE1','PE2','PE3','PE4','PE5','PE6','PE7','PE8']  # course "numbers" from within PS that will be looked for, must match exactly
VALID_SCHOOL_CODES = ['2001','2005','2007','1004']  # list of PS school codes to process students from and search for classes

if __name__ == '__main__':  # main file execution
    with open('FG_Log.txt', 'w') as log:
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with open('FG.csv', 'w') as output:
            with oracledb.connect(user=DB_UN, password=DB_PW, dsn=DB_CS) as con:  # create the connecton to the database
                with con.cursor() as cur:  # start an entry cursor
                    print('School ID,Student ID,Student First name,Student Last Name,Student Middle Initial,Student Nickname,Student birthdate,Student Grade,Student Gender,Student Ethnicity,Student Username,Student Password,Student Report Email,Student Address 3,StudentPrintBodyComp,Parent Report Email 1,Parent Report EMail 2,StudentPrintReportInSpanish,Student Permanent Exemption Code,Student is Active?,Class Name,Class ID,ClassDecriptionCode,Class Start Date,Class End Date,Teacher ID,Teacher First Name,Teacher Last Name,Teacher Middle Initial,Teacher Nickname,Teacher Username,Teacher Password,Teacher Email,Teacher Address 3,Teacher is Active?', file=output)  # print out the header row in the file
                    today = datetime.now()
                    for school in VALID_SCHOOL_CODES:
                        # first find the current year term
                        termid = None  # reset for each school in case we cant find a new valid term
                        termDCID = None  # reset for each school in case we cant find a new valid term
                        cur.execute("SELECT id, firstday, lastday, schoolid, dcid FROM terms WHERE schoolid = :schoolcode AND isyearrec = 1 ORDER BY dcid DESC", schoolcode=school)  # get a list of terms for the school, filtering to full years
                        terms = cur.fetchall()
                        for term in terms:  # go through every term
                            termStart = term[1]
                            termEnd = term[2]
                            #compare todays date to the start and end dates with 2 days before start so it populates before the first day of the term
                            if ((termStart - timedelta(days=2) < today) and (termEnd + timedelta(days=1) > today)):
                                termid = str(term[0])
                                termDCID = str(term[4])
                                print(f'INFO: Found good term for year building {school}: {termid} | {termDCID}')
                                print(f'INFO: Found good term year for building {school}: {termid} | {termDCID}', file=log)
                        if termid:  # only continue if we found a valid term
                            # go through and find all active students at the current building
                            cur.execute('SELECT student_number, id, first_name, last_name, dob, grade_level, gender FROM students WHERE enroll_status = 0 AND schoolid = :schoolcode', schoolcode=school)
                            students = cur.fetchall()
                            for student in students:
                                print(student)
                                stuNum = str(int(student[0]))  # the student number usually referred to as their "id number"
                                internalID = str(int(student[1]))  # the internal id of the student that is referenced in the class entries
                                firstName = str(student[2])
                                lastName = str(student[3])
                                birthday = student[4].strftime('%M/%D/%Y')  # format their birthday in the M/D/YYYY format
                                grade = int(student[5])
                                gender = str(student[6])
                                # now go through their classes and find those matching one of the class numbers
                                classBinds = ",".join(":" + str(i + 1) for i in range(len(PE_CLASS_NUMBERS)))  # dynamically build the binds list based on the class numbers list
                                # print(classBinds)
                                classStudentInfo = PE_CLASS_NUMBERS + [internalID, termid]  # append the student internal ID and termID to the class numbers so we can pass all of them together as binds to the query
                                # print(classStudentInfo)
                                sqlQuery = f'SELECT cc.course_number, cc.sectionid, courses.course_name, users.lastfirst, users.email_addr, users.teachernumber FROM cc \
                                    LEFT JOIN courses ON cc.course_number = courses.course_number \
                                    LEFT JOIN schoolstaff ON cc.teacherid = schoolstaff.id \
                                    LEFT JOIN users ON schoolstaff.users_dcid = users.dcid \
                                    WHERE cc.course_number IN ({classBinds}) AND cc.studentid = :studentInternalID AND cc.termid = :termid \
                                    ORDER BY cc.course_number'
                                # print(sqlQuery)
                                cur.execute(sqlQuery, classStudentInfo)
                                currentClassResults = cur.fetchall()
                                for classes in currentClassResults:
                                    className = str()
                                    print(classes)
                                    print(classes, file=log)
                        else:
                            print(f'ERROR: Could not find valid term at building {school} for todays date of {today}, skipping building')
                            print(f'ERROR: Could not find valid term at building {school} for todays date of {today}, skipping building', file=log)