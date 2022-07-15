// Dialog functionality
function SpoolManagerEditSpoolDialog(){

    var self = this;

    ///////////////////////////////////////////////////////////////////////////////////////////////////////// CONSTANTS
    var DEFAULT_COLOR = "#ff0000";
    var densityMap = {
        PLA:	1.24,
        PLA_plus:	1.24,
        ABS:	1.04,
        PETG:	1.27,
        NYLON:	1.52,
        TPU:	1.21,
        PC:	    1.3,
        Wood:	1.28,
        Carbon:	1.3,
        PC_ABS:	1.19,
        HIPS:	1.03,
        PVA:	1.23,
        ASA:	1.05,
        PP:	    0.9,
        POM:	1.4,
        PMMA:	1.18,
        FPE:	2.16
    };

    self.unitValues = {
        WEIGHT: "weight",
        LENGTH: "length"
    };
    self.stateValues = {
        INITIAL: "initial",
        USED: "used",
        REMAINING: "remaining"
    };
    self.scopeValues = {
        FILAMENT: "filament",
        SPOOL: "spool",
        COMBINED: "spool+filament"
    };

    var FILAMENT = self.scopeValues.FILAMENT;
    var COMBINED = self.scopeValues.COMBINED;
    var SPOOL = self.scopeValues.SPOOL;

    ///////////////////////////////////////////////////////////////////////////////////////////////////////// ITEM MODEL
    var SpoolItem = function(spoolData, editable) {
        // Init Item

        // if we use the Item for Editing we need to initialise the widget-model as well , e.g. Option-Values, Suggestion-List
        // if we just use this Item in readonly-mode we need simple ko.observer

        // FormatHelperFunction
        formatOnlyDate = function (data, dateBindingName) {
            var dateValue = data[dateBindingName];
            if (dateValue != null && dateValue() != null && dateValue() != ""){
                dateValue = dateValue();
                var result = dateValue.split(" ")[0];
                return result
            }
            return "";
        };

        this.selectedFromQRCode = ko.observable(false);
        this.selectedForTool = ko.observable(0);    // Default Tool 0
        this.isFilteredForSelection = ko.observable(false);
        // - list all attributes
        this.version = ko.observable();
        this.isSpoolVisible = ko.observable(false);
        this.hasNoData = ko.observable();
        this.databaseId = ko.observable();
        this.isTemplate = ko.observable();
        this.isActive = ko.observable();
        this.isInActive = ko.observable();
        this.displayName = ko.observable();
//        this.vendor = ko.observable();
//        this.material = ko.observable();
        this.density = ko.observable();
        this.diameter = ko.observable();
        this.diameterTolerance = ko.observable();
        this.flowRateCompensation = ko.observable();
        this.temperature = ko.observable();
        this.bedTemperature = ko.observable();
        this.enclosureTemperature = ko.observable();
        this.offsetTemperature = ko.observable();
        this.offsetBedTemperature = ko.observable();
        this.offsetEnclosureTemperature = ko.observable();
        this.colorName = ko.observable();
        this.color = ko.observable();
        this.totalWeight = ko.observable();
        this.spoolWeight = ko.observable();
        this.remainingWeight = ko.observable();
        this.remainingPercentage = ko.observable();
        this.totalLength = ko.observable();
        this.usedLength = ko.observable();
        this.usedLengthPercentage = ko.observable();
        this.remainingLength = ko.observable();
        this.remainingLengthPercentage = ko.observable();
        this.usedWeight = ko.observable();
        this.usedPercentage = ko.observable();
        this.code = ko.observable();
//        this.labels = ko.observable();
//            this.allLabels = ko.observable();
        this.noteText = ko.observable()
        this.noteDeltaFormat = ko.observable()
        this.noteHtml = ko.observable()

        this.firstUse = ko.observable();
        this.lastUse = ko.observable();
        this.firstUseKO = ko.observable();
        this.lastUseKO = ko.observable();
        this.purchasedOn = ko.observable();
        this.purchasedOnKO = ko.observable();


        // this.purchasedFrom = ko.observable();
        this.cost = ko.observable();
        this.costUnit = ko.observable();

        // Assign default values for editing
        // overwrite and/or add attributes
        var vendorViewModel = self.componentFactory.createSelectWithFilter("spool-vendor-select", $('#spool-form'));
        this.vendor = vendorViewModel.selectedOption;
        this.allVendors = vendorViewModel.allOptions;

        var materialViewModel = self.componentFactory.createSelectWithFilter("spool-material-select", $('#spool-form'));
        this.material = materialViewModel.selectedOption;
        // this.allMaterials = materialViewModel.allOptions;

        var purchasedFromViewModel = self.componentFactory.createSelectWithFilter("spool-purchasedFrom-select", $('#spool-form'));
        this.purchasedFrom = purchasedFromViewModel.selectedOption;
        this.allPurchasedFrom = purchasedFromViewModel.allOptions;

        // Autosuggest for "density"
        this.material.subscribe(function(newMaterial){
            if ($("#dialog_spool_edit").is(":visible")){
                if (self.spoolItemForEditing.isSpoolVisible() == true){
                    var mat = self.spoolItemForEditing.material();
                    if (mat){
                        var density = densityMap[mat.toUpperCase()]
                        if (density){
                           self.spoolItemForEditing.density(density);
                        }
                    }
                }
            }
        });

        if (editable == true){
            var colorViewModel = self.componentFactory.createColorPicker("filament-color-picker");
            this.color = colorViewModel.selectedColor;
            this.color(DEFAULT_COLOR);  // needed

            var firstUseViewModel = self.componentFactory.createDateTimePicker("firstUse-date-picker");
            var lastUseViewModel = self.componentFactory.createDateTimePicker("lastUse-date-picker");
            var purchasedOnViewModel = self.componentFactory.createDateTimePicker("purchasedOn-date-picker", false);
            this.firstUse = firstUseViewModel.currentDateTime;
            this.lastUse = lastUseViewModel.currentDateTime;
            this.purchasedOn = purchasedOnViewModel.currentDateTime;
        }
        self.labelsViewModel = self.componentFactory.createLabels("spool-labels-select", $('#spool-form'));
        this.labels   = self.labelsViewModel.selectedOptions;
        this.allLabels = self.labelsViewModel.allOptions;

        // Non-persistent fields (these exist only in this view model for weight-calculation)
        this.totalCombinedWeight = ko.observable();
        this.remainingCombinedWeight = ko.observable();
        this.drivenScope = ko.observable();
        this.drivenScopeOptions = ko.observableArray([
            {
                text: "Filament Amount",
                value: FILAMENT,
            },
            {
                text: "Spool Weight",
                value: SPOOL,
            },
            {
                text: "Combined Weight",
                value: COMBINED,
            },
        ]);

        // Fill Item with data
        this.update(spoolData);
    }

    SpoolItem.prototype.update = function (data) {
        var updateData = data || {}

        // TODO weight: renaming
        self.autoUpdateEnabled = false;

        // update latest all catalog
        if (self.catalogs != null){
            // labels
            this.allLabels.removeAll();
            ko.utils.arrayPushAll(this.allLabels, self.catalogs.labels);
            // materials
            // this.allMaterials(self.catalogs.materials);

            //vendors
            this.allVendors(self.catalogs.vendors);

            //purchasedFrom
            this.allPurchasedFrom(self.catalogs.purchasedFrom);
        }

        this.selectedFromQRCode(updateData.selectedFromQRCode);
        this.selectedForTool(updateData.selectedForTool);
        this.hasNoData(data == null);
        this.version(updateData.version);
        this.databaseId(updateData.databaseId);
        this.isTemplate(updateData.isTemplate);
        this.isActive(updateData.isActive);
        this.isInActive(!updateData.isActive);
        this.displayName(updateData.displayName);
        this.vendor(updateData.vendor);
        this.purchasedFrom(updateData.purchasedFrom);

        this.material(updateData.material);
        this.density(updateData.density);
        this.diameter(updateData.diameter);
        this.diameterTolerance(updateData.diameterTolerance);
        // first update color code, and then update the color name
        this.color(updateData.color == null ? DEFAULT_COLOR : updateData.color);
        // if no custom color name present, use predefined name
        if (updateData.colorName == null || updateData.colorName.length == 0){
            var preDefinedColorName = tinycolor(this.color()).toName();
            if (preDefinedColorName != false){
                this.colorName(preDefinedColorName);
            }
        } else {
            this.colorName(updateData.colorName);
        }

        this.flowRateCompensation(updateData.flowRateCompensation);
        this.temperature(updateData.temperature);
        this.bedTemperature(updateData.bedTemperature);
        this.enclosureTemperature(updateData.enclosureTemperature);
        this.offsetTemperature(updateData.offsetTemperature);
        this.offsetBedTemperature(updateData.offsetBedTemperature);
        this.offsetEnclosureTemperature(updateData.offsetEnclosureTemperature);
        this.totalWeight(parseFloat(updateData.totalWeight));
        this.spoolWeight(parseFloat(updateData.spoolWeight));
        this.remainingWeight(parseFloat(updateData.remainingWeight));
        this.remainingPercentage(updateData.remainingPercentage);
        this.code(updateData.code);
        this.usedPercentage(updateData.usedPercentage);

        this.totalLength(updateData.totalLength);
        this.usedLength(updateData.usedLength);
        this.usedLengthPercentage(updateData.usedLengthPercentage);
        this.remainingLength(updateData.remainingLength);
        this.remainingLengthPercentage(updateData.remainingLengthPercentage);
        this.usedWeight(parseFloat(updateData.usedWeight));

        this.firstUse(updateData.firstUse);
        this.lastUse(updateData.lastUse);
        this.purchasedOn(updateData.purchasedOn);
        if (updateData.firstUse){
            var convertedDateTime = moment(data.firstUse, "DD.MM.YYYY HH:mm").format("YYYY-MM-DDTHH:mm")
            this.firstUseKO(convertedDateTime);
        }
        if (updateData.lastUse){
            var convertedDateTime = moment(data.lastUse, "DD.MM.YYYY HH:mm").format("YYYY-MM-DDTHH:mm")
            this.lastUseKO(convertedDateTime);
        }
        if (updateData.purchasedOn){
            var convertedDateTime = moment(data.purchasedOn, "DD.MM.YYYY").format("YYYY-MM-DD")
            this.purchasedOnKO(convertedDateTime);
        }

        this.purchasedFrom(updateData.purchasedFrom);

        this.cost(updateData.cost);
        this.costUnit(updateData.costUnit);

        // update label selections
        if (updateData.labels != null){
            this.labels.removeAll();
            selectedLabels = updateData.labels
            if (Array.isArray(updateData.labels) == false){
                selectedLabels = JSON.parse(updateData.labels)
            }
            ko.utils.arrayPushAll(this.labels, selectedLabels);
        }

        // assign content to the Note-Section
        // fill Obseravbles
        this.noteText(updateData.noteText);
        this.noteDeltaFormat(updateData.noteDeltaFormat);
        if (updateData.noteHtml != null){
            this.noteHtml(updateData.noteHtml);
        } else {
            // Fallback text
            this.noteHtml(updateData.noteText);
        }
        // fill editor
        if (self.noteEditor != null){
            if (updateData.noteDeltaFormat == null || updateData.noteDeltaFormat.length == 0) {
                // Fallback is text (if present), not Html
                if (updateData.noteText != null){
                    self.noteEditor.setText(updateData.noteText, 'api');
                } else {
                    self.noteEditor.setText("", 'api');
                }
            }else {
                    deltaFormat = JSON.parse(updateData.noteDeltaFormat);
                    self.noteEditor.setContents(deltaFormat, 'api');
            }
        }

        // Calculate derived fields (these exists only in this view model)
        this.totalCombinedWeight(_getValueOrZero(updateData.totalWeight) + _getValueOrZero(updateData.spoolWeight));
        this.remainingCombinedWeight(_getValueOrZero(updateData.remainingWeight) + _getValueOrZero(updateData.spoolWeight));

        self.autoUpdateEnabled = true;
    };


    ///////////////////////////////////////////////////////////////////////////////////////////////// Instance Variables
    self.componentFactory = new ComponentFactory();
    self.spoolDialog = null;
    self.templateSpoolDialog = null;
    self.closeDialogHandler = null;
    self.spoolItemForEditing = null;
    self.templateSpools = ko.observableArray([]);

    self.noteEditor = null;

    // Do I need these viewModels?
    self.firstUseDatePickerModel = null;
    self.lastUseDatePickerModel = null;
    self.purchasedOndatePickerModel = null;
    self.labelsViewModel = null;
    self.filamentColorViewModel = null;
    self.materialViewModel = null;

    self.catalogs = null;
    self.allMaterials = ko.observableArray([]);
    self.allVendors = ko.observableArray([]);
    self.allColors = ko.observableArray([]);
    self.allPurchasedFrom = ko.observableArray([]);

    self.allToolIndices = ko.observableArray([]);

    // Knockout stuff
    this.isExistingSpool = ko.observable(false);
    this.spoolSelectedByQRCode = ko.observable(false);


    ///////////////////////////////////////////////////////////////////////////////////////////////////////////// HELPER

    self.isFormValidForSubmit = ko.pureComputed(function () {
        if (self._checkMandatoryFields() == false){
            return false;
        }
        if (self._checkDateTimeFormats() == false){
            return false;
        }

        return true;
    });

    self._checkMandatoryFields = function(){
        // "Displayname", "total weight", "color name/code"
        let namePresent = self.isDisplayNamePresent();
        if (namePresent == false){
            return false;
        }
        let colorNametPresent = self.isColorNamePresent();
        if (colorNametPresent == false){
            return false;
        }
        let weightPresent = self.isTotalCombinedWeightPresent();
        if (weightPresent == false){
            return false;
        }
        return true;
    }

    self._checkDateTimeFormats = function(){

        // "First/LastUse", "purchasedOn"
        let firstUse = self.spoolItemForEditing.firstUseKO()
        if (firstUse && firstUse.trim().length != 0){
            if (moment(firstUse, "YYYY-MM-DDTHH:mm").isValid() == false){
                return false;
            }
        }
        let lastUse = self.spoolItemForEditing.lastUseKO()
        if (lastUse && lastUse.trim().length != 0){
            if (moment(lastUse, "YYYY-MM-DDTHH:mm").isValid() == false){
                return false;
            }
        }
        let purchasedOn = self.spoolItemForEditing.purchasedOnKO()
        if (purchasedOn && purchasedOn.trim().length != 0){
            if (moment(purchasedOn, "YYYY-MM-DD").isValid() == false){
                return false;
            }
        }
        return true;
    }

    self.isDisplayNamePresent = function(){
        var displayName = self.spoolItemForEditing.displayName();
        return (!displayName || displayName.trim().length === 0) == false;
    }

    self.isColorNamePresent = function(){
        var colorName = self.spoolItemForEditing.colorName();
        return (!colorName || colorName.trim().length === 0) == false;
    }

    self.isTotalCombinedWeightPresent = function(){
        var totalCombinedWeight = self.spoolItemForEditing.totalCombinedWeight();
        return (!totalCombinedWeight || (""+totalCombinedWeight).trim().length === 0) == false;
    }

    // self.transform2Date = function(dateValue){
    //     if (dateValue == null){
    //         return null;
    //     }
    //     if (dateValue instanceof Date){
    //         return dateValue;
    //     }
    //     return new Date(dateValue);
    // }

//    self.getValueOrDefault = function(data, attribute, defaultValue){
//        if (data == null){
//            return defaultValue;
//        }
//        var value = data[attribute];
//        if (value == null || value == undefine){
//            return defaultValue;
//        }
//        return value;
//    }

    function _roundTo(x, precision) {
        var increments = Math.pow(10, precision);
        return Math.round((x + Number.EPSILON) * increments) / increments;
    }

    this._reColorFilamentIcon = function(newColor){
        var loopCount = 0;
        var primaryColor = newColor; //"#FF1D25"
        var secondaryColor = tinycolor(primaryColor).darken(12).toString();
        //            console.info(primaryColor);
        //            console.info(secondaryColor);
        var svgIcon = $("#svg-filament")
        svgIcon.children("rect").each(function(loopIndex){
            if (loopIndex %2 == 0){
                //Change color of filament
                $(this).attr("fill",primaryColor);

            } else {
                //Change color of filament
                $(this).attr("fill",secondaryColor);
            }
            loopCount++;
        });
        svgIcon.children("path").each(function(loopIndex){
            $(this).attr("stroke",primaryColor);
        });
    };

    function _getValueOrZero(x) {
        if (!x){
            x = 0
        }
        return parseFloat(x);
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////// PUBLIC
    this.initBinding = function(apiClient, pluginSettings, printerProfilesViewModel){

        self.autoUpdateEnabled = false;
        self.apiClient = apiClient;
        self.pluginSettings = pluginSettings;
        self.printerProfilesViewModel = printerProfilesViewModel;

        self.spoolDialog = $("#dialog_spool_edit");
        self.templateSpoolDialog = $("#dialog_template_spool_selection");

        self.noteEditor = new Quill('#spool-note-editor', {
            modules: {
                toolbar: [
                    ['bold', 'italic', 'underline'],
                    [{ 'color': [] }, { 'background': [] }],
                    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                    ['link']
                ]
            },
            theme: 'snow'
        });

        Quill.prototype.getHtml = function() {
            return this.container.querySelector('.ql-editor').innerHTML;
        };

        // initial coloring
        self._createSpoolItemForEditing();
        self._reColorFilamentIcon(self.spoolItemForEditing.color());
        self.spoolItemForEditing.color.subscribe(function(newColor){
            self._reColorFilamentIcon(newColor);
            var colorName = tinycolor(newColor).toName();
            if (colorName != false){
                self.spoolItemForEditing.colorName(colorName);
            }
        });
        // ----------------- start: weight stuff
        var remainingWeightKo = self.spoolItemForEditing.remainingWeight;
        var totalWeightKo = self.spoolItemForEditing.totalWeight;
        var usedWeightKo = self.spoolItemForEditing.usedWeight;
        var remainingCombinedWeightKo = self.spoolItemForEditing.remainingCombinedWeight;
        var spoolWeightKo = self.spoolItemForEditing.spoolWeight;
        var totalCombinedWeightKo = self.spoolItemForEditing.totalCombinedWeight;
        var totalLengthKo = self.spoolItemForEditing.totalLength;
        var usedLengthKo = self.spoolItemForEditing.usedLength;
        var remainingLengthKo = self.spoolItemForEditing.remainingLength;
        var densityKo = self.spoolItemForEditing.density;
        var diameterKo = self.spoolItemForEditing.diameter;
        var usedPercentageKo = self.spoolItemForEditing.usedPercentage;
        var remainingPercentageKo = self.spoolItemForEditing.remainingPercentage;
        var usedLengthPercentageKo = self.spoolItemForEditing.usedLengthPercentage;
        var remainingLengthPercentageKo = self.spoolItemForEditing.remainingLengthPercentage;
        var drivenScopeKo = self.spoolItemForEditing.drivenScope;

        function addition(a, b) {
            return a + b;
        }

        function subtraction(a, b) {
            return a - b;
        }

        // Subscriptions for auto updates

        totalWeightKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(totalWeightKo);
            if (drivenScopeKo() === SPOOL) {
                self.updateSpoolWithScopes();
            } else {
                self.updateCombinedInitialWithScopes();
            }
            self.updateFilamentRemainingWithStates();
            self.doUnitConversion(totalWeightKo, totalLengthKo, self.convertToLength);
            self.updatePercentages(usedPercentageKo, remainingPercentageKo, totalWeightKo, usedWeightKo);
            self.resetLocksIf(iAmRootChange);
        });

        totalLengthKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(totalLengthKo);
            self.doUnitConversion(totalLengthKo, totalWeightKo, self.convertToWeight);
            self.updatePercentages(usedLengthPercentageKo, remainingLengthPercentageKo, totalLengthKo, usedLengthKo);
            self.resetLocksIf(iAmRootChange);
        });

        usedWeightKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(usedWeightKo);
            self.doUnitConversion(usedWeightKo, usedLengthKo, self.convertToLength);
            self.updateFilamentRemainingWithStates();
            self.updatePercentages(usedPercentageKo, remainingPercentageKo, totalWeightKo, usedWeightKo);
            self.resetLocksIf(iAmRootChange);
        });

        usedLengthKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(usedLengthKo);
            self.doUnitConversion(usedLengthKo, usedWeightKo, self.convertToWeight);
            self.updatePercentages(usedLengthPercentageKo, remainingLengthPercentageKo, totalLengthKo, usedLengthKo);
            self.resetLocksIf(iAmRootChange);
        });

        remainingWeightKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(remainingWeightKo);
            if (drivenScopeKo() === COMBINED) {
                self.updateCombinedRemainingWithScopes();
            }
            self.updateFilamentUsedWithStates();
            self.doUnitConversion(remainingWeightKo, remainingLengthKo, self.convertToLength);
            self.updatePercentages(usedPercentageKo, remainingPercentageKo, totalWeightKo, usedWeightKo);
            self.resetLocksIf(iAmRootChange);
        });

        remainingLengthKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(remainingLengthKo);
            self.doUnitConversion(remainingLengthKo, remainingWeightKo, self.convertToWeight);
            self.updatePercentages(usedLengthPercentageKo, remainingLengthPercentageKo, totalLengthKo, usedLengthKo);
            self.resetLocksIf(iAmRootChange);
        });

        densityKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(densityKo);
            self.convertAllUnits();
            self.resetLocksIf(iAmRootChange);
        })

        diameterKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(diameterKo);
            self.convertAllUnits();
            self.resetLocksIf(iAmRootChange);
        })

        spoolWeightKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(spoolWeightKo);
            if (drivenScopeKo() === FILAMENT) {
                self.updateFilamentInitialWithScopes();
            } else if (drivenScopeKo() === COMBINED) {
                self.updateCombinedInitialWithScopes();
                self.updateCombinedRemainingWithScopes();
            }
            self.resetLocksIf(iAmRootChange);
        });

        totalCombinedWeightKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(totalCombinedWeightKo);
            if (drivenScopeKo() === FILAMENT) {
                self.updateFilamentInitialWithScopes();
            } else if (drivenScopeKo() === SPOOL) {
                self.updateSpoolWithScopes();
            }
            self.resetLocksIf(iAmRootChange);
        });

        remainingCombinedWeightKo.subscribe(function (newValue) {
            var iAmRootChange = self.amIRootChange(remainingCombinedWeightKo);
            if (drivenScopeKo() === FILAMENT) {
                self.updateFilamentRemainingWithScopes();
            }
            self.resetLocksIf(iAmRootChange);
        });

        // Update functions

        self.updateFilamentRemainingWithStates = function () {
            self.safeUpdate(remainingWeightKo, subtraction, [totalWeightKo, usedWeightKo]);
        };

        self.updateFilamentRemainingWithScopes = function () {
            self.safeUpdate(remainingWeightKo, subtraction, [remainingCombinedWeightKo, spoolWeightKo]);
        };

        self.updateFilamentUsedWithStates = function () {
            self.safeUpdate(usedWeightKo, subtraction, [totalWeightKo, remainingWeightKo]);
        };

        self.updateFilamentInitialWithScopes = function () {
            self.safeUpdate(totalWeightKo, subtraction, [totalCombinedWeightKo, spoolWeightKo]);
        };

        self.updateSpoolWithScopes = function () {
            self.safeUpdate(spoolWeightKo, subtraction, [totalCombinedWeightKo, totalWeightKo]);
        };

        self.updateCombinedInitialWithScopes = function () {
            self.safeUpdate(totalCombinedWeightKo, addition, [totalWeightKo, spoolWeightKo]);
        };

        self.updateCombinedRemainingWithScopes = function () {
            self.safeUpdate(remainingCombinedWeightKo, addition, [remainingWeightKo, spoolWeightKo]);
        };

        self.convertAllUnits = function () {
            self.doUnitConversion(totalWeightKo, totalLengthKo, self.convertToLength);
            self.doUnitConversion(totalLengthKo, totalWeightKo, self.convertToWeight);
            self.doUnitConversion(usedWeightKo, usedLengthKo, self.convertToLength);
            self.doUnitConversion(usedLengthKo, usedWeightKo, self.convertToWeight);
            self.doUnitConversion(remainingWeightKo, remainingLengthKo, self.convertToLength);
            self.doUnitConversion(remainingLengthKo, remainingWeightKo, self.convertToWeight);
        };

        self.doUnitConversion = function (sourceKo, targetKo, converter) {
            var source = parseFloat(sourceKo());
            if (isNaN(source) || !self.areDensityAndDiameterValid() || !self.getLock(targetKo)) {
                return;
            }
            self.getLock(sourceKo);
            targetKo(converter(source, parseFloat(densityKo()), parseFloat(diameterKo())));
        };

        self.updatePercentages = function (usedPercentageKo, remainPercentageKo, totalKo, usedKo) {
            var total = parseFloat(totalKo());
            var used = parseFloat(usedKo());
            if (isNaN(total) || total <= 0
                || isNaN(used) || used < 0 || used > total) {
                usedPercentageKo(NaN);
                remainPercentageKo(NaN);
                return;
            }
            var usedPercentage = _roundTo(
                100 * used / total,
                0
            );
            usedPercentageKo(usedPercentage);
            remainPercentageKo(100 - usedPercentage);
        };

        self.safeUpdate = function (targetKo, calcFn, calcFnArguments) {
            if (!self.getLock(targetKo)) {
                return;
            }

            function getValueOrZero(x) {
                return parseFloat(x()) || 0;
            }

            targetKo(_roundTo(
                calcFn.apply(null, calcFnArguments.map(getValueOrZero)),
                1
            ));
        };

        // helper functions

        self.areDensityAndDiameterValid = function () {
            var diameter = parseFloat(diameterKo());
            var density = parseFloat(densityKo());
            return (!isNaN(diameter) && diameter > 0
                && !isNaN(density) && density > 0);
        };

        self.convertToLength = function (weight, density, diameter) {
            var volume = weight / (density *  Math.pow(10, -3)); // [mm^3] = [g] / ( [g/cm^3] * 10^-3 )
            var area = (Math.PI / 4) * Math.pow(diameter, 2); // [mm^2] = pi/4 * [mm]^2
            return _roundTo(volume / area, 0); // [mm] = [mm^3] / [mm^2}
        };

        self.convertToWeight = function (length, density, diameter) {
            var area = (Math.PI / 4) * Math.pow(diameter, 2); // [mm^2] = pi/4 * [mm]^2
            var volume = area * length; // [mm^3] = [mm^2] * [mm]
            return _roundTo(volume * density * Math.pow(10, -3), 1); // [g] = [mm^3] * [g/cm^3] * 10^3
        };

        // lock mechanism to prevent infinite update loops

        self.locksOfInProgressUpdate = [];
        self.getLock = function (updatableEntity) {
            if (!self.autoUpdateEnabled || self.locksOfInProgressUpdate.includes(updatableEntity)) {
                return false;
            }
            self.locksOfInProgressUpdate.push(updatableEntity);
            return true;
        };
        self.resetLocksIf = function (condition) {
            if (condition) {
                self.locksOfInProgressUpdate = [];
            }
        };
        self.amIRootChange = function (source) {
            return self.locksOfInProgressUpdate.length === 0 && self.getLock(source);
        };

        // ----------------- end: weight stuff
    }

    this.afterBinding = function(){
    }

    this._createSpoolItemForEditing = function(){
        self.spoolItemForEditing = new SpoolItem(null, true);

        self.spoolItemForEditing.isInActive.subscribe(function(newValue){
            self.spoolItemForEditing.isActive(!newValue);
        });

        return self.spoolItemForEditing;
    }

    this.createSpoolItemForTable = function(spoolData){
        var newSpoolItem = new SpoolItem(spoolData, false);
        return newSpoolItem;
    }

    this.updateCatalogs = function(allCatalogs){
        self.catalogs = allCatalogs;
        if (self.catalogs != null){
            self.allMaterials(self.catalogs["materials"]);
            self.allVendors(self.catalogs["vendors"]);
            self.allColors(self.catalogs["colors"]);
            self.allPurchasedFrom(self.catalogs["purchasedFrom"]);
        } else {
            self.allMaterials([]);
            self.allVendors([]);
            self.allColors([]);
            self.allPurchasedFrom([]);
        }

    }

    this.updateTemplateSpools = function(templateSpoolsData){

        var spoolItemsArray = [];
        if (templateSpoolsData != null && templateSpoolsData.length !=0){
            spoolItemsArray = ko.utils.arrayMap(templateSpoolsData, function (spoolData) {
                var result = self.createSpoolItemForTable(spoolData);
                return result;
            });
        }
        self.templateSpools(spoolItemsArray);
    }

    this.showDialog = function(spoolItem, closeDialogHandler){
        self.autoUpdateEnabled = false;
        self.closeDialogHandler = closeDialogHandler;
        // get the current tool caunt
        self.allToolIndices([]);
        var toolCount = self.printerProfilesViewModel.currentProfileData().extruder.count();
        for (var toolIndex=0; toolIndex<toolCount; toolIndex++){
            self.allToolIndices.push(toolIndex);
        }

        // initial coloring
        self._reColorFilamentIcon(self.spoolItemForEditing.color());

        if (spoolItem == null){
            // New Spool
            self.isExistingSpool(false);
            // reset values for a new spool
            self.spoolItemForEditing.update({});
            // self.spoolItemForEditing.isActive(true);
            self.spoolItemForEditing.isInActive(false);
            // self.spoolItemForEditing.isTemplate(false);
            // self.spoolItemForEditing.isActive(true);
            // self.spoolItemForEditing.databaseId(null);
            // self.spoolItemForEditing.costUnit(self.pluginSettings.currencySymbol());
            // self.spoolItemForEditing.displayName(null);
            // self.spoolItemForEditing.totalWeight(0.0);
            // self.spoolItemForEditing.usedWeight(0.0);
            // self.spoolItemForEditing.totalLength(0);
            // self.spoolItemForEditing.usedLength(0);
            // self.spoolItemForEditing.firstUse(null);
            // self.spoolItemForEditing.firstUseKO(null);
            // self.spoolItemForEditing.lastUse(null);
            // self.spoolItemForEditing.lastUseKO(null);
            // self.spoolItemForEditing.purchasedOn(null);
            // self.spoolItemForEditing.purchasedOnKO(null);
            // self.spoolItemForEditing.remainingCombinedWeight(0);
            // self.spoolItemForEditing.totalCombinedWeight(0);
        } else {
            self.isExistingSpool(true);
            // Make a copy of provided spoolItem
            spoolItemCopy = ko.mapping.toJS(spoolItem);
            self.spoolItemForEditing.update(spoolItemCopy);
        }
        self.spoolItemForEditing.drivenScope(COMBINED); // default calculation mode
        self.spoolItemForEditing.isSpoolVisible(true);

        self.spoolDialog.modal({
            minHeight: function() { return Math.max($.fn.modal.defaults.maxHeight() - 180, 250); },
            keyboard: false,
            clickClose: true,
            showClose: false,
            backdrop: "static"
        })
        .css({
            width: 'auto',
            'margin-left': function() { return -($(this).width() /2); }
        });


        self.autoUpdateEnabled = true;
    };

    self.copySpoolItem = function(){
        self._copySpoolItemForEditing(self.spoolItemForEditing);
    }

    self.copySpoolItemFromTemplate = function(spoolItem){
        // Copy everything
        self._copySpoolItemForEditing(spoolItem);
        // reset values that should'nt be copied


        var defaultExcludedFields = ["selectedForTool","version", "databaseId", "isTemplate","firstUseKO", "lastUseKO",
                                    "remainingWeight","remainingPercentage","usedLength", "usedLengthPercentage","remainingLength", "remainingLengthPercentage",
                                    "usedWeight", "usedPercentage", "totalCombinedWeight", "remainingCombinedWeight"];
        var allFieldNames = Object.keys(spoolItem);
        for (const fieldName of allFieldNames){
            if (self.pluginSettings.excludedFromTemplateCopy().includes(fieldName) ||
                defaultExcludedFields.includes(fieldName)){
                var currentValue = self.spoolItemForEditing[fieldName]();
                self.spoolItemForEditing[fieldName]("");
            }
        }
        if (self.pluginSettings.excludedFromTemplateCopy().includes("allNotes")) {
            if (self.noteEditor != null) {
                self.noteEditor.setText("", 'api');
            }
            // self.spoolItemForEditing["noteText"]("");
            // self.spoolItemForEditing["noteDeltaFormat"]("");
            // self.spoolItemForEditing["noteHtml"]("");
        }

        // close dialog
        self.templateSpoolDialog.modal('hide');
    }

    self._copySpoolItemForEditing = function(spoolItem){
        self.isExistingSpool(false);
        let spoolItemCopy = ko.mapping.toJS(spoolItem);
        self.spoolItemForEditing.update(spoolItemCopy);
        self.spoolItemForEditing.isTemplate(false);
        // self.spoolItemForEditing.isActive(true);  is set by 'isInActive'
        self.spoolItemForEditing.isInActive(false);
        self.spoolItemForEditing.databaseId(null);
        self.spoolItemForEditing.isSpoolVisible(true);
    }

    self.saveSpoolItem = function(){

        // Input validation
        var displayName = self.spoolItemForEditing.displayName();
        if (!displayName || displayName.trim().length === 0){
            alert("Displayname not entered!");
            return;
        }
        // workaround
        self.spoolItemForEditing.costUnit(self.pluginSettings.currencySymbol())

        var noteText = self.noteEditor.getText();
        var noteDeltaFormat = self.noteEditor.getContents();
        var noteHtml = self.noteEditor.getHtml();

        self.spoolItemForEditing.noteText(noteText);
        self.spoolItemForEditing.noteDeltaFormat(noteDeltaFormat);
        self.spoolItemForEditing.noteHtml(noteHtml);

        // read current note values and push to item, because there is no 2-way binding

//        self.printJobItemForEdit.noteText(noteText);
//        self.printJobItemForEdit.noteDeltaFormat(noteDeltaFormat);
//        self.printJobItemForEdit.noteHtml(noteHtml);
//
        self.apiClient.callSaveSpool(self.spoolItemForEditing, function(allPrintJobsResponse){
            self.spoolItemForEditing.isSpoolVisible(false);
            self.spoolDialog.modal('hide');
            // var specialCloseAction = self.isExistingSpool() == false ? "saveNewSpool"
            self.closeDialogHandler(true, "save");
        });
    }

    self.deleteSpoolItem = function(){
        var result = confirm("Do you really want to delete this spool?");
        if (result == true){
            self.apiClient.callDeleteSpool(self.spoolItemForEditing.databaseId(), function(responseData) {
                self.spoolItemForEditing.isSpoolVisible(false);
                self.spoolDialog.modal('hide');
                self.closeDialogHandler(true);
            });
        }
    }

    self.selectSpoolItemForPrinting = function(){
        self.spoolItemForEditing.isSpoolVisible(false);
        self.spoolDialog.modal('hide');
        self.closeDialogHandler(false, "selectSpoolForPrinting", self.spoolItemForEditing);
    }

    self.selectAndCopyTemplateSpool = function(){

        /* needed for Filter-Search dropdown-menu */
        $('.dropdown-menu.keep-open').click(function(e) {
            e.stopPropagation();
        });

        self.templateSpoolDialog.modal({
                minHeight: function () {
                    return Math.max($.fn.modal.defaults.maxHeight() - 80, 250);
                },
                show: true
            });
    }
}
