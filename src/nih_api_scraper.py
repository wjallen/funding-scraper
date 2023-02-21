#!/usr/bin/env python
# 
# For NIH API docs, see:
# https://api.reporter.nih.gov/
#

import argparse
import datetime
import logging
import sys
import json
import requests
from openpyxl import load_workbook
import xlsxwriter
from fuzzywuzzy import fuzz

logging.basicConfig(level=logging.DEBUG,
format='%(asctime)s %(levelname)s %(message)s',
      filename='/data/nih.log',
      filemode='w')

"""
Define the url for NIH API and the info being
saved to our spreadsheets. ALL_RESULTS will store
a list of objects created from the data parsed from
API POST responses.
"""

URL = 'https://api.reporter.nih.gov/v2/projects/search'
AWARD_INFO=['id',
            'agency',
            'awardeeName',
            'startDate',
            'expDate',
            'estimatedTotalAmt',
            'piFirstName',
            'piLastName',
            'pdPIName',
            'title',
            'coPDPI',
            'taccPDPI',
           ]

AGENCY = 'NIH'

ALL_UNIVERSITIES={
    'UNIVERSITY OF TEXAS RIO GRANDE VALLEY': 'University of Texas Rio Grande Valley', 
    'UNIVERSITY OF TEXAS DALLAS': 'University of Texas at Dallas (UTD) (UT Dallas)', 
    'UNIVERSITY OF TEXAS HLTH CTR AT TYLER': 'University of Texas Health Science Center at Tyler', 
    'UNIVERSITY OF TX MD ANDERSON CAN CTR': 'University of Texas MD Anderson Cancer Center', 
    'UNIVERSITY OF TEXAS AT AUSTIN': 'University of Texas at Austin (UT) (UT Austin)', 
    'UNIVERSITY OF TEXAS HLTH SCI CTR HOUSTON': 'University of Texas Health Science Center at Houston', 
    'UT SOUTHWESTERN MEDICAL CENTER': 'University of Texas Southwestern Medical Center (UTSW) (UT Southwestern)', 
    'UNIVERSITY OF TEXAS TYLER': 'University of Texas Tyler', 
    'UNIVERSITY OF TEXAS HLTH SCIENCE CENTER': 'University of Texas Health Science Center at San Antonio', 
    'UNIVERSITY OF TEXAS ARLINGTON': 'University of Texas at Arlington (UTA) (UT Arlington)', 
    'UNIVERSITY OF TEXAS EL PASO': 'University of Texas at El Paso (UTEP)', 
    'UNIVERSITY OF TEXAS MED BR GALVESTON': 'University of Texas Medical Branch at Galveston', 
    'UNIVERSITY OF TEXAS OF THE PERMIAN BASIN': 'University of Texas Permian Basin', 
    'UNIVERSITY OF TEXAS SAN ANTONIO': 'University of Texas at San Antonio'
}

ALL_RESULTS = []


