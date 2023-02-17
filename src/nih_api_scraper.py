#!/usr/bin/env python
# 
# For NSF API docs, see:
# https://www.research.gov/common/webapi/awardapisearch-v1.htm
#
import argparse
import datetime
import logging
import sys
import json
import requests
#from requests.adapters import HTTPAdapter
from openpyxl import load_workbook
import xlsxwriter


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
ALL_RESULTS = []


def findAllProjects(start,end):

    obj = {
    "criteria":
    {
        "project_start_date": { "from_date": start, "to_date": end },
        "org_names": ["University of Texas"]
    },
        "offset":0,
        "sort_field":"project_start_date",
        "sort_order":"desc"
    }

    response = requests.post(URL, json = obj).json()
    results = response["results"]
    print(len(results))

    for x in results:

        startDate = x["project_start_date"]
        if(startDate):
            startDate = startDate[5:7] + "/" + startDate[8:10] + "/" + startDate[0:4]
        endDate = x["project_end_date"]
        if(endDate):
            endDate = endDate[5:7] + "/" + endDate[8:10] + "/" + endDate[0:4]
        else:
            print(x["appl_id"])

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
    not_found_worksheet.write_row(0, 0, AWARD_INFO, bold)
    collab_format = workbook.add_format({'font_color':'red'})


    f_row = 1
    nf_row = 1
    for item in ALL_RESULTS:
        name_str = item['piFirstName'].lower() + item['piLastName'].lower()
        collaborators = []
        formattedCollab = []

        if(item['coPDPI']!= "NO DATA AVAILABLE"):
            collaborators = item['coPDPI']
            
        if(collaborators):
            for z in collaborators:
                collab_str = z['first_name'].lower() + z['last_name'].lower()
                if collab_str in name_dict.keys():
                    formattedCollab.append(z['first_name'] + " " + z['last_name'])

        print(formattedCollab)
        
        if name_str in name_dict.keys() or formattedCollab:
            if not formattedCollab:
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
            else:
                found_worksheet.write_row(f_row, 0, [item['awardeeName'],
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
            if(formattedCollab):
                found_worksheet.write(f_row,14,json.dumps(formattedCollab),collab_format)
            else:
                found_worksheet.write(f_row,14,"None Found")
            f_row += 1
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
            nf_row += 1
        '''
        if(collaborators):
            print(collaborators)
            for x in collaborators:
                print(x)
                name_str = x['first_name'].lower() + x['last_name'].lower()
                if name_str in name_dict.keys():
                    print(name_str)
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
                                                 x['first_name'],
                                                 x['last_name'],
                                                 item['pdPIName'],
                                                 json.dumps(item['coPDPI']),
                                                 item['title']
                                                ])
                    f_row += 1
            '''
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