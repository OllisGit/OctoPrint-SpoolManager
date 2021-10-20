"use strict";
 // START: TESTZONE
$(function() {

});


    function machwas(myObj){
//        $("#configFields").addClass('open');
        //debugger
        //$("#openConfigFields").dropdown();

    }
/*
    var specifiedElement = document.getElementById('configFieldsDropDown');

    document.addEventListener('click', function(event) {
        var isClickInside = specifiedElement.contains(event.target);
        if (isClickInside) {
          console.log('You clicked inside')
        }
        else {
//          debugger
          console.log('You clicked outside');


          if (event.target.id == "openConfigFields" &&  $("#configFields").hasClass("open") == false){
            $("#configFields").addClass('open');
          } else


          if (event.target.id != "openConfigFields" ||
              (event.target.id == "openConfigFields" && $("#configFields").hasClass("open"))){
              $("#configFields").removeClass('open');
          }
        }
    });
*/
 // END: TESTZONE

function SpoolManagerEditSpoolDialog(){

    var self = this;

    ///////////////////////////////////////////////////////////////////////////////////////////////////////// ITEM MODEL
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

    var SpoolItem = function(spoolData, editable) {
        // Init Item

        // if we use the Item for Editing we need to initialise the widget-model as well , e.g. Option-Values, Suggestion-List
        // if we just use this Item in readonly-mode we need simple ko.observer

        // FormatHelperFunction
        this.formatOnlyDate = function (data, dateBindingName) {
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
        // - list all attributes
        this.version = ko.observable();
        this.isSpoolVisible = ko.observable(false);
        this.isEmpty = ko.observable();
        this.databaseId = ko.observable();
        this.isTemplate = ko.observable();
        this.isActive = ko.observable();
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
        this.purchasedOn = ko.observable();

        this.purchasedFrom = ko.observable();
        this.cost = ko.observable();
        this.costUnit = ko.observable();

        // Non-persistent fields (these exist only in this view model)
        this.totalCombinedWeight = ko.observable();
        this.remainingCombinedWeight = ko.observable();
        this.drivenScope = ko.observable();
        this.drivenScopeOptions = ko.observableArray([
            {
                text: "Filament Weight",
                value: FILAMENT,
            },
            {
                text: "Empty Spool Weight",
                value: SPOOL,
            },
            {
                text: "Combined Weight",
                value: COMBINED,
            },
        ]);


        // Assign default values for editing
        // overwrite and/or add attributes
        var vendorViewModel = self.componentFactory.createSelectWithFilter("spool-vendor-select", $('#spool-form'));
        this.vendor = vendorViewModel.selectedOption;
        this.allVendors = vendorViewModel.allOptions;

        var materialViewModel = self.componentFactory.createSelectWithFilter("spool-material-select", $('#spool-form'));
        this.material = materialViewModel.selectedOption;
        this.allMaterials = materialViewModel.allOptions;

        // Autosuggest for "density"
        this.material.subscribe(function(newMaterial){
            if ($("#dialog_spool_select").is(":visible")){
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
        this.labels = self.labelsViewModel.selectedOptions;
        this.allLabels = self.labelsViewModel.allOptions;



        // Fill Item with data
        this.update(spoolData);
    }

    SpoolItem.prototype.update = function (data) {
        self.autoUpdateEnabled = false;
        var updateData = data || {}

        // update latest all catalog
        if (self.catalogs != null){
            // labels
            this.allLabels.removeAll();
            ko.utils.arrayPushAll(this.allLabels, self.catalogs.labels);
            // materials
            this.allMaterials(self.catalogs.materials);

            //vendors
            this.allVendors(self.catalogs.vendors);
        }

        this.selectedFromQRCode(updateData.selectedFromQRCode);
        this.selectedForTool(updateData.selectedForTool);
        this.isEmpty(data == null);
        this.version(updateData.version);
        this.databaseId(updateData.databaseId);
        this.isTemplate(updateData.isTemplate);
        this.isActive(updateData.isActive);
        this.displayName(updateData.displayName);
        this.vendor(updateData.vendor);

        this.material(updateData.material);
        this.density(updateData.density);
        this.diameter(updateData.diameter);
        this.diameterTolerance(updateData.diameterTolerance);
        this.colorName(updateData.colorName);
        this.color(updateData.color == null ? DEFAULT_COLOR : updateData.color);

        if (this.colorName()==null || this.colorName().length == 0){
            var colorName = tinycolor(this.color()).toName();
            if (colorName != false){
                this.colorName(colorName);
            }
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
                var deltaFormat = JSON.parse(updateData.noteDeltaFormat);
                self.noteEditor.setContents(deltaFormat, 'api');
            }
        }

        // Calculate derived fields (these exist only in this view model)
        this.totalCombinedWeight(parseFloat(updateData.totalWeight) + parseFloat(updateData.spoolWeight));
        this.remainingCombinedWeight(parseFloat(updateData.remainingWeight) + parseFloat(updateData.spoolWeight));

        self.autoUpdateEnabled = true;
    };


    ///////////////////////////////////////////////////////////////////////////////////////////////// Instance Variables
    self.componentFactory = new ComponentFactory();
    self.spoolDialog = null;
    self.closeDialogHandler = null;
    self.spoolItemForEditing = null;
    self.templateSpool = new SpoolItem({}, false);

    self.noteEditor = null;

    // Do I need these viewModels?
    self.firstUseDatePickerModel = null;
    self.lastUseDatePickerModel = null;
    self.purchasedOndatePickerModel = null;
    self.labelsViewModel = null;
    self.filamentColorViewModel = null;
    self.materialViewModel = null;

    self.catalogs = null;
    self.allToolIndices = ko.observableArray([]);

    //    Option to filter Attributes
//    SpoolItem.prototype.toJSON = function() {
//        var copy = ko.toJS(this); //easy way to get a clean copy
//        // delete
//      return copy; //return the copy to be serialized
//    };

//    // FIX Date, if you select 01.06 -> 31.05
//    Date.prototype.toJSON = function () {
//        debugger
//      var timezoneOffsetInHours = -(this.getTimezoneOffset() / 60); //UTC minus local time
//      var sign = timezoneOffsetInHours >= 0 ? '+' : '-';
//      var leadingZero = (Math.abs(timezoneOffsetInHours) < 10) ? '0' : '';
//
//      //It's a bit unfortunate that we need to construct a new Date instance
//      //(we don't want _this_ Date instance to be modified)
//      var correctedDate = new Date(this.getFullYear(), this.getMonth(),
//          this.getDate(), this.getHours(), this.getMinutes(), this.getSeconds(),
//          this.getMilliseconds());
//      correctedDate.setHours(this.getHours() + timezoneOffsetInHours);
//      var iso = correctedDate.toISOString().replace('Z', '');
//
//      return iso + sign + leadingZero + Math.abs(timezoneOffsetInHours).toString() + ':00';
//    }

    self.transform2Date = function(dateValue){
        if (dateValue == null){
            return null;
        }
        if (dateValue instanceof Date){
            return dateValue;
        }
        return new Date(dateValue);
    }

    //////////////////////////////////////////////////////////////////////////////////////////////////////////// PRIVATE

    // Knockout stuff
    this.isExistingSpool = ko.observable(false);
    this.spoolSelectedByQRCode = ko.observable(false);

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

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////// PUBLIC
    this.initBinding = function(apiClient, pluginSettings, printerProfilesViewModel){
        self.autoUpdateEnabled = false;

        self.apiClient = apiClient;
        self.pluginSettings = pluginSettings;
        self.printerProfilesViewModel = printerProfilesViewModel;

        self.spoolDialog = $("#dialog_spool_select");
//        self.firstUseDatePickerModel = self.componentFactory.createDatePicker("firstUse-date-container");
////        self.firstUseDatePickerModel.currentDate(new Date(2014, 1, 14));
//
//        self.lastUseDatePickerModel = self.componentFactory.createDatePicker("lastUse-date-container");
//        self.purchasedOnDatePickerModel = self.componentFactory.createDatePicker("purchasedOn-date-container");

//        self.labelsViewModel = self.componentFactory.createLabels("spool-labels", $('#spool-form'));
//        self.labelsViewModel.allOptions.push('FirstLabel','SecondLabel');
//        self.labelsViewModel.selectedOptions.push('FirstLabel','SecondLabel');



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
            var usedPercentage = roundTo(
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

            targetKo(roundTo(
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
            return roundTo(volume / area, 0); // [mm] = [mm^3] / [mm^2}
        };

        self.convertToWeight = function (length, density, diameter) {
            var area = (Math.PI / 4) * Math.pow(diameter, 2); // [mm^2] = pi/4 * [mm]^2
            var volume = area * length; // [mm^3] = [mm^2] * [mm]
            return roundTo(volume * density * Math.pow(10, -3), 1); // [g] = [mm^3] * [g/cm^3] * 10^3
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

        // ----------------- end: length stuff
    }

    this.afterBinding = function(){
    }

    this._createSpoolItemForEditing = function(){
        self.spoolItemForEditing = new SpoolItem(null, true);
        return self.spoolItemForEditing;
    }

    this.createSpoolItemForTemplate = function(spoolData){
        self.templateSpool =  new SpoolItem(spoolData, false);
    }

    this.createSpoolItemForTable = function(spoolData){
        var newSpoolItem = new SpoolItem(spoolData, false);
        return newSpoolItem;
    }

    this.updateCatalogs = function(catalogs){
        self.catalogs = catalogs;
    }

    this.updateTemplateSpool = function(templateSpoolData){
        if (self.templateSpool == null){
            self.createSpoolItemForTemplate(templateSpoolData)
        } else {
            self.templateSpool.update(templateSpoolData);
        }
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
            var templateSpoolItemCopy = ko.mapping.toJS(self.templateSpool);
            self.spoolItemForEditing.update(templateSpoolItemCopy);
            // reset values for a new spool
            self.spoolItemForEditing.isTemplate(false);
            self.spoolItemForEditing.isActive(true);
            self.spoolItemForEditing.databaseId(null);
            self.spoolItemForEditing.costUnit(self.pluginSettings.currencySymbol());
            self.spoolItemForEditing.displayName(null);
            self.spoolItemForEditing.totalWeight(0.0);
            self.spoolItemForEditing.usedWeight(0.0);
            self.spoolItemForEditing.totalLength(0);
            self.spoolItemForEditing.usedLength(0);
            self.spoolItemForEditing.lastUse(null);
            self.spoolItemForEditing.firstUse(null);
            self.spoolItemForEditing.remainingCombinedWeight(0);
            self.spoolItemForEditing.totalCombinedWeight(0);
//            self.spoolItemForEditing.displayName(null);
//            self.spoolItemForEditing.displayName(null);
//            self.spoolItemForEditing.displayName(null);

        }else{
            self.isExistingSpool(true);
            // Make a copy of provided spoolItem
            var spoolItemCopy = ko.mapping.toJS(spoolItem);
            self.spoolItemForEditing.update(spoolItemCopy);
        }
        self.spoolItemForEditing.drivenScope(COMBINED);

        self.spoolItemForEditing.isSpoolVisible(true);

        self.spoolDialog.modal({
            //minHeight: function() { return Math.max($.fn.modal.defaults.maxHeight() - 80, 250); }
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

    this.copySpoolItem = function(){
        self.isExistingSpool(false);
        var spoolItemCopy = ko.mapping.toJS(self.spoolItemForEditing);
        self.spoolItemForEditing.update(spoolItemCopy);
        self.spoolItemForEditing.isTemplate(false);
        self.spoolItemForEditing.isActive(true);
        self.spoolItemForEditing.databaseId(null);
        self.spoolItemForEditing.isSpoolVisible(true);
    }

    this.saveSpoolItem = function(){

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
            self.closeDialogHandler(true);
        });
    }

    this.deleteSpoolItem = function(){
        var result = confirm("Do you really want to delete this spool?");
        if (result == true){
            self.apiClient.callDeleteSpool(self.spoolItemForEditing.databaseId(), function(responseData) {
                self.spoolItemForEditing.isSpoolVisible(false);
                self.spoolDialog.modal('hide');
                self.closeDialogHandler(true);
            });
        }
    }

    this.selectSpoolItemForPrinting = function(){
        self.spoolItemForEditing.isSpoolVisible(false);
        self.spoolDialog.modal('hide');
        self.closeDialogHandler(true, "selectSpoolForPrinting", self.spoolItemForEditing);
    }

    this.generateQRCodeImageSourceAttribute = function(){
        //
        // <img loading="lazy" className="qr-code" alt="QR Code"
        //      data-bind="attr: {src: '/plugin/SpoolManager/generateQRCode/'+spoolDialog.spoolItemForEditing.databaseId() }"
        //      src="/plugin/SpoolManager/generateQRCode/6"><img loading="lazy" className="qr-code" alt="QR Code"
        //                                                       data-bind="attr: {src: '/plugin/SpoolManager/generateQRCode/'+spoolDialog.spoolItemForEditing.databaseId() }"
        //                                                       src="/plugin/SpoolManager/generateQRCode/6">
        // var windowsLocation = window.location.origin;
        // var windowsLocationEncoded = encodeURIComponent(windowsLocation);
        // var source = "/plugin/SpoolManager/generateQRCode/" + self.spoolItemForEditing.databaseId() + "?windowlocation="+windowsLocationEncoded;
        var source = "/plugin/SpoolManager/generateQRCode/" + self.spoolItemForEditing.databaseId();
        var title = "QR-Code for " + self.spoolItemForEditing.displayName();
        return {
            src: source,
            href: source,
            title: title
        }
    }
}

function roundTo(x, precision) {
    var increments = Math.pow(10, precision);
    return Math.round((x + Number.EPSILON) * increments) / increments;
}
