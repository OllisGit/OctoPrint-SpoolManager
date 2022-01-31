


function SpoolsFilterSorter(filterSorterId, spoolsArrayKO) {
    let self = this;
    ////////////////////////////////////////////////////////////////////// field variables
    self.filterSorterId = filterSorterId;
    self.spoolsArray = spoolsArrayKO;

    self.totalShown = ko.observable(1);
    // SORTING
    self.currentSortField = ko.observable();
    self.currentSortOder = ko.observable("ascending"); // or ascending

    // FILTERING
    self.filterSelectionQuery = ko.observable();
    self.hideEmptySpools = ko.observable();
    self.hideInActiveSpools = ko.observable();
    // FILTERING - Catalogs
    self.allColors = ko.observableArray([]);
    // - Filtering - Material
    self.allMaterials = ko.observableArray([]);
    self.showAllMaterialsForFilter = ko.observable(true);
    self.selectedMaterialsForFilter = ko.observableArray();
    // - Filtering - Vendor
    self.allVendors = ko.observableArray([]);
    self.showAllVendorsForFilter = ko.observable(true);
    self.selectedVendorsForFilter = ko.observableArray();
    // - Filtering - Color
    self.showAllColorsForFilter = ko.observable(true);
    self.selectedColorsForFilter = ko.observableArray();

    //////////////////////////////////////////////////////////////////// browser storage
    var storageKeyPrefix = "spoolmanager.filtersorter." + filterSorterId + ".";

    self._loadFilterSelectionsFromBrowserStorage = function(){
        if (!Modernizr.localstorage) {
            // damn, no browser storage!!!
            return false;
        }

        if (localStorage[storageKeyPrefix + "hideEmptySpools"] != null){
            self.hideEmptySpools(   localStorage[storageKeyPrefix + "hideEmptySpools"] == 'false' ? false : true);
        }
        if (localStorage[storageKeyPrefix + "hideInActiveSpools"] != null){
            self.hideInActiveSpools(localStorage[storageKeyPrefix + "hideInActiveSpools"] == 'false' ? false : true);
        }
        // maybe if someone request for it
        // if (localStorage[storageKeyPrefix + "showAllMaterialsForFilter"] != null){
        //     self.showAllMaterialsForFilter(localStorage[storageKeyPrefix + "showAllMaterialsForFilter"] == 'false' ? false : true);
        // }
        // if (localStorage[storageKeyPrefix + "showAllVendorsForFilter"] != null){
        //     self.showAllVendorsForFilter(localStorage[storageKeyPrefix + "showAllVendorsForFilter"] == 'false' ? false : true);
        // }
        // if (localStorage[storageKeyPrefix + "showAllColorsForFilter"] != null){
        //     self.showAllColorsForFilter(localStorage[storageKeyPrefix + "showAllColorsForFilter"] == 'false' ? false : true);
        // }
        //
        // if (localStorage[storageKeyPrefix + "selectedMaterialsForFilter"] != null){
        //   self.selectedMaterialsForFilter(self._stringToArray(localStorage[storageKeyPrefix + "selectedMaterialsForFilter"]));
        // }
        // if (localStorage[storageKeyPrefix + "selectedVendorsForFilter"] != null){
        //   self.selectedVendorsForFilter(self._stringToArray(localStorage[storageKeyPrefix + "selectedVendorsForFilter"]));
        // }
        // if (localStorage[storageKeyPrefix + "selectedColorsForFilter"] != null){
        //   self.selectedColorsForFilter(self._stringToArray(localStorage[storageKeyPrefix + "selectedColorsForFilter"]));
        // }
    }

    self._storeFilterSelectionsToBrowserStorage = function(){
        if (!Modernizr.localstorage) {
            // damn, no browser storage!!!
            return false;
        }
        if (self.hideEmptySpools() != null){
            localStorage[storageKeyPrefix + "hideEmptySpools"] = self.hideEmptySpools();
        }
        if (self.hideInActiveSpools() != null){
            localStorage[storageKeyPrefix + "hideInActiveSpools"] = self.hideInActiveSpools();
        }
        // maybe if someone request for it
        // if (self.showAllMaterialsForFilter() != null){
        //     localStorage[storageKeyPrefix + "showAllMaterialsForFilter"] = self.showAllMaterialsForFilter();
        // }
        // if (self.showAllVendorsForFilter() != null){
        //     localStorage[storageKeyPrefix + "showAllVendorsForFilter"] = self.showAllVendorsForFilter();
        // }
        // if (self.showAllColorsForFilter() != null){
        //     localStorage[storageKeyPrefix + "showAllColorsForFilter"] = self.showAllColorsForFilter();
        // }
        //
        // localStorage[storageKeyPrefix + "selectedMaterialsForFilter"] = self._arrayToString(self.selectedMaterialsForFilter());
        // localStorage[storageKeyPrefix + "selectedVendorsForFilter"] = self._arrayToString(self.selectedVendorsForFilter());
        // localStorage[storageKeyPrefix + "selectedColorsForFilter"] = self._arrayToString(self.selectedColorsForFilter());
    }

    self._stringToArray = function(stringValues){
        var result = stringValues.split("^");
        return result;
    }

    self._arrayToString = function(arrayValues){
        var result = "";
        arrayValues.forEach(function(value) {
            result += value + "^";
        });
        return result;
    }

    // initial loading from browser storage
    self._loadFilterSelectionsFromBrowserStorage();

    ///////////////////////////////////////////////////////////////////// subscribe listeners
    self.hideEmptySpools.subscribe(function(newValues) {
        self._executeFilter();
        self._storeFilterSelectionsToBrowserStorage();
    });
    self.hideInActiveSpools.subscribe(function(newValues) {
        self._executeFilter();
        self._storeFilterSelectionsToBrowserStorage();
    });
    self.selectedMaterialsForFilter.subscribe(function(newValues) {
        if (self.selectedMaterialsForFilter().length > 0){
            self.showAllMaterialsForFilter(true);
        } else{
            self.showAllMaterialsForFilter(false);
        }
        self._executeFilter();
        self._storeFilterSelectionsToBrowserStorage();
    });
    self.selectedVendorsForFilter.subscribe(function(newValues) {
        if (self.selectedVendorsForFilter().length > 0){
            self.showAllVendorsForFilter(true);
        } else{
            self.showAllVendorsForFilter(false);
        }
        self._executeFilter();
        self._storeFilterSelectionsToBrowserStorage();
    });
    self.selectedColorsForFilter.subscribe(function(newValues) {
        if (self.selectedColorsForFilter().length > 0){
            self.showAllColorsForFilter(true);
        } else{
            self.showAllColorsForFilter(false);
        }
        self._executeFilter();
        self._storeFilterSelectionsToBrowserStorage();
    });

    ///////////////////////////////////////////////// functions

    self.initFilterSorter = function (){
        //Needed because, now the array is filled, so triggered it before showing the dialog
        self._executeFilter();
    }

    // maybe not needed
    self.setSpoolsArray = function(spoolsArrayKO){
        self.spoolsArray = spoolsArrayKO;
    }

    self.getSpoolsArray = function(){
        return self.spoolsArray;
    }

    // FILTER - Stuff
    self.clearFilterSelectionQuery = function () {
        self.filterSelectionQuery("");
    };

    self.filterSelectionQuery.subscribe(function(filterQuery) {
        self._executeFilter();
    });

    // FILTER - Catalogs
    self.updateCatalogs = function(catalogs){
        self.allCatalogs = catalogs;
        var materialsCatalog = self.allCatalogs["materials"];
        var vendorsCatalog = self.allCatalogs["vendors"];
        var colorsCatalog = self.allCatalogs["colors"];

        self.allMaterials(materialsCatalog);
        self.allVendors(vendorsCatalog);
        self.allColors(colorsCatalog);

    }

    self.buildFilterLabel = function(filterLabelName){
        // spoolItemTableHelper.selectedColorsForFilter().length == spoolItemTableHelper.allColors().length ? 'all' : spoolItemTableHelper.selectedColorsForFilter().length
        // to detecting all, we can't use the length, because if just the color is changed then length is still true
        // so we need to compare each value
        if ("color" == filterLabelName){
            var selectionArray = self.selectedColorsForFilter(); // array of colorIds [#ffa500;orange, #ffffff;white]
            var allColorArray = self.allColors(); // array of object with 'colorId=#ffa500;orange','color=#ffa500','colorName="orange"'
            // check if all colors selected
            var selectionCount = 0
            for (let colorItem of allColorArray) {
                var colorId = colorItem.colorId;
                if (selectionArray.indexOf(colorId) != -1){
                    selectionCount++;
                }
            }
            var allColorsSelected = selectionCount ==  allColorArray.length
            return allColorsSelected == true ? "all" : self.selectedColorsForFilter().length;
        }
        if ("material" == filterLabelName){
            return self._evalFilterLabel(self.allMaterials(), self.selectedMaterialsForFilter());
        }
        if ("vendor" == filterLabelName){
            return self._evalFilterLabel(self.allVendors(), self.selectedVendorsForFilter());
        }

        return "not defined:" + filterLabelName;
    }

    self.doFilterSelectAll = function(data, catalogName){
        let checked;
        switch (catalogName) {
            case "material":
                checked = self.showAllMaterialsForFilter();
                if (checked == true) {
                    self.selectedMaterialsForFilter().length = 0;
                    ko.utils.arrayPushAll(self.selectedMaterialsForFilter, self.allMaterials());
                } else {
                    self.selectedMaterialsForFilter.removeAll();
                }
                break;
            case "vendor":
                checked = self.showAllVendorsForFilter();
                if (checked == true) {
                    self.selectedVendorsForFilter().length = 0;
                    ko.utils.arrayPushAll(self.selectedVendorsForFilter, self.allVendors());
                } else {
                    self.selectedVendorsForFilter.removeAll();
                }
                break;
            case "color":
                checked = self.showAllColorsForFilter();
                if (checked == true) {
                    self.selectedColorsForFilter().length = 0;
                    // we are using an colorId as a checked attribute, we can just move the color-objects to the selectedArrary
                    // ko.utils.arrayPushAll(self.spoolItemTableHelper.selectedColorsForFilter, self.spoolItemTableHelper.allColors());
                    for (let i = 0; i < self.allColors().length; i++) {
                        let colorObject = self.allColors()[i];
                        self.selectedColorsForFilter().push(colorObject.colorId);
                    }
                    self.selectedColorsForFilter.valueHasMutated();
                } else {
                    self.selectedColorsForFilter.removeAll();
                }
                break;
        }
    }

    self._executeFilter = function(){
        var filterQuery = self.filterSelectionQuery == null || self.filterSelectionQuery() == null ? "" : self.filterSelectionQuery() ;
        filterQuery = filterQuery.toLowerCase();
        var totalShownCount = 0;
        // self.spoolsArray().forEach(function(spool) {
        for (spool of self.spoolsArray()) {

            var spoolProperties = spool.material() + " " +
                                  spool.displayName() + " " +
                                  spool.colorName();

            if (spoolProperties.toLowerCase().indexOf(filterQuery) > -1) {
                spool.isFilteredForSelection(false);
            } else {
                spool.isFilteredForSelection(true);
            }
            if (self.hideEmptySpools() == true){
                var isEmpty = spool.remainingWeight == null || spool.remainingWeight() <= 0 ? true : false;
                if (isEmpty){
                    spool.isFilteredForSelection(true);
                }
            }
            if (self.hideInActiveSpools() == true && spool.isActive() == false){
                spool.isFilteredForSelection(true);
            }

            // Filter against catalogs,  if not already filtered
            if (spool.isFilteredForSelection() == false){
                // Material
                if (self.allMaterials().length != self.selectedMaterialsForFilter().length){
                    var spoolMaterial = spool.material != null && spool.material() != null ? spool.material() : "";
                    if (self.selectedMaterialsForFilter().includes(spoolMaterial) == false){
                        spool.isFilteredForSelection(true);
                    }
                }
                if (spool.isFilteredForSelection() == false){
                    // Vendor
                    if (self.allVendors().length != self.selectedVendorsForFilter().length){
                        var spoolVendor = spool.vendor != null && spool.vendor() != null ? spool.vendor() : "";
                        if (self.selectedVendorsForFilter().includes(spoolVendor) == false){
                            spool.isFilteredForSelection(true);
                        }
                    }
                    if (spool.isFilteredForSelection() == false){
                        // Color
                        if (self.allColors().length != self.selectedColorsForFilter().length){
                            var spoolColorCode = spool.color != null && spool.color() != null ? spool.color() : "";
                            var spoolColorName = spool.colorName != null && spool.colorName() != null ? spool.colorName() : "";
                            var colorId = spoolColorCode + ";" + spoolColorName;
                            if (self.selectedColorsForFilter().includes(colorId) == false){
                                spool.isFilteredForSelection(true);
                            }
                        }
                    }
                }
            }
            if (spool.isFilteredForSelection() == false){
                totalShownCount += 1;
            }
        // });
        }
        self.totalShown(totalShownCount);
    }

    /**
     * return the selection count of a specific catalog-array
     */
    self._evalFilterLabel = function(allArray, selectionArray){
        // check if all selected
        var selectionCount = 0
        for (let item of allArray) {
            if (selectionArray.indexOf(item) != -1){
                selectionCount++;
            }
        }
        var allSelected = selectionCount ==  allArray.length
        return allSelected == true ? "all" : selectionArray.length;
    };

    ////////////////////////////////////////////////////////////////////////////////
    // SORTING - Stuff
    self.sortSpoolArray = function(sortField, requestedSortOrder){
            var sortResult = 0;
            var sorted = self.spoolsArray();

            if (requestedSortOrder){
                self.currentSortOder(requestedSortOrder == "descending" ? "ascending" : "descending");
            }

            var sortOrientation = 1;
            if (self.currentSortOder() == "descending"){
                self.currentSortOder("ascending");
                sortOrientation = -1;
            } else {
                self.currentSortOder("descending");
            }

            if (sortField === "displayName") {
                sorted.sort(function (a, b) {
                    var sortResult = b.displayName().toLowerCase().localeCompare(a.displayName().toLowerCase()) * sortOrientation;
                    return sortResult;
                });
            } else if (sortField === 'material') {
                sorted.sort(function sortDesc(a, b) {
                    var valueA = a.material() != null ? a.material().toLowerCase() : "";
                    var valueB = b.material() != null ? b.material().toLowerCase() : "";
                    var sortResult = valueB.localeCompare(valueA) * sortOrientation;

                    return sortResult;
                });
            } else if (sortField === 'lastUse') {
                sorted.sort(function sortDesc(a, b) {
                    var valueA = a.lastUse() != null ? a.lastUse() : "";
                    var valueB = b.lastUse() != null ? b.lastUse() : "";
                    if (valueA == valueB){
                        sortResult = b.databaseId() - a.databaseId();
                    } else {
                        if (valueA == ""){
                            sortResult = 1;
                        } else {
                            if (valueB == ""){
                                sortResult = -1;
                            } else {
                                var momA = moment(valueA, "DD.MM.YYYY hh:mm");
                                var momB = moment(valueB, "DD.MM.YYYY hh:mm");

                                if (momA > momB){
                                    sortResult = -1;
                                } else {
                                    sortResult = 1;
                                }
                            }
                        }
                    }
                    // sortResult = momB - momA;
                    sortResult = sortResult * sortOrientation;
                    return sortResult;
                });
            } else if (sortField === 'firstUse') {
                sorted.sort(function sortDesc(a, b) {
                    var valueA = a.firstUse() != null ? a.firstUse() : "";
                    var valueB = b.firstUse() != null ? b.firstUse() : "";
                    if (valueA == valueB){
                        sortResult = b.databaseId() - a.databaseId();
                    } else {
                        if (valueA == ""){
                            sortResult = 1;
                        } else {
                            if (valueB == ""){
                                sortResult = -1;
                            } else {
                                var momA = moment(valueA, "DD.MM.YYYY hh:mm");
                                var momB = moment(valueB, "DD.MM.YYYY hh:mm");

                                if (momA > momB){
                                    sortResult = -1;
                                } else {
                                    sortResult = 1;
                                }
                            }
                        }
                    }
                    // sortResult = momB - momA;
                    sortResult = sortResult * sortOrientation;
                    return sortResult;
                });
            } else if (sortField === 'remaining') {
                sorted.sort(function sortDesc(a, b) {
                    var valueA = a.remainingWeight() != null ? a.remainingWeight() : 0;
                    var valueB = b.remainingWeight() != null ? b.remainingWeight() : 0;
                    var sortResult = valueB - valueA;

                    sortResult = sortResult * sortOrientation;
                    return sortResult;
                });
            }
            self.spoolsArray(sorted);
            self.currentSortField(sortField);
    }
}
