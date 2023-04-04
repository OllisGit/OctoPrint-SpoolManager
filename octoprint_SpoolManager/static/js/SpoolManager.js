/*
 * View model for OctoPrint-SpoolManager
 *
 * Author: OllisGit
 * License: AGPLv3
 */
// from setup.py plugin_identifier
const PLUGIN_ID = "SpoolManager";
const WEIGHT_UNIT_SYMBOL = "g";

const buildSpoolLabel = (item) => {
    const remainingWeightInfo = (
        (
            item.remainingWeight != null &&
            typeof item.remainingWeight === 'number'
        )
            ? `(${item.remainingWeight.toFixed(2)} ${WEIGHT_UNIT_SYMBOL})`
            : undefined
    );

    const basicInfo = `${item.material} - ${item.spoolName}`;
    const label = `${item.toolIndex}: '${basicInfo}${remainingWeightInfo ? ` ${remainingWeightInfo}` : ''}'`;

    return label;
};

$(function() {
    ///////////////////////////////////////////////////////////////////////////////////////////////////////// VIEW MODEL
    function SpoolManagerViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];
        self.printerStateViewModel = parameters[2];
        self.filesViewModel = parameters[3];
        self.printerProfilesViewModel = parameters[4];

        self.pluginSettings = null;

        self.apiClient = new SpoolManagerAPIClient(PLUGIN_ID, BASEURL);
        self.spoolDialog = new SpoolManagerEditSpoolDialog();


        //////////////////////////////////////////////////////////////////////////////////////////////// HELPER FUNCTION

        loadSettingsFromBrowserStore = function(){
            // TODO maybe in a separate js-file
            // load all settings from browser storage
            if (!Modernizr.localstorage) {
                // damn!!!
                return false;
            }
            // Table visibility
            self.initTableVisibilities();

            var storageKey = "spoolmanager.table.selectedPageSize";
            if (localStorage[storageKey] == null){
                localStorage[storageKey] = "25"; // default page size
            } else {
                self.spoolItemTableHelper.selectedPageSize(localStorage[storageKey]);
            }
            self.spoolItemTableHelper.selectedPageSize.subscribe(function(newValue){
                localStorage[storageKey] = newValue;
            });
        }

        // Typs: error
        self.showPopUp = function(popupType, popupTitle, message, autoclose){
            var title = popupType.toUpperCase() + ": " + popupTitle;
            var popupId = (title+message).replace(/([^a-z0-9]+)/gi, '-');
            if($("."+popupId).length <1) {
                new PNotify({
                    title: "SPM:" + title,
                    text: message,
                    type: popupType,
                    hide: autoclose,
                    addclass: popupId
                });
            }
        };

        self.reloadQRCodePreviewImage = function(){
            var imageDom = $("#settings-qrimage-preview");
            var currentSrc = imageDom.attr("src");
            currentSrc = currentSrc + "&"+new Date().getTime();
            imageDom.attr("src", currentSrc);
        }

        // Generate HTML-Image Attributes for the QR-Code
        self.generateQRCodeImageSourceAttribute = function(databaseId, spoolDisplayName, showHtmlView, withColors){
            var requestParameters = "";
            if (withColors){
                requestParameters = "?" +
                                    "fillColor=" + encodeURIComponent(self.pluginSettings.qrCodeFillColor()) + "&" +
                                    "backgroundColor=" + encodeURIComponent(self.pluginSettings.qrCodeBackgroundColor());

                if (self.pluginSettings.qrCodeUseURLPrefix() == true){
                    requestParameters = requestParameters + "&" +
                        "useURLPrefix=true" + "&" +
                        "urlPrefix=" + encodeURIComponent(self.pluginSettings.qrCodeURLPrefix())
                }
            }

            var source = "";
            if (showHtmlView == "htmlView"){
                source = PLUGIN_BASEURL + "SpoolManager/generateQRCodeView/" + databaseId + "" + requestParameters;
            } else {
                source = PLUGIN_BASEURL + "SpoolManager/generateQRCode/" + databaseId+ "" + requestParameters;
            }
            var title = "QR-Code for " + spoolDisplayName;
            return {
                src: source,
                href: source,
                title: title
            }
        }

        ///////////////////////////////////////////////////// START: SETTINGS
        self.pluginNotWorking = ko.observable(undefined);

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

        self.handleDatabaseMetaDataResponse = function(metaDataResponse) {
            const metadata = metaDataResponse.metadata;

            if (metadata == null) {
                return;
            }

            const errorMessage = metadata.errorMessage;
            if (errorMessage != null && errorMessage.length != 0) {
                self.showDatabaseErrorMessage(true);
                self.databaseErrorMessage(errorMessage);
            }
            const success = metadata.success;
            const successMessageFlag = (success != null && success == true) ? true : false;

            self.showSuccessMessage(successMessageFlag);

            self.databaseMetaData.localSchemeVersionFromDatabaseModel(metadata.localSchemeVersionFromDatabaseModel);
            self.databaseMetaData.localSchemeVersionFromDatabaseModel(metadata.localSchemeVersionFromDatabaseModel);
            self.databaseMetaData.localSpoolItemCount(metadata.localSpoolItemCount);
            self.databaseMetaData.externalSchemeVersionFromDatabaseModel(metadata.externalSchemeVersionFromDatabaseModel);
            self.databaseMetaData.externalSpoolItemCount(metadata.externalSpoolItemCount);
            self.databaseMetaData.schemeVersionFromPlugin(metadata.schemeVersionFromPlugin);

            if (self.databaseMetaData.schemeVersionFromPlugin() != self.databaseMetaData.externalSchemeVersionFromDatabaseModel()) {
                self.showUpdateSchemeMessage(true);
            }
        }

        self.buildDatabaseSettings = function() {
            return {
                databaseType: self.pluginSettings.databaseType(),
                databaseHost: self.pluginSettings.databaseHost(),
                databasePort: self.pluginSettings.databasePort(),
                databaseName: self.pluginSettings.databaseName(),
                databaseUser: self.pluginSettings.databaseUser(),
                databasePassword: self.pluginSettings.databasePassword(),
            }
        }

        self.testDatabaseConnection = function() {
            self.resetDatabaseMessages()
            self.showExternalBusyIndicator(true);

            const databaseSettings = self.buildDatabaseSettings();

            self.apiClient.testDatabaseConnection(databaseSettings, function(responseData) {
                self.handleDatabaseMetaDataResponse(responseData);
                self.showExternalBusyIndicator(false);
            });
        }

        self.deleteDatabaseAction = function(databaseType) {
            const confirmationResult = confirm("Do you really want to delete all SpoolManager data?");

            if (!confirmationResult) {
                return;
            }

            const databaseSettings = self.buildDatabaseSettings();

            self.apiClient.callDeleteDatabase(databaseType, databaseSettings, function(responseData) {
                self.spoolItemTableHelper.reloadItems();
            });
        };

        $("#spoolmanger-settings-tab")
            .find('a[data-toggle="tab"]')
            .on('shown', function (evt) {
                const activatedTab = evt.target.hash;
                const prevTab = evt.relatedTarget.hash;

                if ("#tab-spool-Storage" != activatedTab) {
                    return;
                }

                self.resetDatabaseMessages()
                self.showLocalBusyIndicator(true);
                self.showExternalBusyIndicator(true);
                self.apiClient.loadDatabaseMetaData(function(responseData) {
                    self.handleDatabaseMetaDataResponse(responseData);
                    self.showLocalBusyIndicator(false);
                    self.showExternalBusyIndicator(false);
                });
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
            if (self.csvImportUploadData === undefined) {
                return;
            }

            self.csvImportInProgress(true);
            self.csvImportDialog.showDialog(function(shouldTableReload) {
                if (shouldTableReload == true) {
                    self.spoolItemTableHelper.reloadItems();
                }
            });
            self.csvImportUploadData.submit();
        };

        // template stuff
        self.checkExcludedFromTemplateCopy = function(fieldName) {
            return ko.pureComputed({
                read: function () {
                    var result = self.pluginSettings.excludedFromTemplateCopy().includes(fieldName) == false;
                    return result
                },
                write: function (value) {
                    if (value == false){
                        self.pluginSettings.excludedFromTemplateCopy.push(fieldName);
                    } else {
                        self.pluginSettings.excludedFromTemplateCopy.remove(fieldName);
                    }
                },
                owner: this
            });
        }

        // overwrite save-button
        const origSaveSettingsFunction = self.settingsViewModel.saveData;
        const newSaveSettingsFunction = function confirmSpoolSelectionBeforeStartPrint(data, successCallback, setAsSending) {
            if (
                self.pluginSettings.useExternal() == true &&
                (
                    self.showDatabaseErrorMessage() == true ||
                    self.showUpdateSchemeMessage() == true
                )
            ) {
                const confirmationResult = confirm('External database will not work. Save settings anyway?');
                if (confirmationResult == true) {
                    return origSaveSettingsFunction(data, successCallback, setAsSending);
                }
                return null;
            }

            return origSaveSettingsFunction(data, successCallback, setAsSending);
        }
        self.settingsViewModel.saveData = newSaveSettingsFunction;

        // QR-Code stuff
        self.generateQRCodeTestLink = function(){
            var source = self.pluginSettings.qrCodeURLPrefix() + "/plugin/SpoolManager/selectSpoolByQRCode/qrPreviewId";
            var title = "This link is used for the QR-Code";
            return {
                href: source,
                title: title
            }
        }

        ///////////////////////////////////////////////////// END: SETTINGS


        ////////////////////////////////////////////////////////////////////////////////////////// SIDEBAR - REPLACEMENT
        self.printerStateViewModel.spoolsWithWeight = ko.observableArray([]);
        self.printerStateViewModel.extrusionValues = ko.observableArray([]);

        self.updateExtrusionValues = function(extrusionValuesArray){
            // update patched PrinterStateViewModel
            self.printerStateViewModel.extrusionValues(extrusionValuesArray);
        }

        self.updateRequiredFilament = function(requiredFilament){
/*
                    # "metaDataPresent": metaDataPresent,
					# "warnUser": fromPluginSettings,
					# "attributesMissing": someAttributesMissing,
					# "notEnough": notEnough,
					# "detailedSpoolResult": [
					# 				"toolIndex": toolIndex,
					# 				"requiredWeight": requiredWeight,
					# 				"requiredLength": filamentLength,
					# 				"diameter": diameter,
					# 				"density": density,
					# 				"notEnough": notEnough,
					# 				"spoolSelected": True
					# ]
 */
            var filamentList = requiredFilament["detailedSpoolResult"];
            var filteredFilamentList = [];
            // filter not required tools
            for (filamentItem of filamentList){
                if (filamentItem.requiredLength > 0){
                    filteredFilamentList.push(filamentItem)
                }
            }
            self.printerStateViewModel.spoolsWithWeight(filteredFilamentList)
        }

        self.printerStateViewModel.formatSpoolsWithWeight = function formatSpoolsWithWeightInSidebar(filament) {
            if (!filament) return '-';

            // length in m
            var result = (filament.requiredLength / 1000).toFixed(2) + 'm';
            // try to get the weight
            if (filament.requiredWeight) {
                result += ' / ' + filament.requiredWeight.toFixed(2) + 'g';
            }
            if (filament.spoolSelected && filament.spoolSelected == true){
                if (filament.notEnough) {
                    if (filament.notEnough == true){
                        result += ' (<span style="color:red">'+filament.remainingWeight.toFixed(2) +'g</span>)';
                    }
                }
            } else {
                if (filament.requiredLength > 0){
                    result += ' (no spool selected)';
                }
            }

            return result;
        };

        self.replaceFilamentView = function replaceFilamentViewInSidebar() {
            $('#state').find('.accordion-inner').contents().each(function (index, item) {
                if (item.nodeType !== Node.COMMENT_NODE) {
                    return true;
                }

                if (
                    item.nodeValue !== ' ko foreach: filament ' &&
                    item.nodeValue !== ' ko foreach: [] '
                ) {
                    return true;
                }

                item.nodeValue = ' ko foreach: [] '; // eslint-disable-line no-param-reassign

                let newElement = '<!-- ko if: spoolsWithWeight().length < 1 -->  <span><strong>Required Filament unknown</strong></span><br/> <!-- /ko -->';
                newElement += '<!-- ko foreach: spoolsWithWeight --> <span data-bind="text: \'Tool \' + toolIndex + \': \', attr: {title: \'Filament usage for Spool \' + spoolName}"></span><strong data-bind="html: $root.formatSpoolsWithWeight($data)"></strong><br> <!-- /ko -->';

                newElement += '<div data-bind="visible: settings.settings.plugins.SpoolManager.extrusionDebuggingEnabled">';
                newElement += '<!-- ko foreach: extrusionValues -->';
                newElement += '<div>Extruded Tool <span data-bind="text: $index"></span>: <strong data-bind="text: $data.toFixed(2)"></strong></div>';
                newElement += '<!-- /ko -->';

                newElement += '</div>'
                $(newElement).insertBefore(item);

                return false; // exit loop
            });
        };

        /////////////////////////////////////////////////////////////////////////////////////////// SIDEBAR - SELECT
        self.allSpoolsForSidebar = ko.observableArray([]);
        self.selectedSpoolsForSidebar = ko.observableArray([]);
        // see FILTER/SORTING https://embed.plnkr.co/plunk/Kj5JMv
        self.filterSelectionQuery = ko.observable();

        // self.sidebarFilterSorter = new SpoolsFilterSorter("sidebarSpoolSelection", self.allSpoolsForSidebar);

        self.sidebarSelectSpoolModalToolIndex = ko.observable(null);  // index of the current tool we want to select for
        self.sidebarSelectSpoolModalSpoolItem = ko.observable(null); // current spoolitem

        self.deselectSpoolForSidebar = function(toolIndex, item){
            self.selectSpoolForSidebar(toolIndex, null);
        }

        self.loadSpoolsForSidebar = function() {
            // update filament list length
            var currentProfileData = self.settingsViewModel.printerProfiles.currentProfileData(),
                numExtruders = (currentProfileData ? currentProfileData.extruder.count() : 0),
                currentSelectedSpools = self.selectedSpoolsForSidebar().length,
                diff = numExtruders - currentSelectedSpools,
                i, item;
            if (diff !== 0) {
                if (diff > 0) {
                    for (i = 0; i < diff; i++) {
                        self.selectedSpoolsForSidebar().push(ko.observable(null));
                    }
                } else if (diff < 0) {
                    for (i = 0; i > diff; i--) {
                        self.selectedSpoolsForSidebar().pop();
                    }
                }
                self.selectedSpoolsForSidebar.valueHasMutated();
            }

            const fetchSpoolsQueryParams = {
                filterName: "all",
                from: 0,
                to: 3333,
                sortColumn: "lastUse",
                sortOrder: "desc"
            }

            self.apiClient.callLoadSpoolsByQuery(fetchSpoolsQueryParams, function(responseData) {
                const allSpoolData = responseData.allSpools;

                if (allSpoolData == null) {
                    return;
                }

                // transform to SpoolItems with KO.obseravables
                const allSpoolItems = ko.utils.arrayMap(allSpoolData, function (spoolData) {
                    return self.spoolDialog.createSpoolItemForTable(spoolData);
                });
                self.allSpoolsForSidebar(allSpoolItems);

                const spoolsData = responseData.selectedSpools;

                for (let spoolIdx = 0; spoolIdx < self.selectedSpoolsForSidebar().length; spoolIdx++) {
                    const slot = self.selectedSpoolsForSidebar()[spoolIdx];
                    const spoolData = (spoolIdx < spoolsData.length) ? spoolsData[spoolIdx] : null;
                    const spoolItem = spoolData ? self.spoolDialog.createSpoolItemForTable(spoolData) : null;

                    slot(spoolItem);
                }

                // Pre sorting in Selection-Dialog
                // self.sidebarFilterSorter.sortSpoolArray("displayName", "ascending");
            });
        }

        _buildRemainingWeightText = function(spoolItem) {
            const remainingWeight = spoolItem.remainingWeight();

            if (remainingWeight == null || remainingWeight.length == 0) {
                return "";
            }

            return `${remainingWeight}${WEIGHT_UNIT_SYMBOL}`;
        }

        self.remainingText = function(spoolItem) {
            const remainingWeightText = _buildRemainingWeightText(spoolItem);

            return `(${remainingWeightText})`;
        }

        self.buildTooltipForSpoolItem = function(spoolItem, textPrefix, attribute) {
            const spoolItemAttributeValue = spoolItem[attribute]();
            const mainContent = (
                spoolItemAttributeValue != null ?
                    spoolItemAttributeValue :
                    ""
            );

            return `${textPrefix}${mainContent}`;
        }

        self.getSpoolItemSelectedTool = function(databaseId) {
            const selectedSpools = self.selectedSpoolsForSidebar();

            for (let spoolIdx = 0; spoolIdx < selectedSpools.length; spoolIdx++) {
                const spoolItem = selectedSpools[spoolIdx]();

                if (
                    spoolItem !== null &&
                    spoolItem.databaseId() === databaseId
                ) {
                    return spoolIdx;
                }
            }

            return null;
        }

        self.selectSpoolForSidebar = function(toolIndex, inputSpoolItem) {
            let commitCurrentSpoolValues;
            if (self.printerStateViewModel.isPrinting()) {
                commitCurrentSpoolValues = confirm(
                    'You are changing a spool while printing. SpoolManager will commit the usage so far to the previous spool, unless you wish otherwise.\n\n' +
                    'Commit the usage of the print so far…\n' +
                    '"OK": …to the previously selected spool\n' +
                    '"Cancel": …to the new spool'
                )
            }

            // Note: there was a commented-out code checking whether the selected spool
            // is already selected for another tool head.
            const databaseId = (
                inputSpoolItem != null ?
                    inputSpoolItem.databaseId() :
                    -1
            );

            self.apiClient.callSelectSpool(toolIndex, databaseId, commitCurrentSpoolValues, function(responseData) {
                const selectedSpoolData = responseData.selectedSpool;

                if (selectedSpoolData == null) {
                    // remove spool from toolIndex

                    self.selectedSpoolsForSidebar()[toolIndex](null);
                    return;
                }

                // remove the spool from the current toolIndex
                const addedSpoolItem = self.spoolDialog.createSpoolItemForTable(selectedSpoolData);
                const addedSpoolItemDatabaseId = addedSpoolItem.databaseId();
                const selectedSpools = self.selectedSpoolsForSidebar();

                for (let spoolIdx = 0; spoolIdx < selectedSpools.length; spoolIdx++) {
                    const spoolItem = selectedSpools[spoolIdx]();

                    if (
                        spoolItem !== null &&
                        spoolItem.databaseId() === addedSpoolItemDatabaseId
                    ) {
                        selectedSpools[spoolIdx](null);

                        break;
                    }
                }

                // assign to new (or same) toolIndex
                if (toolIndex != -1) {
                    self.selectedSpoolsForSidebar()[toolIndex](addedSpoolItem)
                }
            });
        }

        self.editSpoolFromSidebar = function(toolIndex, spoolItem){
            if (spoolItem == null){
                alert("Something is wrong. No Spool is selected to edit from sidebar!")
            }
            self.showSpoolDialogAction(spoolItem);
        }

        self.sidebarSelectSpoolFromDialog = function (spoolItem) {
            self.selectionSpoolDialog.modal("hide");
            self.selectSpoolForSidebar(self.sidebarSelectSpoolModalToolIndex(), spoolItem);
        }

        self.sidebarOpenSelectSpoolDialog = function(toolIndex, spoolItem){

            /* needed for Filter-Search dropdown-menu */
            $('.dropdown-menu.keep-open').click(function(e) {
                e.stopPropagation();
            });

            self.sidebarSelectSpoolModalSpoolItem(spoolItem);
            self.sidebarSelectSpoolModalToolIndex(toolIndex);

            // self.sidebarFilterSorter.initFilterSorter();

            self.selectionSpoolDialog.modal({
                minHeight: 300,
                show: true
            });
            $("#filterSelectionQueryTextfield").focus();
        }

        //////////////////////////////////////////////////////////////////////////////////////////////////// TABLE / TAB

        self.addNewSpool = function(){
            self.spoolDialog.showDialog(null, closeDialogHandler);
        }

        self.tableAttributeVisibility = {
            databaseId: ko.observable(false),
            displayName: ko.observable(true),
            material: ko.observable(true),
            lastFirstUse: ko.observable(true),
            weight: ko.observable(true),
            used: ko.observable(true),
            note: ko.observable(true),
        };

        const assignSpoolsTableColumnVisibility = (attributeName) => {
            const localStorageKey = `spoolmanager.table.visible.${attributeName}`;
            const localStorageValue = localStorage[localStorageKey];
            const attributeVisibilityObservable = self.tableAttributeVisibility[attributeName];

            if (localStorageValue == null) {
                // Initialize localStorage with default value
                localStorage[localStorageKey] = attributeVisibilityObservable();
            } else {
                const isVisible = "true" == localStorageValue;

                attributeVisibilityObservable(isVisible);
            }

            attributeVisibilityObservable.subscribe(function(newValue) {
                localStorage[localStorageKey] = newValue;
            });
        };

        self.initTableVisibilities = function() {
            if (!Modernizr.localstorage) {
                return;
            }

            Object.keys(self.tableAttributeVisibility).forEach((attributeName) => {
                assignSpoolsTableColumnVisibility(attributeName);
            });
        }

        ///////////////////////////////////////////////////////////////////////////////////////////////// TABLE BEHAVIOR
        /* needed for Filter-Search dropdown-menu */
        $('.dropdown-menu.keep-open').click(function(e) {
            e.stopPropagation();
        });

        self.spoolItemTableHelper = new TableItemHelper(
            function(tableQuery, observableTableModel, observableTotalItemCount) {
                self.apiClient.callLoadSpoolsByQuery(tableQuery, function(responseData) {
                    const hasDbConnectionProblem = responseData.databaseConnectionProblem == true;

                    self.pluginNotWorking(hasDbConnectionProblem);

                    const {
                        totalItemCount,
                        allSpools,
                        catalogs,
                        templateSpools,
                    } = responseData;

                    self.spoolItemTableHelper.updateCatalogs(catalogs);
                    self.spoolDialog.updateCatalogs(catalogs);
                    self.spoolDialog.updateTemplateSpools(templateSpools);

                    const dataRows = ko.utils.arrayMap(allSpools, function (spoolData) {
                        return self.spoolDialog.createSpoolItemForTable(spoolData);
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

            // identify for which toolindex is the current selectedSpoolItem is selected
            var currentDatabaseId = selectedSpoolItem.databaseId();
            if (currentDatabaseId) {
                for (var i = 0; i < self.selectedSpoolsForSidebar().length; i++) {
                    spoolItem = self.selectedSpoolsForSidebar()[i]();
                    if (spoolItem !== null && spoolItem.databaseId() === currentDatabaseId) {
                        selectedSpoolItem.selectedForTool(i);
                        break;
                    }
                }
            }
            self.spoolDialog.showDialog(selectedSpoolItem, closeDialogHandler);
        };

        closeDialogHandler = function(shouldTableReload, specialAction, currentSpoolItem){

            if (specialAction === "selectSpoolForPrinting"){
                var toolIndex = currentSpoolItem.selectedForTool();
                if (toolIndex === undefined){
                    // clear current selection
                    toolIndex = -1;
                }
                self.selectSpoolForSidebar(toolIndex, currentSpoolItem);
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
            self.apiClient.allowedToPrint(function(responseData) {
                var result = responseData.result, itemList;

                const printWarnings = (
                    responseData.metaOrAttributesMissing
                    ? {
                        header: "ATTENTION: Needed filament could not calculated (missing metadata or spool-fields)\n\n",
                        missingMeta: " (maybe)",
                    }
                    : {
                        header: "",
                        missingMeta: "",
                    }
                );

                if (result.noSpoolSelected.length) {
                    const toolsWithMissingSpools = result.noSpoolSelected.map((item) => {
                        return `- Tool ${item.toolIndex}`;
                    });

                    const hasConfirmedPrintWithoutSpoolsSelected = confirm(
                        printWarnings.header +
                        'There are no spools selected for the following tools ' +
                        'despite them being used' + printWarnings.missingMeta + ' by this print:\n' +
                        toolsWithMissingSpools.join('\n') + '\n\n' +
                        'Do you want to start the print without selected spools?'
                    );

                    if (!hasConfirmedPrintWithoutSpoolsSelected) {
                        return;
                    }
                }

                if (result.filamentNotEnough.length) {
                    const inadequateFilamentSpools = result.filamentNotEnough.map((item) => {
                        return `- ${buildSpoolLabel(item)}`;
                    });

                    const hasConfirmedPrintWithInadequateFilamentSpools = confirm(
                        printWarnings.header +
                        'The following selected spools do not have enough remaining filament' + printWarnings.missingMeta + ':\n' +
                        inadequateFilamentSpools.join('\n') + '\n\n' +
                        'Do you want to start the print anyway?'
                    );

                    if (!hasConfirmedPrintWithInadequateFilamentSpools) {
                        return;
                    }
                }

                if (result.reminderSpoolSelection.length) {
                    const selectedSpools = result.reminderSpoolSelection.map((item) => {
                        const spoolLabel = buildSpoolLabel(item);
                        const toolTempOffsetText = (
                            responseData.toolOffsetEnabled && item.toolOffset != null
                                ? "\n--  Tool Offset:  " + item.toolOffset + '\u00B0'
                                : ""
                        );
                        const bedTempOffsetText = (
                            responseData.bedOffsetEnabled && item.bedOffset != null
                                ? "\n--  Bed Offset:  " + item.bedOffset + '\u00B0'
                                : ""
                        );
                        const enclosureTempOffsetText = (
                            responseData.enclosureOffsetEnabled && item.enclosureOffset != null
                                ? "\n--  Enclosure Offset:  " + item.enclosureOffset + '\u00B0'
                                : ""
                        );

                        return `- ${spoolLabel}${toolTempOffsetText}${bedTempOffsetText}${enclosureTempOffsetText}`;
                    });

                    const hasConfirmedPrint = confirm(
                        "Do you want to start the print with following selected spools?\n" +
                        selectedSpools.join('\n')
                    );

                    if (!hasConfirmedPrint) {
                        return;
                    }
                }

                self.apiClient.startPrintConfirmed(() => {
                    origStartPrintFunction();
                });
            });
        };
        self.printerStateViewModel.print = newStartPrintFunction;

        // overwrite loadFile
        self.filesViewModel.loadFile = function confirmSpoolSelectionOnLoadAndPrint(data, printAfterLoad) {
            // orig. SourceCode
            if (
                !self.filesViewModel.loginState.hasPermission(self.filesViewModel.access.permissions.FILES_SELECT) ||
                !data
            ) {
                return;
            }

            if (
                printAfterLoad &&
                self.filesViewModel.listHelper.isSelected(data) &&
                self.filesViewModel.enablePrint(data)
            ) {
                // file was already selected, just start the print job with the newStartPrint function
                // SPOOLMANAGER-CHANGE changed OctoPrint.job.start();
                newStartPrintFunction();

                return;
            }

            // select file, start print job (if requested and within dimensions)
            const withinPrintDimensions = self.filesViewModel.evaluatePrintDimensions(data, true);
            const shouldAllowPrint = printAfterLoad && withinPrintDimensions;

            const startPrint = () => {
                OctoPrint.files.select(data.origin, data.path, false).done(function () {
                    if (shouldAllowPrint) {
                        newStartPrintFunction();
                    }
                });
            };

            // TODO: `shouldAllowPrint` should be separated
            if (
                shouldAllowPrint &&
                self.filesViewModel.settingsViewModel.feature_printStartConfirmation()
            ) {
                showConfirmationDialog({
                    message: gettext("This will start a new print job. Please check that the print bed is clear."),
                    question: gettext("Do you want to start the print job now?"),
                    cancel: gettext("No"),
                    proceed: gettext("Yes"),
                    onproceed: function() {
                        startPrint();
                    },
                    nofade: true
                });
            } else {
                startPrint();
            }
        };

        //////////////////////////////////////////////////////////////////////////////////////// PUBLIC VIEWMODEL - APIs
        // e.g. for CostEstaminator-Plugin
        self.api_getSelectedSpoolInformations = function() {
            return self.selectedSpoolsForSidebar().map((spoolItemObservable) => {
                const spoolItem = spoolItemObservable();

                if (spoolItem === null) {
                    return null;
                }

                return {
                    toolIndex: i,
                    databaseId: spoolItem.databaseId(),
                    spoolName: spoolItem.displayName(),
                    vendor: spoolItem.vendor(),
                    material: spoolItem.material(),
                    diameter: spoolItem.diameter(),
                    density: spoolItem.density(),
                    colorName: spoolItem.colorName(),
                    color: spoolItem.color(),
                    cost: spoolItem.cost(),
                    weight: spoolItem.totalWeight()
                };
            });
        }

        //////////////////////////////////////////////////////////////////////////////////////////////// OCTOPRINT HOOKS
        self.onStartup = function onStartupCallback() {
            // Replace FilamentView in sidebar to show weight instead of volumne
            self.replaceFilamentView();
        };

        self.onBeforeBinding = function() {
            // Register Knockout Components
            new SpoolSelectionTableComp().registerSpoolSelectionTableComp();

            // assign current pluginSettings
            self.pluginSettings = self.settingsViewModel.settings.plugins[PLUGIN_ID];
            // load browser stored settings (includs TabelVisibility and pageSize, ...)
            loadSettingsFromBrowserStore();

            // resetSettings-Stuff
            new ResetSettingsUtilV3(self.pluginSettings).assignResetSettingsFeature(PLUGIN_ID, function(data) {
                // no additional reset function needed in V2
            });

            // Load all Spools
            self.loadSpoolsForSidebar();
            // Edit Spool Dialog Binding
            self.spoolDialog.initBinding(self.apiClient, self.pluginSettings, self.printerProfilesViewModel);
            // Import Dialog
            self.csvImportDialog.init(self.apiClient);
            // Database connection problem dialog
            self.databaseConnectionProblemDialog.init(self.apiClient);
            // Select Spool Dialog (no special binding)
            self.selectionSpoolDialog = $("#dialog_spool_selection");

            // Settings - Color-Picker
            self.componentFactory = new ComponentFactory();
            var fillColorViewModel = self.componentFactory.createColorPicker("qrcode-fill-color-picker");
            this.qrCodeFillColor = fillColorViewModel.selectedColor;
            // Init with current value
            this.qrCodeFillColor(self.pluginSettings.qrCodeFillColor());  // needed
            this.qrCodeFillColor.subscribe(function(newColorValue){
                self.pluginSettings.qrCodeFillColor(newColorValue);
            });

            var backgroundColorViewModel = self.componentFactory.createColorPicker("qrcode-background-color-picker");
            this.qrCodeBackgroundColor = backgroundColorViewModel.selectedColor;
            // Init with current value
            this.qrCodeBackgroundColor(self.pluginSettings.qrCodeBackgroundColor());  // needed
            this.qrCodeBackgroundColor.subscribe(function(newColorValue){
                self.pluginSettings.qrCodeBackgroundColor(newColorValue);
            });

            // needed after the tool-count is changed
            self.settingsViewModel.printerProfiles.currentProfileData.subscribe(self.loadSpoolsForSidebar);
        }

        self.onAfterBinding = function() {
            self.spoolDialog.afterBinding();
            self.downloadDatabaseUrl(self.apiClient.getDownloadDatabaseUrl());

// testing            self.spoolDialog.showDialog(null, closeDialogHandler);
        }

        self.onSettingsShown = function() {
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
                var spoolsData = data.selectedSpools,
                    slot, spoolData, spoolItem;
                for(var i=0; i<self.selectedSpoolsForSidebar().length; i++) {
                    slot = self.selectedSpoolsForSidebar()[i];
                    spoolData = (i < spoolsData.length) ? spoolsData[i] : null;
                    spoolItem = spoolData ? self.spoolDialog.createSpoolItemForTable(spoolData) : null;
                    slot(spoolItem);
                }

                return;
            }
            if ("showPopUp" == data.action){
                self.showPopUp(data.type, data.title, data.message, data.autoclose);
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
                self.showPopUp("error", 'ERROR:' + data.title, data.message, data.autoclose);
                return;
            }
            if ("requiredFilamentChanged" == data.action){
                self.updateRequiredFilament(data);
                return;
            }
            if ("extrusionValuesChanged" == data.action){
                self.updateExtrusionValues(data.extrusionValues);
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
            if ("#tab_plugin_PrintJobHistory" == next){
                //self.reloadTableData();
            }
        }

        self.onAfterTabChange = function(current, previous) {
            const tabHashCode = window.location.hash;
            // QR-Code-Call: We can only contain -spoolId on the very first page
            if (!tabHashCode.includes("#tab_plugin_SpoolManager-spoolId")) {
                return;
            }

            let selectedSpoolId = tabHashCode.replace("-spoolId", "").replace("#tab_plugin_SpoolManager", "");
            selectedSpoolId = parseInt(selectedSpoolId);
            console.info('Loading spool: '+selectedSpoolId);

            const spoolCurrentToolId = self.getSpoolItemSelectedTool(selectedSpoolId);
            if (spoolCurrentToolId !== null) {
                alert('This spool is already selected for tool ' + spoolCurrentToolId + '!');
                return;
            }
            if (self.printerStateViewModel.isPrinting()) {
                // not doing this while printing
                return;
            }
            // - Load SpoolItem from Backend
            // - Open SpoolItem
            const commitCurrentSpoolValues = false;

            self.apiClient.callSelectSpool(0, selectedSpoolId, commitCurrentSpoolValues, function(responseData) {
                //Select the SpoolManager tab
                $('a[href="#tab_plugin_SpoolManager"]').tab('show')
                const spoolData = responseData["selectedSpool"];

                if (spoolData == null) {
                    return;
                }

                const spoolItem = self.spoolDialog.createSpoolItemForTable(spoolData);

                spoolItem.selectedFromQRCode(true);
                self.selectedSpoolsForSidebar()[0](spoolItem);
                self.showSpoolDialogAction(spoolItem);
            });
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
            "filesViewModel",
            "printerProfilesViewModel"
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
