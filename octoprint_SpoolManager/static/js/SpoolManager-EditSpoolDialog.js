// START: TESTZONE
$(function () {

});


function machwas(myObj) {
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

function SpoolManagerEditSpoolDialog() {

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

    var SpoolItem = function (spoolData, editable) {
        // Init Item

        // if we use the Item for Editing we need to initialise the widget-model as well , e.g. Option-Values, Suggestion-List
        // if we just use this Item in readonly-mode we need simple ko.observer

        // FormatHelperFunction
        formatOnlyDate = function (data, dateBindingName) {
            var dateValue = data[dateBindingName];
            if (dateValue != null && dateValue() != null && dateValue() != "") {
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

        // Assign default values for editing
        // overwrite and/or add attributes
        var vendorViewModel = self.componentFactory.createSelectWithFilter("spool-vendor-select", $('#spool-form'));
        this.vendor = vendorViewModel.selectedOption;
        this.allVendors = vendorViewModel.allOptions;

        var materialViewModel = self.componentFactory.createSelectWithFilter("spool-material-select", $('#spool-form'));
        this.material = materialViewModel.selectedOption;
        this.allMaterials = materialViewModel.allOptions;

        // Autosuggest for "density"
        this.material.subscribe(function (newMaterial) {
            if ($("#dialog_spool_select").is(":visible")) {
                if (self.spoolItemForEditing.isSpoolVisible() == true) {
                    var mat = self.spoolItemForEditing.material();
                    if (mat) {
                        var density = densityMap[mat.toUpperCase()]
                        if (density) {
                            self.spoolItemForEditing.density(density);
                        }
                    }
                }
            }
        });


        if (editable == true) {
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
        var updateData = data || {}

        // update latest all catalog
        if (self.catalogs != null) {
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

        if (this.colorName() == null || this.colorName().length == 0) {
            var colorName = tinycolor(this.color()).toName();
            if (colorName != false) {
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
        this.totalWeight(updateData.totalWeight);
        this.spoolWeight(updateData.spoolWeight);
        this.remainingWeight(updateData.remainingWeight);
        this.remainingPercentage(updateData.remainingPercentage);
        this.code(updateData.code);
        this.usedPercentage(updateData.usedPercentage);

        this.totalLength(updateData.totalLength);
        this.usedLength(updateData.usedLength);
        this.usedLengthPercentage(updateData.usedLengthPercentage);
        this.remainingLength(updateData.remainingLength);
        this.remainingLengthPercentage(updateData.remainingLengthPercentage);
        this.usedWeight(updateData.usedWeight);

        this.firstUse(updateData.firstUse);
        this.lastUse(updateData.lastUse);
        this.purchasedOn(updateData.purchasedOn);

        this.purchasedFrom(updateData.purchasedFrom);

        this.cost(updateData.cost);
        this.costUnit(updateData.costUnit);

        // update label selections
        if (updateData.labels != null) {
            this.labels.removeAll();
            selectedLabels = updateData.labels
            if (Array.isArray(updateData.labels) == false) {
                selectedLabels = JSON.parse(updateData.labels)
            }
            ko.utils.arrayPushAll(this.labels, selectedLabels);
        }

        // assign content to the Note-Section
        // fill Obseravbles
        this.noteText(updateData.noteText);
        this.noteDeltaFormat(updateData.noteDeltaFormat);
        if (updateData.noteHtml != null) {
            this.noteHtml(updateData.noteHtml);
        } else {
            // Fallback text
            this.noteHtml(updateData.noteText);
        }
        // fill editor
        if (self.noteEditor != null) {
            if (updateData.noteDeltaFormat == null || updateData.noteDeltaFormat.length == 0) {
                // Fallback is text (if present), not Html
                if (updateData.noteText != null) {
                    self.noteEditor.setText(updateData.noteText, 'api');
                } else {
                    self.noteEditor.setText("", 'api');
                }
            } else {
                deltaFormat = JSON.parse(updateData.noteDeltaFormat);
                self.noteEditor.setContents(deltaFormat, 'api');
            }
        }
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

    self.transform2Date = function (dateValue) {
        if (dateValue == null) {
            return null;
        }
        if (dateValue instanceof Date) {
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


    this._reColorFilamentIcon = function (newColor) {
        var loopCount = 0;
        var primaryColor = newColor; //"#FF1D25"
        var secondaryColor = tinycolor(primaryColor).darken(12).toString();
        //            console.info(primaryColor);
        //            console.info(secondaryColor);
        var svgIcon = $("#svg-filament")
        svgIcon.children("rect").each(function (loopIndex) {
            if (loopIndex % 2 == 0) {
                //Change color of filament
                $(this).attr("fill", primaryColor);

            } else {
                //Change color of filament
                $(this).attr("fill", secondaryColor);
            }
            loopCount++;
        });
        svgIcon.children("path").each(function (loopIndex) {
            $(this).attr("stroke", primaryColor);
        });
    };

    ///////////////////////////////////////////////////////////////////////////////////////////////////////////// PUBLIC
    this.initBinding = function (apiClient, pluginSettings, printerProfilesViewModel) {

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
                    [{'color': []}, {'background': []}],
                    [{'list': 'ordered'}, {'list': 'bullet'}],
                    ['link']
                ]
            },
            theme: 'snow'
        });

        Quill.prototype.getHtml = function () {
            return this.container.querySelector('.ql-editor').innerHTML;
        };

        // initial coloring
        self._createSpoolItemForEditing();
        self._reColorFilamentIcon(self.spoolItemForEditing.color());
        self.spoolItemForEditing.color.subscribe(function (newColor) {
            self._reColorFilamentIcon(newColor);
            var colorName = tinycolor(newColor).toName();
            if (colorName != false) {
                self.spoolItemForEditing.colorName(colorName);
            }
        });
// ----------------- start: weight stuff
        // update used percentage
        self.updateRemainingValues = function () {
            var total = self.spoolItemForEditing.totalWeight();
            var used = self.spoolItemForEditing.usedWeight();
            // - remaining weight
            if (total != null && used != null) {
                if (isNaN(total) == false && isNaN(used) == false && 0 != total.length && 0 != used.length) {
                    var remainingWeight = (total - used).toFixed(1);
                    console.info("calculated remainWeight:" + remainingWeight);
                    self.spoolItemForEditing.remainingWeight(remainingWeight);
                } else {
                    self.spoolItemForEditing.remainingWeight("");
                }
            } else {
                self.spoolItemForEditing.remainingWeight("");
            }
            // - remaininig percentage
            var remainingWeight = self.spoolItemForEditing.remainingWeight();
            if (total != null && remainingWeight != null) {
                if (isNaN(total) == false && isNaN(remainingWeight) == false) {
                    result = Number(remainingWeight / (total / 100)).toFixed(1);
                    self.spoolItemForEditing.remainingPercentage(result);
                } else {
                    self.spoolItemForEditing.remainingPercentage("");
                }
            }
        }

        // update updateUsedPercentage
        self.updateUsedPercentage = function () {
            var total = self.spoolItemForEditing.totalWeight();
            var used = self.spoolItemForEditing.usedWeight();
            if (total != null && used != null) {
                if (isNaN(total) == false && isNaN(used) == false) {
                    result = Number(used / (total / 100)).toFixed(1);
                    self.spoolItemForEditing.usedPercentage(result);
                } else {
                    self.spoolItemForEditing.usedPercentage("");
                }
            }
        }

        self.spoolItemForEditing.totalWeight.subscribe(function (newValue) {
            self.updateUsedPercentage();
            self.updateRemainingValues();
        });
        self.spoolItemForEditing.usedWeight.subscribe(function (newValue) {
            self.updateUsedPercentage();
            self.updateRemainingValues();
        });
// ----------------- end: weight stuff
// ----------------- start: length stuff
        // update used percentage
        self.updateRemainingLengthValues = function () {
            var total = self.spoolItemForEditing.totalLength();
            var used = self.spoolItemForEditing.usedLength();
            // - remaining weight
            if (total != null && used != null) {
                if (isNaN(total) == false && isNaN(used) == false && 0 != total.length && 0 != used.length) {
                    var remainingLength = (total - used).toFixed(0);
                    console.info("calculated remainLength:" + remainingLength);
                    self.spoolItemForEditing.remainingLength(remainingLength);
                } else {
                    self.spoolItemForEditing.remainingLength("");
                }
            } else {
                self.spoolItemForEditing.remainingLength("");
            }
            // - remaininig percentage
            var remainingLength = self.spoolItemForEditing.remainingLength();
            if (total != null && remainingLength != null) {
                if (isNaN(total) == false && isNaN(remainingLength) == false) {
                    result = Number(remainingLength / (total / 100)).toFixed(0);
                    self.spoolItemForEditing.remainingLengthPercentage(result);
                } else {
                    self.spoolItemForEditing.remainingLengthPercentage("");
                }
            }
        }

        // update updateUsedLengthPercentage
        self.updateUsedLengthPercentage = function () {
            var total = self.spoolItemForEditing.totalLength();
            var used = self.spoolItemForEditing.usedLength();
            if (total != null && used != null) {
                if (isNaN(total) == false && isNaN(used) == false) {
                    result = Number(used / (total / 100)).toFixed(1);
                    self.spoolItemForEditing.usedLengthPercentage(result);
                } else {
                    self.spoolItemForEditing.usedLengthPercentage("");
                }
            }
        }

        self.spoolItemForEditing.totalLength.subscribe(function (newValue) {
            self.updateUsedLengthPercentage();
            self.updateRemainingLengthValues();
        });
        self.spoolItemForEditing.usedLength.subscribe(function (newValue) {
            self.updateUsedLengthPercentage();
            self.updateRemainingLengthValues();
        });
// ----------------- end: length stuff
    }

    this.afterBinding = function () {
    }

    this._createSpoolItemForEditing = function () {
        self.spoolItemForEditing = new SpoolItem(null, true);
        return self.spoolItemForEditing;
    }

    this.createSpoolItemForTemplate = function (spoolData) {
        self.templateSpool = new SpoolItem(spoolData, false);
    }

    this.createSpoolItemForTable = function (spoolData) {
        newSpoolItem = new SpoolItem(spoolData, false);
        return newSpoolItem;
    }

    this.updateCatalogs = function (catalogs) {
        self.catalogs = catalogs;
    }

    this.updateTemplateSpool = function (templateSpoolData) {
        if (self.templateSpool == null) {
            self.createSpoolItemForTemplate(templateSpoolData)
        } else {
            self.templateSpool.update(templateSpoolData);
        }
    }

    this.showDialog = function (spoolItem, closeDialogHandler) {
        self.closeDialogHandler = closeDialogHandler;
        // get the current tool caunt
        self.allToolIndices([]);
        var toolCount = self.printerProfilesViewModel.currentProfileData().extruder.count();
        for (var toolIndex = 0; toolIndex < toolCount; toolIndex++) {
            self.allToolIndices.push(toolIndex);
        }

        // initial coloring
        self._reColorFilamentIcon(self.spoolItemForEditing.color());

        if (spoolItem == null) {
            // New Spool
            self.isExistingSpool(false);
            templateSpoolItemCopy = ko.mapping.toJS(self.templateSpool);
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
//            self.spoolItemForEditing.displayName(null);
//            self.spoolItemForEditing.displayName(null);
//            self.spoolItemForEditing.displayName(null);

        } else {
            self.isExistingSpool(true);
            // Make a copy of provided spoolItem
            spoolItemCopy = ko.mapping.toJS(spoolItem);
            self.spoolItemForEditing.update(spoolItemCopy);
        }
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
                'margin-left': function () {
                    return -($(this).width() / 2);
                }
            });

    };

    this.copySpoolItem = function () {
        self.isExistingSpool(false);
        spoolItemCopy = ko.mapping.toJS(self.spoolItemForEditing);
        self.spoolItemForEditing.update(spoolItemCopy);
        self.spoolItemForEditing.isTemplate(false);
        self.spoolItemForEditing.isActive(true);
        self.spoolItemForEditing.databaseId(null);
        self.spoolItemForEditing.isSpoolVisible(true);
    }

    this.saveSpoolItem = function () {

        // Input validation
        var displayName = self.spoolItemForEditing.displayName();
        if (!displayName || displayName.trim().length === 0) {
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
        self.apiClient.callSaveSpool(self.spoolItemForEditing, function (allPrintJobsResponse) {
            self.spoolItemForEditing.isSpoolVisible(false);
            self.spoolDialog.modal('hide');
            self.closeDialogHandler(true);
        });
    }

    this.deleteSpoolItem = function () {
        var result = confirm("Do you really want to delete this spool?");
        if (result == true) {
            self.apiClient.callDeleteSpool(self.spoolItemForEditing.databaseId(), function (responseData) {
                self.spoolItemForEditing.isSpoolVisible(false);
                self.spoolDialog.modal('hide');
                self.closeDialogHandler(true);
            });
        }
    }

    this.selectSpoolItemForPrinting = function () {
        self.spoolItemForEditing.isSpoolVisible(false);
        self.spoolDialog.modal('hide');
        self.closeDialogHandler(true, "selectSpoolForPrinting", self.spoolItemForEditing);
    }

    this.generateQRCodeImageSourceAttribute = function () {
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
