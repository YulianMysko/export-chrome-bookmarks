# export_bookmarks.py
#
# Python script to export Chrome bookmarks to a text file or spreadsheet.
# Copyright (C) 2021  Yulian Mysko
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import csv
import json
import os.path
import platform
import requests
import sys
import warnings

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

license_string = """
    export_bookmarks.py  Copyright (C) 2021  Yulian Mysko
    This program comes with ABSOLUTELY NO WARRANTY.
    This is free software, and you are welcome to redistribute it
    under certain conditions.\n"""

CHROME_BOOKMARKS_VER = 1


def get_bookmarks_location() -> str:
    """Finds the Chrome bookmarks file in the current OS."""
    location = ""
    # Select the path that corresponds to the current system
    current_system = platform.system()
    if current_system == "Windows":
        location = "~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks"
    elif current_system == "Linux":
        # may also be ~/.config/chromium/Default/Bookmarks
        location = "~/.config/google-chrome/Default/Bookmarks"
    elif current_system == "Darwin":
        # this is macOS
        location = "~/Library/Application Support/Google/Chrome/Default/Bookmarks"
    location = os.path.expanduser(location)
    # Make sure the path is correct
    if not os.path.exists(location) or location == "":
        print(
            "Sorry, the Bookmarks file was not found. Please specify the path manually:\n"
            "  python3 export_bookmarks.py {Your_correct_path}/Bookmarks"
        )
        sys.exit(0)
    return location


def process_children_elements(children: list, folder: str) -> tuple:
    """Extracts every URL in each folder and subfolder.
    
    Args:
        children (list): An array of child elements.
        folder (str): The root folder. Will be recursively expanded with subfolders.
    
    Yields:
        (folder, url_title, url_link)
    
    """
    # 1. For each child in an array of child elements:
    # 2. Return the child if it's a URL,
    #    but if it's a folder - retrieve its children and go to step 1.
    for child in children:
        if child.get("type") == "folder":
            nested_dir = folder + "/" + child.get("name")
            yield from process_children_elements(child.get("children"), nested_dir)
        else:
            yield (
                folder,
                child.get("name"),
                child.get("url"),
            )  # URL should always be the last item!


