# # D118-FitnessGram-PS-Sync

A script used to synchronize student and teacher information in FitnessGram from PowerSchool.

## Overview

The purpose of this script is to gather information about student enrollments in specific PE courses from specific buildings in PowerSchool, then synchronize that information to FitnessGram. It accomplishes this by going through each school, finding the current term year (as our PE courses are year long), then doing an SQL query of all active students in the specified buildings. Each student is iterated through and searched for course enrollments matching the specified course names in the current term year. If enrollments are found, the teacher information for that course is also collected, and then the student, course, and teacher information is output to a .csv file. Once all students and buildings are processed, the output file is closed, and uploaded to FitnessGram via SFTP.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- FITNESSGRAM_SFTP_USERNAME
- FITNESSGRAM_SFTP_USERNAME
- FITNESSGRAM_SFTP_ADDRESS
- FITNESSGRAM_STUDENT_PASS
- FITNESSGRAM_STAFF_PASS

These are fairly self explanatory, and just relate to the usernames, passwords, and host IP/URLs for PowerSchool, as well as the SFTP login information for FitnessGram, and finally the default password that will be included in the file for students and staff (if you wish to mass change the passwords at the start of the year and check the box to overwrite passwords on the FitnessGram import site). If you wish to directly edit the script and include these credentials or to use other environment variable names, you can.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

**As part of the pysftp connection to the output SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

## Customization

This script should be pretty easy to set up for other district's uses, as it just uses standard tables and fields for the information it grabs. Besides the environment variables outlined above, you will want to change the following things:

- Change `PE_CLASS_NUMBERS` to a list containing your buildings PE course "numbers" (which don't actually have to be numbers in PS), these are the cc.course_number from PS and are used to find students in these courses who will be added to the output.
- Change `EMAIL_DOMAIN` to your districts email domain. Similarly, if you use something else besides the student number to construct student emails, you will want to change the `email = stuNum + EMAIL_DOMAIN` line to match your case.
- `VALID_SCHOOL_CODES` are the building codes in PowerSchool (and FitnessGram) that will be processed. This lets you skip schools where FitnessGram is not being used.
- `OUTPUT_FILE_NAME` is the name of the .csv file that is used, this does not have to be anything specific to be imported into FitnessGram so you can change it to your liking.
- If you dont want to make a new mapping in the FitnessGram importer and want to change the order in which columns are exported to the file, you will need to change both the initial print of the headers, and the lines that do the final output to reorder them to your needs.
