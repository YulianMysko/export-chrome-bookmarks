# Export Chrome Bookmarks
Python script to export Chrome bookmarks to a text file [csv] or spreadsheet [xlsx].

## Dependencies
- All code is written in [Python 3](https://www.python.org/downloads/).
- Some code depends on the [aiohttp](https://docs.aiohttp.org/en/stable/) library (optional).

## How To Use
To clone and run this application, you'll need Git and Python 3 installed on your computer.  
Run from the terminal:
```
# To automatically export bookmarks:
python3 export_bookmarks.py

# To automatically export bookmarks AND check the status of URLs (active/down):
python3 export_bookmarks.py -check-status

# To provide optional input/output files
python3 export_bookmarks.py ~/Chrome/Default/Bookmarks --output ./my_bookmarks.csv
```

To install the [aiohttp](https://docs.aiohttp.org/en/stable/) library run from the terminal:
```
pip3 install aiohttp
```

## License
This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
