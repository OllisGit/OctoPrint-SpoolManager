# OctoPrint-SpoolManager

[![Version](https://img.shields.io/badge/dynamic/json.svg?color=brightgreen&label=version&url=https://api.github.com/repos/OllisGit/OctoPrint-SpoolManager/releases&query=$[0].name)]()
[![Released](https://img.shields.io/badge/dynamic/json.svg?color=brightgreen&label=released&url=https://api.github.com/repos/OllisGit/OctoPrint-SpoolManager/releases&query=$[0].published_at)]()
![GitHub Releases (by Release)](https://img.shields.io/github/downloads/OllisGit/OctoPrint-SpoolManager/latest/total.svg)

# Release candidate 1 is out!

The OctoPrint-Plugin manages all spool informations and stores it in a database.

#### Support my Efforts

This plugin, as well as my [other plugins](https://github.com/OllisGit/) were developed in my spare time.
If you like it, I would be thankful about a cup of coffee :)

[![More coffee, more code](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=6SW5R6ZUKLB5E&source=url)

## Planning Release #1

should include the following features:

### Basic attributes to be captured:
- [X] Spool basic attributes, like name,  color, material, vendor ...
- [X] "Used length" and "Remaining weight"
- [X] Additional notes
- [ ] Labels

### UI features
- [X] Better error-feedback (more then just the "happy-path")
- [X] List all spools
- [X] Edit single spool
- [X] Copy single spool
- [X] Template spool
- [X] Sort spool table (Displayname, Last/First use)
- [X] Force to select a spool before printing
- [ ] Filter spool table

## Planning Release #2

- [ ] Table column visibity
- [ ] Capture Spool-Image
- [ ] Scan QR/Barcodes of a spool
- [ ] CSV Export function
- [ ] CSV Import function
- [ ] Multi Tool support


## Screenshots
<!---
![plugin-settings](screenshots/plugin-settings.png "Plugin-Settings")
![plugin-tab](screenshots/plugin-tab.png "Plugin-Tab")
-->
![listSpools-tab](screenshots/listSpools-tab.png "ListSpools-Tab")
![editSpool-dialog](screenshots/editSpool-dialog.png "EditSpool-Dialog")
![scanSpool-dialog](screenshots/scanSpool-dialog.png "ScanSpool-Dialog")


## Setup

Plugin is in "working-mode" and not released in official OctoPrint Plugin-Repository.
You need to install it manually using this URL:

    https://github.com/OllisGit/OctoPrint-SpoolManager/releases/latest/download/master.zip


## Versions

see [Release-Overview](https://github.com/OllisGit/OctoPrint-SpoolManager/releases/)

---

### Used UI-Tools
* Color-Picker:
Pick-a-Color https://github.com/lauren/pick-a-color/
* Color Helper:
https://github.com/bgrins/TinyColor
* Date-Picker:
~~bootstrap-datapicker https://github.com/uxsolutions/bootstrap-datepicker~~
datepicker https://github.com/fengyuanchen/datepicker

* datetimepicker
 https://github.com/xdan/datetimepicker/tree/2.5.20
https://www.jqueryscript.net/time-clock/Clean-jQuery-Date-Time-Picker-Plugin-datetimepicker.html

* Select/Labels
select2 https://select2.org/

* WYSIWYG - Editor
quill https://quilljs.com/
