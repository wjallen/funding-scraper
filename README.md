Funding Scraper for UTRC Reports
================================

This tool is designed to pull federal grant information associated with a given
list of PIs + Affiliations, and falling within a user-defined date range. 


Set Up and Run
--------------

The easiest way to run this tool is using Docker. After you install Docker,
clone this repo:

```
$ git clone https://github.com/wjallen/funding-scraper
$ cd funding-scraper/
```

Stage an input list of PIs + Affiliations into the `data/` folder (see format
requirements in next section):

```
$ cp /path/to/PIs_Afills.xlsx ./data/
```

Edit the Makefile to your search specification. For example, the following is 
used to search date ranges 2022-06-01 to 2022-06-30 and only institutions that
match the search term "University+of+Texas". The input list of PIs + Affiliations
was staged into the `data/` folder, and the final output will be written into
the same folder:

```
START ?= 20220601
END ?= 20220630
INST ?= "University+of+Texas"
USERLIST ?= "/data/PIs_Afills.xlsx"
OUTPUT ?= "/data/output.xlsx"
```

Run the tool:

```
$ make run
```

Output will be written to the same folder as the input:

```
$ ls /data/
PIs_Afills.xlsx    output.xlsx
```


Input File Format
-----------------

This tool was designed for a very specific purpose, and it was designed to work
in conjunction with another reporting tool (utrc_reports). As it is currently written,
it requires a specific input format which happens to be output from the utrc_reports
tool.

The input must be a spreadsheet (.xlsx) with a tab called `utrc_institution_accounts`.
That tab must have three columns: `root_institution_name`, `first_name`, `last_name`.

Example input might resemble:

| **root_institution_name**             | **first_name** | **last_name** |
|---------------------------------------|:--------------:|---------------|
| University of Texas at Austin         |      John      |      Doe      |
| University of Texas Rio Grande Valley |      Jane      |      Doe      |

The institution name, first name, and last name should appear as they would
appear in the federal grant databases.



NSF Award API
-------------

The NSF Award API scraper works in three steps:

1. First searches all awards by a range of dates and award institution name.
   Note that "University+of+Texas" will actually match all 14 UT System
   institutions. Returns a list of award IDs matching the institution and that
   started within the range of dates.
2. Given the list of award IDs, the search tool then scrapes another NSF API
   that returns award information for each ID including PI names, award
   institution, grant titles, grant amount, etc. in a list of dictionaries
   format.
3. Finally, the tool compares the retrieved results with the input list of PIs
   and affiliations. The output is written to an xlsx sheet with two tabs: (i) 
   awards that match one of the PIs in the input list, and (ii) awards that do
   not match any PIs in the input list.


Note there are some some issues with the way Name matching work. For example the
match will usually fail if a PI has a middle initial listed in the NSF Award
database, but not in the input list. In that case, the award information will end
up in output sheet (ii), the list of awards that does not match any of the input 
PIs / affiliations.


API reference:

https://www.research.gov/common/webapi/awardapisearch-v1.htm


NIH Award API
-------------

*In progress* 


DOE Award API
-------------

*In progress*