def process_bookmarks(file_loc: str) -> list:
    """Processes the Bookmarks JSON file.

    Args:
        file_loc (str): Path to the Bookmarks file.

    Returns:
        bookmarks: A list of tuples where each tuple is metadata for a bookmark.

    """
    # Read bookmarks file
    try:
        with open(file_loc, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("Oops! No such file or directory:", file_loc)
        sys.exit(0)
    # Check if the file version is supported
    if data.get("version") != CHROME_BOOKMARKS_VER:
        print(
            'Unfortunately, the current version of the Bookmarks file is "{}", '
            'but the script was designed to work with version "{}"'.format(
                data.get("version"), CHROME_BOOKMARKS_VER
            )
        )
        choice = input("Do you want to proceed [Y/n]? ")
        if choice.lower() not in ["y", "yes"]:
            sys.exit(0)
    # Simplify
    data = data.get("roots")
    # Parse the bookmarks for each root folder and stack them together in one list
    bookmarks = []
    for key in data.keys():
        folder = data[key].get("name")
        bkm_list = list(process_children_elements(data[key].get("children"), folder))
        bookmarks.extend(bkm_list)
    bookmarks.sort(key=lambda x: x[0])
    return bookmarks


# Progress Bar in the Console - by Greenstick on Stack Overflow
# https://stackoverflow.com/a/34325723
def printProgressBar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    printEnd="\r",
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def check_url_status(bookmarks: list) -> list:
    """Sends a HEAD request to check whether the website is online.
    
    Args:
        bookmarks: A list of tuples where each tuple is metadata for a bookmark.
    
    Returns:
        bookmarks: Same list, but the last element is now a website Status."""
    try:
        # super speed
        import asyncio
        import aiohttp
        from aiohttp import ClientSession
    except ImportError:
        # oh crap
        asyncio = None
        aiohttp = None

    if not asyncio and aiohttp:
        
        # Initialize progress bar
        global bkms_count, bkms_checked
        bkms_count = len(bookmarks)
        bkms_checked = 0
        printProgressBar(bkms_checked, bkms_count, prefix="Progress:", suffix="Complete", length=50)
        
        async def get_status(bookmark: str, session: ClientSession, **kwargs) -> str:
            """Checks the website availability."""
            # URL should always be the last item!
            url = bookmark[-1]
            # Check the availability of the URL
            website_status = "Online"
            try:
                resp = await session.head(url=url, ssl=False, **kwargs)
                if resp.status == 404:
                    website_status = "Not found"
                # print(f"Got response [{resp.status}] for URL: {url}")
            except Exception as e:
                website_status = "Failed to check"
                # print("Failed to check URL:", url)
            
            # Update Progress Bar
            global bkms_count, bkms_checked
            bkms_checked += 1
            printProgressBar(bkms_checked, bkms_count, prefix="Progress:", suffix="Complete", length=50)
            
            # Append status to bookmark data and return it
            return bookmark + (website_status,)

        async def make_requests(bookmarks: list, **kwargs) -> list:
            """Async request for each url."""
            timeout = aiohttp.ClientTimeout(total=30)
            async with ClientSession(timeout=timeout) as session:
                tasks = []
                for bkm in bookmarks:
                    tasks.append(get_status(bookmark=bkm, session=session, **kwargs))
                results = await asyncio.gather(*tasks)
                # do something with the results
                return results

        bookmarks = asyncio.run(make_requests(bookmarks))
    else:
        choice = input(
            "It looks like you don't have the aiohttp package installed, so it may take some time to complete the operation without it (a few minutes).\n"
            "To install it (recommended), run in the terminal:\n"
            "  pip3 install aiohttp\n"
            "Do you want to proceed without the aiohttp [Y/n]? "
        )
        if choice.lower() not in ["y", "yes"]:
            return bookmarks
        # Ah, here we go again
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36"
        }
        
        for i, (folder, title, url) in enumerate(bookmarks):
            website_status = "Online"
            # HEAD request to check if a website is online
            try:
                status_code = requests.head(
                    url, headers=headers, verify=False, timeout=5
                ).status_code
                if status_code == 404:
                    website_status = "Not found"
            except requests.exceptions.RequestException as e:
                website_status = "Failed to check"
            bookmarks[i] += (website_status,)
            # Update Progress Bar
            printProgressBar(
                i + 1, len(bookmarks), prefix="Progress:", suffix="Complete", length=50
            )
    not_found = [b[-1] for b in bookmarks].count("Not found")
    print(f'{not_found} links returned "404 Not Found" and therefore may be dead.')
    return bookmarks


def save_csv(output_file: str, bookmarks: list, write_status: bool):
    # Support for Cyrilic
    with open(output_file, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        header = ["Folder", "Title", "URL"]
        if write_status:
            header += ["Status"]
        writer.writerow(header)
        writer.writerows(bookmarks)


def main():
    print(license_string)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bookmarks_file",
        nargs="?",
        default=None,
        help="path to your bookmarks file, can be empty",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="desired output file name, should end with .csv",
        default="exported_bookmarks.csv",
    )
    parser.add_argument(
        "-check-status",
        action="store_true",
        help="additionally check the website status: active/down",
    )
    args = parser.parse_args()

    # get file location
    if args.bookmarks_file is not None:
        file_loc = args.bookmarks_file
    else:
        file_loc = get_bookmarks_location()

    # process file
    bookmarks = process_bookmarks(file_loc)

    # check status if requested
    if args.check_status:
        bookmarks = check_url_status(bookmarks)

    # export
    save_csv(args.output, bookmarks, args.check_status)
    print(f'Success! All bookmarks were exported to the "{args.output}"')


if __name__ == "__main__":
    main()
