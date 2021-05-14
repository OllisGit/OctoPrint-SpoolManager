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
        self.filesViewModel = parameters[3];

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
            var popupId = (title+message).replace(/([^a-z0-9]+)/gi, '-');
            if($("."+popupId).length <1) {
                new PNotify({
                    title: title,
                    text: message,
                    type: popupType,
                    hide: false,
                    addclass: popupId
                });
            }
        };



        // found here: https://stackoverflow.com/questions/19491336/how-to-get-url-parameter-using-jquery-or-plain-javascript?rq=1
        var getUrlParameter = function getUrlParameter(sParam) {
            var sPageURL = window.location.search.substring(1),
                sURLVariables = sPageURL.split('&'),
                sParameterName,
                i;

            for (i = 0; i < sURLVariables.length; i++) {
                sParameterName = sURLVariables[i].split('=');

                if (sParameterName[0] === sParam) {
                    return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
                }
            }
        };


        ///////////////////////////////////////////////////// START: SETTINGS
        self.pluginNotWorking = ko.observable(false);

        self.downloadDatabaseUrl = ko.observable();
        self.databaseConnectionProblemDialog = new DatabaseConnectionProblemDialog();


        self.databaseMetaData = {
            localSchemeVersionFromDatabaseModel: ko.observable(),
            localSpoolItemCount: ko.observable(),
            externalSchemeVersionFromDatabaseModel: ko.observable(),
            externalSpoolItemCount: ko.observable(),
            schemeVersionFromPlugin: ko.observable(),
        }
        self.showSuccessMessage = ko.observable(false);
        self.showDatabaseErrorMessage = ko.observable(false);
        self.showUpdateSchemeMessage = ko.observable(false);
        self.databaseErrorMessage = ko.observable("");
        self.showLocalBusyIndicator = ko.observable(false);
        self.showExternalBusyIndicator = ko.observable(false);

        self.resetDatabaseMessages = function(){
            self.showSuccessMessage(false);
            self.showDatabaseErrorMessage(false);
            self.showUpdateSchemeMessage(false);
            self.databaseErrorMessage("");
        }

        self.handleDatabaseMetaDataResponse = function(metaDataResponse){
            var metadata = metaDataResponse["metadata"];
            if (metadata != null){
                var errorMessage = metadata["errorMessage"];
                if (errorMessage != null && errorMessage.length != 0){
                    self.showDatabaseErrorMessage(true);
                    self.databaseErrorMessage(errorMessage);
                }
                var success = metadata["success"];
                if (success != null && success == true){
                    self.showSuccessMessage(true);
                } else {
                    self.showSuccessMessage(false);
                }

                self.databaseMetaData.localSchemeVersionFromDatabaseModel(metadata["localSchemeVersionFromDatabaseModel"]);
                self.databaseMetaData.localSchemeVersionFromDatabaseModel(metadata["localSchemeVersionFromDatabaseModel"]);
                self.databaseMetaData.localSpoolItemCount(metadata["localSpoolItemCount"]);
                self.databaseMetaData.externalSchemeVersionFromDatabaseModel(metadata["externalSchemeVersionFromDatabaseModel"]);
                self.databaseMetaData.externalSpoolItemCount(metadata["externalSpoolItemCount"]);
                self.databaseMetaData.schemeVersionFromPlugin(metadata["schemeVersionFromPlugin"]);

                if (self.databaseMetaData.schemeVersionFromPlugin() != self.databaseMetaData.externalSchemeVersionFromDatabaseModel()){
                    self.showUpdateSchemeMessage(true);
                }
            }
        }

        self.buildDatabaseSettings = function(){

            var databaseSettings = {
                databaseType: self.pluginSettings.databaseType(),
                databaseHost: self.pluginSettings.databaseHost(),
                databasePort: self.pluginSettings.databasePort(),
                databaseName: self.pluginSettings.databaseName(),
                databaseUser: self.pluginSettings.databaseUser(),
                databasePassword: self.pluginSettings.databasePassword(),
            }
            return databaseSettings
        }

        self.testDatabaseConnection = function(){

            self.resetDatabaseMessages()
            self.showExternalBusyIndicator(true);

//  TODO cleanup          var databaseSettings = {
//                databaseType: self.pluginSettings.databaseType(),
//                databaseHost: self.pluginSettings.databaseHost(),
//                databasePort: self.pluginSettings.databasePort(),
//                databaseName: self.pluginSettings.databaseName(),
//                databaseUser: self.pluginSettings.databaseUser(),
//                databasePassword: self.pluginSettings.databasePassword(),
//            }
            var databaseSettings = self.buildDatabaseSettings();
            // api-call
            self.apiClient.testDatabaseConnection(databaseSettings, function(responseData){
                self.handleDatabaseMetaDataResponse(responseData);
                self.showExternalBusyIndicator(false);
            });
        }

        self.deleteDatabaseAction = function(databaseType) {
            var result = confirm("Do you really want to delete all SpoolManager data?");
            if (result == true){
//  TODO cleanup
//                var databaseSettings = {
//                    databaseType: self.pluginSettings.databaseType(),
//                    databaseHost: self.pluginSettings.databaseHost(),
//                    databasePort: self.pluginSettings.databasePort(),
//                    databaseName: self.pluginSettings.databaseName(),
//                    databaseUser: self.pluginSettings.databaseUser(),
//                    databasePassword: self.pluginSettings.databasePassword(),
//                }
                var databaseSettings = self.buildDatabaseSettings();
                self.apiClient.callDeleteDatabase(databaseType, databaseSettings, function(responseData) {
                    self.spoolItemTableHelper.reloadItems();
                });
            }
        };

        $("#spoolmanger-settings-tab").find('a[data-toggle="tab"]').on('shown', function (e) {

              var activatedTab = e.target.hash; // activated tab
              var prevTab = e.relatedTarget.hash; // previous tab

              if ("#tab-spool-Storage" == activatedTab){
                  self.resetDatabaseMessages()

                  self.showLocalBusyIndicator(true);
                  self.showExternalBusyIndicator(true);
                  self.apiClient.loadDatabaseMetaData(function(responseData) {
                        self.handleDatabaseMetaDataResponse(responseData);
                        self.showLocalBusyIndicator(false);
                        self.showExternalBusyIndicator(false);
                   });
              }
        });

        self.isFilamentManagerPluginAvailable = ko.observable(false);

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

        // overwrite save-button
        const origSaveSettingsFunction = self.settingsViewModel.saveData;
        const newSaveSettingsFunction = function confirmSpoolSelectionBeforeStartPrint(data, successCallback, setAsSending) {
            if (self.pluginSettings.useExternal() == true &&
                (self.showDatabaseErrorMessage() == true || self.showUpdateSchemeMessage() == true)
                ){
                var check = confirm('External database will not work. Save settings anyway?');
                if (check == true) {
                    return origSaveSettingsFunction(data, successCallback, setAsSending);
                }
                return null;
            }
            return origSaveSettingsFunction(data, successCallback, setAsSending);
        }
        self.settingsViewModel.saveData = newSaveSettingsFunction;

        ///////////////////////////////////////////////////// END: SETTINGS


        //////////////////////////////////////////////////////////////////////////////////////////////////// SIDEBAR

        self.allSpoolsForSidebar = ko.observableArray([]);
        self.selectedSpoolForSidebar = ko.observable();
        self.selectedSpoolsForSidebar = ko.observableArray([]);
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
            if (self.pluginSettings!= null){
                 if(self.pluginSettings.hideEmptySpoolsInSidebar() == true) {
                     currentFilterName = "hideEmptySpools";
                 }
                 if(self.pluginSettings.hideInactiveSpoolsInSidebar() == true) {
                     currentFilterName = "hideInactiveSpools";
                 }
                 if(self.pluginSettings.hideEmptySpoolsInSidebar() == true && self.pluginSettings.hideInactiveSpoolsInSidebar() == true) {
                     currentFilterName = "hideEmptySpools,hideInactiveSpools";
                 }
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
                if (allSpoolData != null){
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
                }
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


        var TableAttributeVisibility = function (){
            this.displayName = ko.observable(true);
            this.material = ko.observable(true);
            this.lastFirstUse = ko.observable(true);
            this.weight = ko.observable(true);
            this.used = ko.observable(true);
            this.note = ko.observable(true);
        }
        self.tableAttributeVisibility = new TableAttributeVisibility();

        self.initTableVisibilities = function(){
            // load all settings from browser storage
            if (!Modernizr.localstorage) {
                // damn!!!
                return false;
            }

            assignVisibility = function(attributeName){
                var storageKey = "spoolmanager.table.visible." + attributeName;
                if (localStorage[storageKey] == null){
                    localStorage[storageKey] = true
                } else {
                    self.tableAttributeVisibility[attributeName]( "true" == localStorage[storageKey]);
                }
                self.tableAttributeVisibility[attributeName].subscribe(function(newValue){
                    localStorage[storageKey] = newValue;
                });
            }

            assignVisibility("displayName");
            assignVisibility("material");
            assignVisibility("lastFirstUse");
            assignVisibility("weight");
            assignVisibility("used");
            assignVisibility("note");
        }

        ///////////////////////////////////////////////////////////////////////////////////////////////// TABLE BEHAVIOR
        self.spoolItemTableHelper = new TableItemHelper(function(tableQuery, observableTableModel, observableTotalItemCount){
            // api-call
            self.apiClient.callLoadSpoolsByQuery(tableQuery, function(responseData){

                if (responseData["databaseConnectionProblem"] != null && responseData["databaseConnectionProblem"] == true){
                    self.pluginNotWorking(true);
                } else {
                    self.pluginNotWorking(false);
                }

                totalItemCount = responseData["totalItemCount"];
                allSpoolItems = responseData["allSpools"];
                catalogs = responseData["catalogs"];
                self.spoolDialog.updateCatalogs(catalogs);
                templateSpoolData = responseData["templateSpool"];
                self.spoolDialog.updateTemplateSpool(templateSpoolData);

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

        closeDialogHandler = function(shouldTableReload, specialAction, currentSpoolItem){

            if (specialAction === "selectSpoolForPrinting"){
                self.selectSpoolForSidebar(currentSpoolItem);
            }

            if (shouldTableReload == true){
                self.spoolItemTableHelper.reloadItems();
                // TODO auto reload of sidebar spools without loosing selection
                self.loadSpoolsForSidebar();
            }
        }


        ///////////////////////////////////////////////////////////////////////////////////////// OCTOPRINT PRINT-BUTTON
        const origStartPrintFunction = self.printerStateViewModel.print;
        const newStartPrintFunction = function confirmSpoolSelectionBeforeStartPrint() {
                // api-call
                self.apiClient.allowedToPrint(function(responseData){
                    var result = responseData.result;
                    if ("startPrint" == result){
                        origStartPrintFunction();
                    } else {
                        if ("noSpoolSelected" == result){
                            var check = confirm('Do you want to start the print without a selected spool?');
                            if (check == true) {
                                origStartPrintFunction();
                            }
                            return;
                        }
//                        Not needed because a length check is only done, if spool was selected
//                        if ("noSpoolForUsageCheck" == result){
//                            self.showPopUp("Error", "", "No Spool selected for usage check. Select a spool first");
//                            return;
//                        }
                        if ("filamentNotEnough" == result){
                            var check = confirm("The selected spool '"+responseData.spoolName+"' does not have enough remaining filament. Do you want to start the print anyway?");
                            if (check == true) {
                                origStartPrintFunction();
                            }
                            return;
                        }
                        if ("reminderSpoolSelection" == result){
                            var question = "Do you want to start the print with the selected spool '"+responseData.spoolName+"'?";
                            var check = confirm(question);
                            if (check == true) {
                                origStartPrintFunction();
                            }
                        }
                    }
                });
        };

        self.filesViewModel.loadFile = function confirmSpoolSelectionOnLoadAndPrint(data, printAfterLoad) {
            // orig. SourceCode
            if (!self.filesViewModel.loginState.hasPermission(self.filesViewModel.access.permissions.FILES_SELECT)) return;

            if (!data) {
                return;
            }

            if (printAfterLoad && self.filesViewModel.listHelper.isSelected(data) && self.filesViewModel.enablePrint(data)) {
                // file was already selected, just start the print job with the newStartPrint function
                // SPOOLMANAGER-CHANGE changed OctoPrint.job.start();
                newStartPrintFunction();
            } else {
                // select file, start print job (if requested and within dimensions)
                var withinPrintDimensions = self.filesViewModel.evaluatePrintDimensions(data, true);
                var print = printAfterLoad && withinPrintDimensions;

                if (print && self.filesViewModel.settingsViewModel.feature_printStartConfirmation()) {
                    showConfirmationDialog({
                        message: gettext("This will start a new print job. Please check that the print bed is clear."),
                        question: gettext("Do you want to start the print job now?"),
                        cancel: gettext("No"),
                        proceed: gettext("Yes"),
                        onproceed: function() {
                            OctoPrint.files.select(data.origin, data.path, false).done(function () {
                                                                                    if (print){
                                                                                     newStartPrintFunction();
                                                                                    }
                                                                                });
                        },
                        nofade: true
                    });
                } else {
                    OctoPrint.files.select(data.origin, data.path, false).done(function () {
                                                                                    if (print){
                                                                                     newStartPrintFunction();
                                                                                    }
                                                                                });
                }
            }
        };


        self.printerStateViewModel.print = newStartPrintFunction;

        //////////////////////////////////////////////////////////////////////////////////////////////// OCTOPRINT HOOKS
        self.onBeforeBinding = function() {
            // assign current pluginSettings
            self.pluginSettings = self.settingsViewModel.settings.plugins[PLUGIN_ID];
            // Table visibility
            self. initTableVisibilities();
            // resetSettings-Stuff
             new ResetSettingsUtilV3(self.pluginSettings).assignResetSettingsFeature(PLUGIN_ID, function(data){
                // no additional reset function needed in V2
             });

            // Load all Spools
            self.loadSpoolsForSidebar();
            // Edit Dialog Binding
            self.spoolDialog.initBinding(self.apiClient, self.pluginSettings);
            // Import Dialog
            self.csvImportDialog.init(self.apiClient);
            // Database connection problem dialog
            self.databaseConnectionProblemDialog.init(self.apiClient);

            self.pluginSettings.hideEmptySpoolsInSidebar.subscribe(function(newCheckedVaue){
                var payload = {
                        "hideEmptySpoolsInSidebar": newCheckedVaue
                    };
                OctoPrint.settings.savePluginSettings(PLUGIN_ID, payload);
                self.loadSpoolsForSidebar();
            });
            self.pluginSettings.hideInactiveSpoolsInSidebar.subscribe(function(newCheckedVaue){
                var payload = {
                        "hideInactiveSpoolsInSidebar": newCheckedVaue
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

                self.pluginNotWorking(data.pluginNotWorking);
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

            if ("reloadTable and sidebarSpools" == data.action){
                self.spoolItemTableHelper.reloadItems();
                self.loadSpoolsForSidebar();
                return;
            }

            if ("csvImportStatus" == data.action){
                self.csvImportDialog.updateText(data);
                return;
            }
            if ("errorPopUp" == data.action){
                self.showPopUp("error", 'ERROR:' + data.title, data.message);
                return;
            }
            if ("showConnectionProblem" == data.action){
// TODO enable problem dialog again
//                new PNotify({
//                    title: 'ERROR:' + data.title,
//                    text: data.message,
//                    type: "error",
//                    hide: false
//                    });

//                self.databaseConnectionProblemDialog.showDialog(data, function(){
//                    // nothing special here, everything is done in the dialog
//                });

                return;
            }

        }

        self.onTabChange = function(next, current){
            //alert("Next:"+next +" Current:"+current);
            // debugger
            if ("#tab_plugin_PrintJobHistory" == next){
                //self.reloadTableData();
            }
        }
        self.onAfterTabChange = function(current, previous){
            //alert("Next:"+next +" Current:"+current);
            //if ("#tab_plugin_SpoolManager" == current){
            // var selectedSpoolId = getUrlParameter("selectedSpoolId");
            // if (selectedSpoolId) {
            //     console.error("Id"+selectedSpoolId);
            // }
            var tabHashCode = window.location.hash;
            //we can only contain -spoolId on the very first page
            if (tabHashCode.includes("#tab_plugin_SpoolManager-spoolId")){
                var selectedSpoolId = tabHashCode.replace("-spoolId", "").replace("#tab_plugin_SpoolManager", "");
                console.info('Loading spool: '+selectedSpoolId);
                // - Load SpoolItem from Backend
                // - Open SpoolItem
                self.apiClient.callSelectSpool(selectedSpoolId, function(responseData){
                    //Select the SpoolManager tab
                    $('a[href="#tab_plugin_SpoolManager"]').tab('show')
                    var spoolItem = null;
                    var spoolData = responseData["selectedSpool"];
                    if (spoolData != null){
                        self.selectedSpoolForSidebar(spoolItem);
                        spoolItem = self.spoolDialog.createSpoolItemForTable(spoolData);
                        spoolItem.selectedFromQRCode(true);
                        self.showSpoolDialogAction(spoolItem);
                    }
                });
            }
            //}
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
            "printerStateViewModel",
            "filesViewModel"
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
