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
        self.isFilamentManagerPluginAvailable = ko.observable(false);

        self.databaseFileLocation = ko.observable("hello");
        self.downloadDatabaseUrl = ko.observable();

        self.deleteDatabaseAction = function() {
            var result = confirm("Do you really want to delete all SpoolManager data?");
            if (result == true){
                self.apiClient.callDeleteDatabase(function(responseData) {
                    self.spoolItemTableHelper.reloadItems();
                });
            }
        };

        // - Import CSV
        self.csvFileUploadName = ko.observable();
        self.csvImportInProgress = ko.observable(false);

        self.csvImportDialog = new SpoolManagerImportDialog();
        self.csvImportUploadButton = $("#settings-spool-importcsv-upload");
        self.csvImportUploadData = undefined;
        self.csvImportUploadButton.fileupload({
            dataType: "json",
            maxNumberOfFiles: 1,
            autoUpload: false,
            headers: OctoPrint.getRequestHeaders(),
            add: function(e, data) {
                if (data.files.length === 0) {
                    // no files? ignore
                    return false;
                }
                self.csvFileUploadName(data.files[0].name);
                self.csvImportUploadData = data;
            },
            done: function(e, data) {
                self.csvImportInProgress(false);
                self.csvFileUploadName(undefined);
                self.csvImportUploadData = undefined;
            },
            error: function(response, data, errorMessage){
                self.csvImportInProgress(false);
                statusCode = response.status;       // e.g. 400
                statusText = response.statusText;   // e.g. BAD REQUEST
                responseText = response.responseText; // e.g. Invalid request
            }
        });

        self.performCSVImportFromUpload = function() {
            if (self.csvImportUploadData === undefined) return;

            self.csvImportInProgress(true);
            self.csvImportDialog.showDialog(function(shouldTableReload){
                    //
                    if (shouldTableReload == true){
                        self.spoolItemTableHelper.reloadItems();
                    }
                }
            );
            self.csvImportUploadData.submit();
        };

        ///////////////////////////////////////////////////// END: SETTINGS


        //////////////////////////////////////////////////////////////////////////////////////////////////// SIDEBAR

        self.allSpoolsForSidebar = ko.observableArray([]);
        self.selectedSpoolForSidebar = ko.observable();
        self.selectedSpoolText = ko.observable();


        self.selectedSpoolForSidebar.subscribe(function(newSelectedSpool){

            var selectSpoolText = _buildSpoolLabel(newSelectedSpool);
            self.selectedSpoolText(selectSpoolText)

        });


        self.deselectSpoolsForSidebar = function(){
            self.selectedSpoolForSidebar(null);
            self.selectSpoolForSidebar(null);
        }

        self.loadSpoolsForSidebar = function(){
            var currentFilterName = "all";
            if (self.pluginSettings!= null && self.pluginSettings.hideEmptySpoolsInSidebar() == true){
                currentFilterName = "hideEmptySpools";
            }

            var tableQuery = {
                filterName: currentFilterName,
                from: 0,
                to: 3000,
                sortColumn: "lastUse",
                sortOrder: "desc"
            }

            // api-call
            self.apiClient.callLoadSpoolsByQuery(tableQuery, function(responseData){
                var allSpoolData = responseData["allSpools"]; // rawdtata

                var allSpoolItems = ko.utils.arrayMap(allSpoolData, function (spoolData) {
                    var result = self.spoolDialog.createSpoolItemForTable(spoolData);
                    return result;
                }); // transform to SpoolItems with KO.obseravables
                self.allSpoolsForSidebar(allSpoolItems);

                var spoolItem = null;
                var spoolData = responseData["selectedSpool"];
                if (spoolData != null){
                    spoolItem = self.spoolDialog.createSpoolItemForTable(spoolData);
                }
                self.selectedSpoolForSidebar(spoolItem)
            });
        }

        // helper for create a Label for a Spool (Color-Box, Material, ...)
        _buildSpoolLabel = function(spoolItem){
            var spoolLabel = "No Spool selected!";
            if (spoolItem != null){
                spoolLabel = '<span class="color-preview" style="background-color: '+spoolItem.color()+';" title="'+spoolItem.colorName()+'"></span>';
                var remainingInfo = _buildRemainingText(spoolItem);
                spoolLabel += '<span style="vertical-align:super">'+spoolItem.material()+'-'+spoolItem.displayName()+' '+remainingInfo+'</span>'
            }
            return spoolLabel;
        }

        _buildRemainingText = function(spoolItem){
            var remainingInfo = "";
            if (  spoolItem.remainingWeight() != null && spoolItem.remainingWeight().length != 0
                && spoolItem.remainingPercentage() != null && spoolItem.remainingPercentage().length != 0){
                remainingInfo = "("+spoolItem.remainingWeight()+"g / "+spoolItem.remainingPercentage()+"%)";
            }
            return remainingInfo
        }

        self.remainingText = function(spoolItem){
            var remainingInfo = _buildRemainingText(spoolItem);
            return remainingInfo;
        }

        self.selectSpoolForSidebar = function(spoolItem){
            // api-call
            var databaseId = -1
            if (spoolItem != null){
                databaseId = spoolItem.databaseId();
            }
            self.apiClient.callSelectSpool(databaseId, function(responseData){
                    // check if we need to send a warning
//                    self.showPopUp("warning", "Keine Ahnng", "out off stuff");

                var spoolItem = null;
                var spoolData = responseData["selectedSpool"];
                if (spoolData != null){
                    spoolItem = self.spoolDialog.createSpoolItemForTable(spoolData);
                }
                self.selectedSpoolForSidebar(spoolItem)
            });
        }

        self.editSpoolFromSidebar = function(){
            if (self.selectedSpoolForSidebar() == null){
                alert("Something is wrong. No Spool is selected to edit from sidebar!")
            }

            var spoolItem = self.selectedSpoolForSidebar();
            self.showSpoolDialogAction(spoolItem);
        }

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
                self.loadSpoolsForSidebar();
            }
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
//                        Not needed because a length check is only done, if spool was selected
//                        if ("noSpoolForUsageCheck" == result){
//                            self.showPopUp("Error", "", "No Spool selected for usage check. Select a spool first");
//                            return;
//                        }
                        if ("filamentNotEnough" == result){
                            var check = confirm('Not enough filament. Do you want to start the print anyway?');
                            if (check == true) {
                                startPrint();
                            }
                            return;
                        }
                        if ("reminderSpoolSelection" == result){
                            var question = "Please verify your selected Spool '"+responseData.spoolName+"'. Do you want to start the print anyway?";
                            var check = confirm(question);
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

            // Load all Spools
            self.loadSpoolsForSidebar();
            // Edit Dialog Binding
            self.spoolDialog.initBinding(self.apiClient, self.pluginSettings);
            // Import Dialog
            self.csvImportDialog.init(self.apiClient);

            self.pluginSettings.hideEmptySpoolsInSidebar.subscribe(function(newCheckedVaue){
                var payload = {
                        "hideEmptySpoolsInSidebar": newCheckedVaue
                    };
                OctoPrint.settings.savePluginSettings(PLUGIN_ID, payload);
                self.loadSpoolsForSidebar();
            });
        }

        self.onAfterBinding = function() {
            self.spoolDialog.afterBinding();
            self.downloadDatabaseUrl(self.apiClient.getDownloadDatabaseUrl());

// testing            self.spoolDialog.showDialog(null, closeDialogHandler);
        }

        self.onSettingsShown = function(){
            if (self.isFilamentManagerPluginAvailable() == false){
                self.apiClient.callAdditionalSettings(function(responseData) {
                    self.isFilamentManagerPluginAvailable(responseData.isFilamentManagerPluginAvailable);
                });
            }
        }
        // receive data from server
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin != PLUGIN_ID) {
                return;
            }

            if ("initalData" == data.action){
                self.databaseFileLocation(data.databaseFileLocation);

                self.isFilamentManagerPluginAvailable(data.isFilamentManagerPluginAvailable);

                var selectedSpoolData = data.selectedSpool;
                if (selectedSpoolData != null){
                    var selectedSpoolItem = self.spoolDialog.createSpoolItemForTable(selectedSpoolData);
                    self.selectedSpoolForSidebar(selectedSpoolItem);
                } else {
                    self.selectedSpoolForSidebar(null);
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

            if ("csvImportStatus" == data.action){
                self.csvImportDialog.updateText(data);
                return;
            }
            if ("errorPopUp" == data.action){
                new PNotify({
                    title: 'ERROR:' + data.title,
                    text: data.message,
                    type: "error",
                    hide: false
                    });

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
            document.getElementById("modal-dialogs-spoolManager"),
            document.getElementById("sidebar_spool_select")
        ]
    });
});
