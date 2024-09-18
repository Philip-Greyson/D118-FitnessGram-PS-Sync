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
SFTP_UN = os.environ.get('FITNESSGRAM_SFTP_USERNAME')  # the username provided by FitnessGram to log into the SFTP server
SFTP_PW = os.environ.get('FITNESSGRAM_SFTP_PASSWORD')  # the password provided by FitnessGram to log in using the username above
SFTP_HOST = os.environ.get('FITNESSGRAM_SFTP_ADDRESS')  # the URL/server IP provided by FitnessGram

DEFAULT_STUDENT_PASS = os.environ.get('FITNESSGRAM_STUDENT_PASS')
DEFAULT_STAFF_PASS = os.environ.get('FITNESSGRAM_STAFF_PASS')

print(f"DBUG: DB Username: {DB_UN} |DB Password: {DB_PW} |DB Server: {DB_CS}")  # debug so we can see where oracle is trying to connect to/with
print(f"DBUG: SFTP Username: {SFTP_UN} |SFTP Password: {SFTP_PW} |SFTP Server: {SFTP_HOST}")  # debug so we can see what FTP info is trying to be used

PE_CLASS_NUMBERS = ['PEKA','PEKP','PE1','PE2','PE3','PE4','PE5','PE6','PE7','PE8']  # course "numbers" from within PS that will be looked for, must match exactly
VALID_SCHOOL_CODES = ['2001','2005','2007','1004']  # list of PS school codes to process students from and search for classes
EMAIL_DOMAIN = '@d118.org'  # domain used to construct student emails from their student number

if __name__ == '__main__':  # main file execution
    with open('FG_Log.txt', 'w') as log:
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with open('FG.csv', 'w') as output:
            with oracledb.connect(user=DB_UN, password=DB_PW, dsn=DB_CS) as con:  # create the connecton to the database
                with con.cursor() as cur:  # start an entry cursor
                    print('SchoolID,StudentID,StudentFirstName,StudentLastName,StudentBirthdate,StudentGrade,StudentSexAssignedAtBirth,StudentUsername,StudentPassword,StudentReportEmail,StudentIsActive,ClassName,ClassID,ClassStartDate,ClassEndDate,TeacherID,TeacherFirstName,TeacherLastName,TeacherUsername,TeacherPassword,TeacherEmail,TeacherIsActive', file=output)  # print out the header row in the file
                    today = datetime.now()
                    for school in VALID_SCHOOL_CODES:
                        # first find the current year term
                        termid = None  # reset for each school in case we cant find a new valid term
                        termDCID = None  # reset for each school in case we cant find a new valid term
                        startDate = None  # date for the start of the course
                        endDate = None  # date for the end of the course
                        cur.execute("SELECT id, firstday, lastday, schoolid, dcid FROM terms WHERE schoolid = :schoolcode AND isyearrec = 1 ORDER BY dcid DESC", schoolcode=school)  # get a list of terms for the school, filtering to full years
                        terms = cur.fetchall()
                        for term in terms:  # go through every term
                            termStart = term[1]
                            termEnd = term[2]
                            #compare todays date to the start and end dates with 2 days before start so it populates before the first day of the term
                            if ((termStart - timedelta(days=2) < today) and (termEnd + timedelta(days=1) > today)):
                                termid = str(term[0])
                                termDCID = str(term[4])
                                startDate = termStart.strftime('%m/%d/%Y')
                                endDate = termEnd.strftime('%m/%d/%Y')
                                print(f'INFO: Found good term for year building {school}: {termid} | {termDCID}')
                                print(f'INFO: Found good term year for building {school}: {termid} | {termDCID}', file=log)
                        if termid:  # only continue if we found a valid term
                            # go through and find all active students at the current building
                            cur.execute('SELECT student_number, id, first_name, last_name, dob, grade_level, gender FROM students WHERE enroll_status = 0 AND schoolid = :schoolcode', schoolcode=school)
                            students = cur.fetchall()
                            for student in students:
                                # print(student)
                                stuNum = str(int(student[0]))  # the student number usually referred to as their "id number"
                                internalID = str(int(student[1]))  # the internal id of the student that is referenced in the class entries
                                firstName = str(student[2])
                                lastName = str(student[3])
                                birthday = student[4].strftime('%m/%d/%Y')  # format their birthday in the M/D/YYYY format
                                grade = str(int(student[5])) if int(student[5]) > 0 else 'K'  # if they are in a numeric grade level keep the number, otherwise need to mark pre-k or kinders as K
                                gender = str(student[6])
                                email = stuNum + EMAIL_DOMAIN
                                # now go through their classes and find those matching one of the class numbers
                                classBinds = ",".join(":" + str(i + 1) for i in range(len(PE_CLASS_NUMBERS)))# dynamically build the binds list based on the class numbers constant list. See https://python-oracledb.readthedocs.io/en/latest/user_guide/bind.html#bind
                                classStudentInfo = PE_CLASS_NUMBERS + [internalID, termid]  # append the student internal ID and termID to the class numbers so we can pass all of them together as binds to the query
                                sqlQuery = f'SELECT cc.course_number, cc.sectionid, courses.course_name, users.first_name, users.last_name, users.email_addr, users.teachernumber FROM cc \
                                    LEFT JOIN courses ON cc.course_number = courses.course_number \
                                    LEFT JOIN schoolstaff ON cc.teacherid = schoolstaff.id \
                                    LEFT JOIN users ON schoolstaff.users_dcid = users.dcid \
                                    WHERE cc.course_number IN ({classBinds}) AND cc.studentid = :studentInternalID AND cc.termid = :termid \
                                    ORDER BY cc.course_number'
                                # print(sqlQuery)
                                cur.execute(sqlQuery, classStudentInfo)
                                currentClassResults = cur.fetchall()
                                for classEntry in currentClassResults:
                                    classID = int(classEntry[1])
                                    className = str(classEntry[2])
                                    teacherFirstName = str(classEntry[3])
                                    teacherLastName = str(classEntry[4])
                                    teacherEmail = str(classEntry[5])
                                    teacherUsername = teacherEmail.split('@')[0]  # set their username to their email without the domain
                                    teacherID = int(classEntry[6])
                                    # print(classEntry)
                                    # print(classEntry, file=log)
                                    print(f'{school},{stuNum},{firstName},{lastName},{birthday},{grade},{gender},{stuNum},{DEFAULT_STUDENT_PASS},{email},Y,{className},{classID},{startDate},{endDate},{teacherID},{teacherFirstName},{teacherLastName},{teacherUsername},{DEFAULT_STAFF_PASS},{teacherEmail},Y')
                                    print(f'{school},{stuNum},{firstName},{lastName},{birthday},{grade},{gender},{stuNum},{DEFAULT_STUDENT_PASS},{email},Y,{className},{classID},{startDate},{endDate},{teacherID},{teacherFirstName},{teacherLastName},{teacherUsername},{DEFAULT_STAFF_PASS},{teacherEmail},Y', file=output)
                        else:
                            print(f'ERROR: Could not find valid term at building {school} for todays date of {today}, skipping building')
                            print(f'ERROR: Could not find valid term at building {school} for todays date of {today}, skipping building', file=log)