# fb2-cleaner

Usage: fb2_clean.py [-h] [-b BOOK] [-f FOLDER] [-s] [-z] [-r] [-i] [-c] [-t]
                    [-n] [-v] [-d]

Optional arguments:
  -b BOOK, --book BOOK  handle one book
  -f FOLDER, --folder FOLDER
                        folder for search books (without subfolders)
  -s, --subfolders      enable search in subfolders

  -z, --zip             enable result compression
  -r, --remove          enable removal original file

  -i, --ID              enable generation book's ID if exist
  -c, --clean           enable removal incorrect tags
  -t, --tabulation      enable alignment indentation

  -n, --name            enable renaming book

  -v, --validation      validation only, without writing any changes

  -d, --details         enable display details during work

Example: fb2_clean.py -f=/home/user/Books -s -r -i -c -t -d