def findAllProjects(start,end):

    """
    Given a start and end date, the function makes a POST call to NIH API
    given a date range and a list of strings for the query. Data from the response
    is parsed and appended to our list of formatted objects. North Texas results are
    removed.
    """

    texas = {
    "criteria":
    {
        "project_start_date": { "from_date": start, "to_date": end },
        "org_names": ["UNIVERSITY OF TEXAS","University of TX","UT SOUTHWESTERN MEDICAL CENTER"]
    },
        "limit": 499,
        "offset":0,
        "sort_field":"project_start_date",
        "sort_order":"desc"
    }


    response = requests.post(URL, json = texas).json()

    results = response["results"]

    with open('/data/data.json','w') as f:
        json.dump(results,f)

    logging.info(f"START: {start} END: {end}")
    print(f'Before removing North Texas: {len(results)}')

    for x in results:

        # Remove all of North Texas Results

        if ('NORTH' in x['organization']['org_name']):
            logging.info(f"REMOVING: {x['organization']['org_name']}")
            continue

        startDate = x["project_start_date"]
        if(startDate):
            startDate = startDate[5:7] + "/" + startDate[8:10] + "/" + startDate[0:4]
        endDate = x["project_end_date"]
        if(endDate):
            endDate = endDate[5:7] + "/" + endDate[8:10] + "/" + endDate[0:4]
        else:
            endDate = "N/A"

        coPDPI = []
        for y in x["principal_investigators"]:
            if(y["is_contact_pi"] == True):
                piFirstName = y["first_name"]
                piLastName = y["last_name"]
            else:
                coPDPI.append({
                    "first_name": y["first_name"],
                    "middle_name": y["last_name"],
                    "last_name" : y["last_name"]
                    })

        # Create objects with the information we want.

        myObj = {
            "id" : x["appl_id"],
            "agency": x["agency_ic_fundings"][0]["abbreviation"],
            "awardeeName": x["organization"]["org_name"],
            "piFirstName": piFirstName,
            "piLastName": piLastName,
            "coPDPI": coPDPI or "NO DATA AVAILABLE",
            "pdPIName": x["contact_pi_name"],
            "startDate": startDate,
            "expDate": endDate,
            "estimatedTotalAmt": x["award_amount"],
            "title": x["project_title"],
            "city" : x["organization"]["org_city"]
        }

        ALL_RESULTS.append(myObj)

    print(f'After removing North Texas: {len(ALL_RESULTS)}')

