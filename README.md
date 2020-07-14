# OctoPrint-SpoolManager

# WORK IN PROGRESS!!!! 

The OctoPrint-Plugin manages all spool informations and stores it in a database

#### Current implementation for Plugin-Manager URL: 
    
    https://github.com/OllisGit/OctoPrint-SpoolManager/... not released yet!!!

#### Support my Efforts

This plugin, as well as my [other plugins](https://github.com/OllisGit/) were developed in my spare time.
If you like it, I would be thankful about a cup of coffee :) 

[![More coffee, more code](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=2BJP2XFEKNG9J&source=url)

## Planning Release #1
 
should include the following features:

### Basic attributes to be captured:
- [ ] Spool basic attributes, like name,  color, material, ...
- [ ] "Used length" and "Remaining weight" will be set by [OctorPrint-PrintJobHistory - Plugin](https://github.com/OllisGit/OctoPrint-PrintJobHistory)
- [ ] Additional notes
- [ ] Labels
- [ ] Scan QR/Barcodes of a spool

### UI features
- [ ] Better error-feedback (more then just the "happy-path")
- [ ] List all printjobs
- [ ] Edit single printjob
- [ ] Capture Spool-Image
- [ ] Export all spool informations as CSV
- [ ] Filter spool table  (?)
- [ ] Sort spool table (?)

### Not included
- No adjustment settings (e.g ???)
- No fancy looking UI

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

* Date-Picker: 
~~bootstrap-datapicker https://github.com/uxsolutions/bootstrap-datepicker~~
datepicker https://github.com/fengyuanchen/datepicker


Select/Labels
select2 https://select2.org/

WYSIWYG - Editor
quill https://quilljs.com/
