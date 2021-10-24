/**
 * loadItemsFunction,
 * defaultPageSize,
 * defaultSortColumn,
 * defaultFilterName
 */
function TableItemHelper(loadItemsFunction, defaultPageSize, defaultSortColumn, defaultFilterName){

    var self = this;

    self.loadItemsFunction = loadItemsFunction;
    self.items = ko.observableArray([]);
    self.totalItemCount = ko.observable(0);

    // paging
    self.pageSizeOptions = ko.observableArray([10, 25, 50, 100, "all"])
    self.selectedPageSize = ko.observable(defaultPageSize)
    self.pageSize = ko.observable(self.selectedPageSize());
    self.currentPage = ko.observable(0);
    // Sorting
    self.sortColumn = ko.observable(defaultSortColumn);
    self.sortOrder = ko.observable("desc");
    // Filtering - all, hide empty, hide inactive
    self.filterOptions = ["all", "onlySuccess", "onlyFailed"];
    self.selectedFilterName = ko.observable(defaultFilterName);
    // Filtering - Material
    self.allMaterials = ko.observableArray([]);
    self.showAllMaterialsForFilter = ko.observable(true);
    self.selectedMaterialsForFilter = ko.observableArray();
    // Filtering - Vendor
    self.allVendors = ko.observableArray([]);
    self.showAllVendorsForFilter = ko.observable(true);
    self.selectedVendorsForFilter = ko.observableArray();
    // Filtering - Color
    self.allColors = ko.observableArray([]);
    self.showAllColorsForFilter = ko.observable(true);
    self.selectedColorsForFilter = ko.observableArray();

    self.isInitialLoadDone = false;
    // ############################################################################################### private functions


    self._evalFilter = function(allItems, selectedItems){
        var filterResult = ["all"];
        if (allItems.length != selectedItems.length){
            filterResult = selectedItems;
        }
        return filterResult;
        // return selectedItems;
    }

    self._loadItems = function(){
        var from = Math.max(self.currentPage() * self.pageSize(), 0);
//        var to = Math.min(from + self.pageSize(), self.totalItemCount());
        var to = self.pageSize();
        if (to == 0){
            to = self.pageSize();
        }

        var materialFilter = self._evalFilter(self.allMaterials(), self.selectedMaterialsForFilter());
        var vendorFilter = self._evalFilter(self.allVendors(), self.selectedVendorsForFilter());
        var colorFilter = self._evalFilter(self.allColors(), self.selectedColorsForFilter());

        var tableQuery = {
            "selectedPageSize": self.selectedPageSize(),
            "from": from,
            "to": to,
            "sortColumn": self.sortColumn(),
            "sortOrder": self.sortOrder(),
            "filterName": self.selectedFilterName(),
            "materialFilter": materialFilter,
            "vendorFilter": vendorFilter,
            "colorFilter": colorFilter
        };
        self.loadItemsFunction( tableQuery, self.items, self.totalItemCount );
    }

    self.currentPage.subscribe(function(newPageIndex) {
        self._loadItems()
    });

    self.selectedPageSize.subscribe(function(newPageSize) {
        self.currentPage(0);
        if ("all" == newPageSize){
            self.pageSize(self.totalItemCount());
        } else {
            self.pageSize(newPageSize);
        }
        // TODO Optimize. provide the defaultpagesize during creation of the helper (default page size)
        self._loadItems()
    });


    self.selectedMaterialsForFilter.subscribe(function(newValues) {
        if (self.selectedMaterialsForFilter().length > 0){
            self.showAllMaterialsForFilter(true);
        } else{
            self.showAllMaterialsForFilter(false);
        }
        // TODO Optimize enable after the values where initialy changed
        self.reloadItems();
    });
    self.selectedVendorsForFilter.subscribe(function(newValues) {
        if (self.selectedVendorsForFilter().length > 0){
            self.showAllVendorsForFilter(true);
        } else{
            self.showAllVendorsForFilter(false);
        }
        // TODO Optimize enable after the values where initialy changed
        self.reloadItems();
    });
    self.selectedColorsForFilter.subscribe(function(newValues) {
        if (self.selectedColorsForFilter().length > 0){
            self.showAllColorsForFilter(true);
        } else{
            self.showAllColorsForFilter(false);
        }

        if (self.selectedColorsForFilter().length != 0){
            // TODO Optimize enable after the values where initialy changed
            self.reloadItems();
        }

    });

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

    // ################################################################################################ public functions
    self.reloadItems = function(){
        self._loadItems();
    }

    self.updateCatalogs = function(catalogs){
        self.allCatalogs = catalogs;
        var materialsCatalog = self.allCatalogs["materials"];
        var vendorsCatalog = self.allCatalogs["vendors"];
        var colorsCatalog = self.allCatalogs["colors"];

        self.allMaterials(materialsCatalog);
        self.allVendors(vendorsCatalog);
        self.allColors(colorsCatalog);
    }

    self.paginatedItems = ko.dependentObservable(function() {
        if (self.items() === undefined) {
            return [];
        } else if (self.pageSize() === 0) {
            return self.items();
        } else {
            if (self.isInitialLoadDone == false){
                self.isInitialLoadDone = true;
                self._loadItems();
            }
            return self.items();
        }
    });
    // ############################################## SORTING
    self.changeSortOrder = function(newSortColumn){
        if (newSortColumn == self.sortColumn()){
            // toggle
            if ("desc" == self.sortOrder()){
                self.sortOrder("asc");
            } else {
               self.sortOrder("desc");
            }
        } else {
            self.sortColumn(newSortColumn);
            self.sortOrder("asc");
        }
        self.currentPage(0);
        self._loadItems();
    }

    self.sortOrderLabel = function(sortColumn){
        if (sortColumn == self.sortColumn()){
            // toggle
            if ("desc" == self.sortOrder()){
                return ("(descending)");
            } else {
               return ("(ascending)");
            }
        }
        return "";
    }

    // ############################################## FILTERING
    self.changeFilter = function(newFilterName) {
        self.selectedFilterName(newFilterName)
        self.currentPage(0);
        self._loadItems();
    };

    self.isFilterSelected = function(filterName) {
        return self.selectedFilterName() == filterName;
    };

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

    // ############################################## PAGING
    self.changePage = function(newPage) {
        if (newPage < 0 || newPage > self.lastPage())
            return;
        self.currentPage(newPage);
    };

    self.prevPage = function() {
        if (self.currentPage() > 0) {
            self.currentPage(self.currentPage() - 1);
        }
    };
    self.nextPage = function() {
        if (self.currentPage() < self.lastPage()) {
            self.currentPage(self.currentPage() + 1);
        }
    };
    self.lastPage = ko.dependentObservable(function() {
        return (self.pageSize() === 0 ? 1 :
                Math.ceil(self.totalItemCount() / self.pageSize()) - 1);
    });

   self.pages = ko.dependentObservable(function() {
        var pages = [];
        var i;

        if (self.pageSize() === 0) {
            pages.push({ number: 0, text: 1 });
        } else if (self.lastPage() < 7) {
            for (i = 0; i < self.lastPage() + 1; i++) {
                pages.push({ number: i, text: i+1 });
            }
        } else {
            pages.push({ number: 0, text: 1 });
            if (self.currentPage() < 5) {
                for (i = 1; i < 5; i++) {
                    pages.push({ number: i, text: i+1 });
                }
                pages.push({ number: -1, text: "…"});
            } else if (self.currentPage() > self.lastPage() - 5) {
                pages.push({ number: -1, text: "…"});
                for (i = self.lastPage() - 4; i < self.lastPage(); i++) {
                    pages.push({ number: i, text: i+1 });
                }
            } else {
                pages.push({ number: -1, text: "…"});
                for (i = self.currentPage() - 1; i <= self.currentPage() + 1; i++) {
                    pages.push({ number: i, text: i+1 });
                }
                pages.push({ number: -1, text: "…"});
            }
            pages.push({ number: self.lastPage(), text: self.lastPage() + 1})
        }
        return pages;
    });


}