def findTACCUsers(userlist,output):

    """
    Given a list of award information and a list of TACC usernames, write
    an output workbook with two worksheets: (1) Awards that match a TACC username
    and (2) awards that don't match a TACC username.
    """

    userlist_wb = load_workbook(filename=userlist, read_only=True)
    worksheet = userlist_wb['utrc_institution_accounts']
    row_count = worksheet.max_row
    rows = worksheet.rows

    name_dict = {}

    if row_count > 1:
        next(rows) # skip header row
        for row in rows:
            institution = row[0].value
            first_name = row[1].value
            last_name = row[2].value
            name = ' '.join([first_name, last_name]).lower().replace(' ','')
            name_dict[name] = [institution, first_name, last_name]

    logging.info(f'number of items in name_dict = {len(name_dict.keys())}')

    workbook = xlsxwriter.Workbook(output)
    bold = workbook.add_format({'bold': 1})
    found_worksheet = workbook.add_worksheet('utrc_nsf_funding')
    found_worksheet.write_row(0, 0, ['utrc_institution', 'utrc_first_name', 'utrc_last_name']+AWARD_INFO, bold)
    not_found_worksheet = workbook.add_worksheet('not_utrc_nsf_funding')
    not_found_worksheet.write_row(0, 0, AWARD_INFO+['conflicts'], bold)
    collab_format = workbook.add_format({'font_color':'red'})
    fizz_format = workbook.add_format({'bg_color':'orange', 'bold':True})

    f_row = 1
    nf_row = 1

    postCheck = []

    for item in ALL_RESULTS:
        name_str = item['piFirstName'].lower() + item['piLastName'].lower()
        name_str = name_str.replace(" ", "")
        first_name_str = item['piFirstName'].lower()
        last_name_str = item['piLastName'].lower()
        affiliation = item['awardeeName']
        collaborators = []
        formattedCollab = []
        collab_str = ""

        if(item['coPDPI']!= "NO DATA AVAILABLE"):
            collaborators = item['coPDPI']
            
        if(collaborators):
            for z in collaborators:
                collab_str = z['first_name'].lower() + z['last_name'].lower()
                if collab_str in name_dict.keys():
                    formattedCollab.append(z['first_name'] + " " + z['last_name'])

        # If the name matches one in our TACC system, add it to the found sheet. 
        # If the collaborators are in our TACC systems, highlight their names red.

        if name_str in name_dict.keys():
            logging.info(f'{name_str} matches {name_dict[name_str]}')
            found_worksheet.write_row(f_row, 0, [name_dict[name_str][0],
                                                name_dict[name_str][1],
                                                name_dict[name_str][2],
                                                item['id'],
                                                item['agency'],
                                                item['awardeeName'],
                                                item['startDate'],
                                                item['expDate'],
                                                item['estimatedTotalAmt'],
                                                item['piFirstName'],
                                                item['piLastName'],
                                                item['pdPIName'],
                                                item['title'],
                                                json.dumps(item['coPDPI'])
                                                ])
            if(formattedCollab):
                found_worksheet.write(f_row,14,json.dumps(formattedCollab),collab_format)
            else:
                found_worksheet.write(f_row,14,"None Found")
            f_row += 1

        # If the name does not match one in our TACC system, but a collaborator does, add it to
        # the found sheet. Collaborator will be highlighted in red.

        elif formattedCollab:
            found_worksheet.write_row(f_row, 0, [name_dict[formattedCollab[0].lower().replace(" ","")][0],
                                                item['piFirstName'],
                                                item['piLastName'],
                                                item['id'],
                                                item['agency'],
                                                item['awardeeName'],
                                                item['startDate'],
                                                item['expDate'],
                                                item['estimatedTotalAmt'],
                                                item['piFirstName'],
                                                item['piLastName'],
                                                item['pdPIName'],
                                                item['title'],
                                                json.dumps(item['coPDPI'])
                                                ])
            found_worksheet.write(f_row,14,json.dumps(formattedCollab),collab_format)
            f_row += 1

        # If the name does not match one in our TACC system, we will search through names that have an exact 
        # last name match. The first name will be compared using fuzzywuzzy word matching. If this returns 
        # a score of 89 or higher, the affiliation will be checked. If affiliation matches, the name will be considered a match.

        else:
            logging.info(f'{name_str} has no match')
            not_found_worksheet.write_row(nf_row, 0,[ item['id'],
                                                        item['agency'],
                                                        item['awardeeName'],
                                                        item['startDate'],
                                                        item['expDate'],
                                                        item['estimatedTotalAmt'],
                                                        item['piFirstName'],
                                                        item['piLastName'],
                                                        item['pdPIName'],
                                                        item['title'],
                                                        json.dumps(item['coPDPI'])
                                                    ])
            not_found_worksheet.write(nf_row,11,"None Found")                                  
            for x in name_dict:
                if(last_name_str != name_dict[x][2].lower()):
                    continue
                y = fuzz.ratio(first_name_str,name_dict[x][1].lower())
                if(y >= 89 and y < 100 ):
                    logging.warning(f"Ratio of {y} for {first_name_str} {last_name_str} and {name_dict[x][1].lower()} {name_dict[x][2].lower()}")
                    logging.warning(f"Checking {affiliation} and {name_dict[x][0]}")
                    if(ALL_UNIVERSITIES[affiliation] == name_dict[x][0]):
                        logging.warning(f"{affiliation} matched with {name_dict[x][0]}")
                        not_found_worksheet.write(nf_row,12,f"{item['piFirstName'] }{item['piLastName']} vs {name_dict[x][1]}{name_dict[x][2]}",fizz_format)                                  
            nf_row += 1

    workbook.close()
    return


def main():

    parser = argparse.ArgumentParser(description='Scrape NSF funded awards')
    parser.add_argument('-s', '--start', dest='start_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-e', '--end', dest='end_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-i', '--institution', dest='inst', help='institution search term, format = University+of+Texas', required=True)
    parser.add_argument('-u', '--userlist', dest='userlist', help='input file with list of names and affiliations', required=True)
    parser.add_argument('-o', '--output', dest='output', help='output file', required=True)
    args = parser.parse_args()

    start = str(args.start_date)[0:4] + "-" + str(args.start_date)[4:6] + "-" + str(args.start_date)[6:]
    end = str(args.end_date)[0:4] + "-" + str(args.end_date)[4:6] + "-" + str(args.end_date)[6:]

    findAllProjects(start,end)
    findTACCUsers('/data/' + args.userlist, '/data/' + args.output)

if __name__ == '__main__':
    main()