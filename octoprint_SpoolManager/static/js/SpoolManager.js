/*
 * View model for OctoPrint-SpoolManager
 *
 * Author: OllisGit
 * License: AGPLv3
 */
 // START: TESTZONE

 var expanded = false;

function showCheckboxes() {

  var checkboxes = document.getElementById("checkboxes");
  if (!expanded) {
    checkboxes.style.display = "block";
    expanded = true;
  } else {
    checkboxes.style.display = "none";
    expanded = false;
  }
}

var data = [{
   id: 0,
   text: 'enhancement',
	html: '<div class="pick-a-color-markup"><span class="color-preview" style="background-color: rgb(255, 255, 0);"></span>enhancement</div>'
}, {
   id: 1,
   text: 'bug',
	html: '<div style="color:red">bug</div><div><small>This is some small text on a new line</small></div>'
}];

function template(data) {
	return data.html;
}

$("#colorFilter").select2({
   data: data,
   templateResult: template,
   escapeMarkup: function(m) {
      return m;
   }
});



 // END: TESTZONE


$(function() {

    var PLUGIN_ID = "SpoolManager"; // from setup.py plugin_identifier


    ///////////////////////////////////////////////////////////////////////////////////////////////////////// VIEW MODEL
    function SpoolManagerViewModel(parameters) {

        var PLUGIN_ID = "SpoolManager"; // from setup.py plugin_identifier

        var self = this;

        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];
        self.printerStateViewModel = parameters[2];

        self.pluginSettings = null;

        self.apiClient = new SpoolManagerAPIClient(PLUGIN_ID, BASEURL);
        self.spoolDialog = new SpoolManagerEditSpoolDialog();

        // KNOCKOUT - MODLES


//        self.spoolItemForEditing = ko.observable();
//        self.spoolItemForEditing(new SpoolItem(null));
//        self.spoolItemForEditing = self.spoolDialog.createSpoolItemForEditing();

        ////////////////////////////////////////////////////////////////////////////////////////////////HELPER FUNCTION
        // Typs: error
        self.showPopUp = function(popupType, popupTitle, message){
            var title = popupType.toUpperCase() + ": " + popupTitle;
            new PNotify({
                title: title,
                text: message,
                type: popupType,
                hide: false
                });
        };

        ///////////////////////////////////////////////////// START: SETTINGS
        self.databaseFileLocation = ko.observable("hallo");
        self.downloadDatabaseUrl = ko.observable();

        self.deleteDatabaseAction = function() {
            var result = confirm("Do you really want to delete all SpoolManager data?");
            if (result == true){
                self.apiClient.callDeleteDatabase(function(responseData) {
                    self.spoolItemTableHelper.reloadItems();
                });
            }
        };
        ///////////////////////////////////////////////////// END: SETTINGS


        //////////////////////////////////////////////////////////////////////////////////////////////////// SIDEBAR

        self.allSpoolsForSidebar = ko.observableArray([]);
        self.selectedSpoolForSidebar = ko.observable();

        self.loadSpoolsForSidebar = function(){

            tableQuery = {
                filterName: "all",
                from: 0,
                to: 30,
                sortColumn: "lastUse",
                sortOrder: "desc"
            }

            // api-call
            self.apiClient.callLoadSpoolsByQuery(tableQuery, function(responseData){
                allSpoolItems = responseData["allSpools"];

                self.allSpoolsForSidebar(allSpoolItems);
            });
        }

        self.buildSpoolNameForSidebar = function(spoolItem){
            var color = tinycolor(spoolItem.color).toName();
            if (color == false){
                color = "   ";
            }
            var material = spoolItem.material;
            if (!material || material.trim().length === 0){
                material = "   ";
            }

            var displayName = spoolItem.displayName;
            if (!displayName || displayName.trim().length === 0){
                displayName = "   ";
            }

            var label =  color + " - " + material + " - " + displayName;
            return label
        }

        self.spoolChangeByInitialCall = false;
        self.selectedSpoolForSidebar.subscribe(function(newSelectedSpool){

            if (self.spoolChangeByInitialCall == false){
                // api-call
                self.apiClient.callSelectSpool(newSelectedSpool, function(responseData){

                    // check if we need to send a warning
//                    self.showPopUp("warning", "Keine Ahnng", "out off stuff");
    //                totalItemCount = responseData["totalItemCount"];
    //                allSpoolItems = responseData["allSpools"];
    //                catalogs = responseData["catalogs"];
    //                self.spoolDialog.updateCatalogs(catalogs);
    //                templateSpool = responseData["templateSpool"];
                });
            }
            self.spoolChangeByInitialCall = false
        });


        //////////////////////////////////////////////////////////////////////////////////////////////////// TABLE / TAB

        self.addNewSpool = function(){
            self.spoolDialog.showDialog(null, closeDialogHandler);
        }

        ///////////////////////////////////////////////////////////////////////////////////////////////// TABLE BEHAVIOR
        self.spoolItemTableHelper = new TableItemHelper(function(tableQuery, observableTableModel, observableTotalItemCount){
            // api-call
            self.apiClient.callLoadSpoolsByQuery(tableQuery, function(responseData){
                totalItemCount = responseData["totalItemCount"];
                allSpoolItems = responseData["allSpools"];
                catalogs = responseData["catalogs"];
                self.spoolDialog.updateCatalogs(catalogs);
                templateSpool = responseData["templateSpool"];
                self.spoolDialog.updateTemplateSpool(templateSpool);

                var dataRows = ko.utils.arrayMap(allSpoolItems, function (spoolData) {
                    var result = self.spoolDialog.createSpoolItemForTable(spoolData);
                    return result;
                });

                observableTotalItemCount(totalItemCount);
                observableTableModel(dataRows);
            });
            },
            10,
            "displayName",
            "all"
        );


        self.showSpoolDialogAction = function(selectedSpoolItem) {
            self.spoolDialog.showDialog(selectedSpoolItem, closeDialogHandler);
        };

        closeDialogHandler = function(shouldTableReload){
            if (shouldTableReload == true){
                self.spoolItemTableHelper.reloadItems();

                // TODO auto reload of sidebar spools without loosing selection
            }
//
//            if (self.printJobToShowAfterStartup != null){
//                // PrintJob was presented to user and user confirmed
//                self.printJobToShowAfterStartup = null;
//                payload = {
//                    "showPrintJobDialogAfterPrint_jobId": null
//                };
//                OctoPrint.settings.savePluginSettings(PLUGIN_ID, payload);
//            }
        }




        ///////////////////////////////////////////////////////////////////////////////////////// OCTOPRINT PRINT-BUTTON
        const startPrint = self.printerStateViewModel.print;
        self.printerStateViewModel.print = function confirmSpoolSelectionBeforeStartPrint() {

                // api-call
                self.apiClient.allowedToPrint(function(responseData){
                    var result = responseData.result;
                    if ("startPrint" == result){
                        startPrint();
                    } else {
                        if ("noSpoolSelected" == result){
                            var check = confirm('Do you want to start the print without a selected spool?');
                            if (check == true) {
                                startPrint();
                            }
                            return;
                        }
                        if ("noSpoolForUsageCheck" == result){
                            self.showPopUp("Error", "", "No Spool selected for usage check. Select a spool first");
                            return
                        }
                        if ("filamentNotEnough" == result){
                            var check = confirm('Not enough filament. Do you want to start the print anyway?');
                            if (check == true) {
                                startPrint();
                            }
                        }
                    }
                });
        };


        //////////////////////////////////////////////////////////////////////////////////////////////// OCTOPRINT HOOKS
        self.onBeforeBinding = function() {
            // assign current pluginSettings
            self.pluginSettings = self.settingsViewModel.settings.plugins[PLUGIN_ID];

            // resetSettings-Stuff
             new ResetSettingsUtilV2(self.pluginSettings).assignResetSettingsFeature(PLUGIN_ID, function(data){
                // no additional reset function needed in V2
             });

            self.loadSpoolsForSidebar();

            self.spoolDialog.initBinding(self.apiClient, self.pluginSettings);
        }

        self.onAfterBinding = function() {
            self.spoolDialog.afterBinding();
            self.downloadDatabaseUrl(self.apiClient.getDownloadDatabaseUrl());

//            self.spoolDialog.showDialog(null, closeDialogHandler);
        }


        // receive data from server
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin != PLUGIN_ID) {
                return;
            }

            if ("initalData" == data.action){
                self.databaseFileLocation(data.databaseFileLocation);

                var selectedSpoolData = data.selectedSpool;
                if (selectedSpoolData != null){
                    // loop thru the options to pick the right spoolItem-instance
                    selectedDatabaseId = selectedSpoolData.databaseId;
                    selectedSpoolItem = null;
                    ko.utils.arrayForEach(self.allSpoolsForSidebar(), function(spoolItem) {
                        if (spoolItem.databaseId == selectedDatabaseId){
                            selectedSpoolItem = spoolItem;
                        }
                    });
                    self.spoolChangeByInitialCall = true;
                    self.selectedSpoolForSidebar(selectedSpoolItem);
                }
                return;
            }
            if ("showPopUp" == data.action){
                self.showPopUp(data.type, data.title, data.message);
                return;
            }
            if ("reloadTable" == data.action){
                self.spoolItemTableHelper.reloadItems();
                return;
            }


        }

        self.onTabChange = function(next, current){
            //alert("Next:"+next +" Current:"+current);
            if ("#tab_plugin_PrintJobHistory" == next){
                //self.reloadTableData();
            }
        }


    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: SpoolManagerViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [
            "loginStateViewModel",
            "settingsViewModel",
            "printerStateViewModel"
        ],
        // Elements to bind to, e.g. #settings_plugin_SpoolManager, #tab_plugin_SpoolManager, ...
        elements: [
            document.getElementById("settings_spoolmanager"),
            document.getElementById("tab_spoolOverview"),
            document.getElementById("dialog_spool_select"),
            document.getElementById("sidebar_spool_select")
        ]
    });
});
