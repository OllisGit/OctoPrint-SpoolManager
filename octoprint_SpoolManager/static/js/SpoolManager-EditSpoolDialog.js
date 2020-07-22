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

    self.componentFactory = new ComponentFactory();
    self.spoolDialog = null;
    self.closeDialogHandler = null;
    self.spoolItemForEditing = null;
    self.templateSpool = null;
    self.noteEditor = null;

    // Do I need these viewModels?
    self.firstUseDatePickerModel = null;
    self.lastUseDatePickerModel = null;
    self.purchasedOndatePickerModel = null;
    self.labelsViewModel = null;
    self.filamentColorViewModel = null;
    self.materialViewModel = null;

    self.catalogs = null;

    ///////////////////////////////////////////////////////////////////////////////////////////////////////// ITEM MODEL
    var DEFAULT_COLOR = "#ff0000";

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

        // - list all attributes
        this.isEmpty = ko.observable();
        this.databaseId = ko.observable();
        this.isTemplate = ko.observable();
        this.displayName = ko.observable();
//        this.vendor = ko.observable();
//        this.material = ko.observable();
        this.density = ko.observable();
        this.diameter = ko.observable();
        this.temperature = ko.observable();
        this.color = ko.observable();
        this.totalWeight = ko.observable();
        this.remainingWeight = ko.observable();
        this.usedLength = ko.observable();
        this.usedWeight = ko.observable();
        this.usedPercentage = ko.observable();  // TODO needed?
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
        // Fill Item with data
        this.update(spoolData);
    }

    SpoolItem.prototype.update = function (data) {
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

        this.isEmpty(data == null);
        this.databaseId(updateData.databaseId);
        this.isTemplate(updateData.isTemplate);
        this.displayName(updateData.displayName);
        this.vendor(updateData.vendor);

        this.material(updateData.material);
        this.density(updateData.density);
        this.diameter(updateData.diameter);
        this.color(updateData.color == null ? DEFAULT_COLOR : updateData.color);
        this.temperature(updateData.temperature);
        this.totalWeight(updateData.totalWeight);
        this.remainingWeight(updateData.remainingWeight);
        this.code(updateData.code);
        this.usedPercentage(updateData.usedPercentage);
        this.usedLength(updateData.usedLength);
        this.usedWeight(updateData.usedWeight);

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
                    deltaFormat = JSON.parse(updateData.noteDeltaFormat);
                    self.noteEditor.setContents(deltaFormat, 'api');
            }
        }
    };

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
    this.initBinding = function(apiClient, pluginSettings){

        self.apiClient = apiClient;
        self.pluginSettings = pluginSettings;

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

        // initial coloring
        self._createSpoolItemForEditing();
        self._reColorFilamentIcon(self.spoolItemForEditing.color());
        self.spoolItemForEditing.color.subscribe(function(newColor){
            self._reColorFilamentIcon(newColor);
        });

        // update used percentage
        self.updateUsedPercentage = function(){
            var total = self.spoolItemForEditing.totalWeight();
            var remainingWeight = self.spoolItemForEditing.remainingWeight();
            if (total != null && remainingWeight != null){
                if (isNaN(total)==false && isNaN(remainingWeight)==false){
                    result = remainingWeight/(total/100);
                    self.spoolItemForEditing.usedPercentage(result);
                }
            }
        }
        self.spoolItemForEditing.remainingWeight.subscribe(function(newValue){
            self.updateUsedPercentage();
        });

        // update RemainingWeight
        self.updateRemainingWeight = function(){
            var total = self.spoolItemForEditing.totalWeight();
            var used = self.spoolItemForEditing.usedWeight();
            if (total != null && used != null){
                if (isNaN(total)==false && isNaN(used)==false && 0 != total.length && 0 != used.length){
                    remainingWeight = total - used;
                    self.spoolItemForEditing.remainingWeight(remainingWeight);
                } else {
                    self.spoolItemForEditing.remainingWeight("");
                }
            } else {
                self.spoolItemForEditing.remainingWeight("");
            }
        }

        self.spoolItemForEditing.totalWeight.subscribe(function(newValue){
            self.updateRemainingWeight();
        });
        self.spoolItemForEditing.usedWeight.subscribe(function(newValue){
            self.updateRemainingWeight();
        });
    }

    this.afterBinding = function(){
    }

    this._createSpoolItemForEditing = function(){
        self.spoolItemForEditing = new SpoolItem(null, true);
        return self.spoolItemForEditing;
    }

    this._createSpoolItemForTemplate = function(spoolData){
        self.templateSpool =  new SpoolItem(spoolData, false);
    }


    this.createSpoolItemForTable = function(spoolData){
        newSpoolItem = new SpoolItem(spoolData, false);
        return newSpoolItem;
    }


    this.updateCatalogs = function(catalogs){
        self.catalogs = catalogs;
    }

    this.updateTemplateSpool = function(templateSpoolData){
        if (self.templateSpool == null){
            self._createSpoolItemForTemplate(templateSpoolData)
        } else {
            self.templateSpool.update(templateSpoolData);
        }
    }

    this.showDialog = function(spoolItem, closeDialogHandler){
        self.closeDialogHandler = closeDialogHandler;

        // initial coloring
        self._reColorFilamentIcon(self.spoolItemForEditing.color());

        if (spoolItem == null){
            // New Spool
            self.isExistingSpool(false);
            templateSpoolItemCopy = ko.mapping.toJS(self.templateSpool);
            self.spoolItemForEditing.update(templateSpoolItemCopy);
            self.spoolItemForEditing.isTemplate(false);
            self.spoolItemForEditing.databaseId(null);
            self.spoolItemForEditing.costUnit(self.pluginSettings.currencySymbol());
        }else{
            self.isExistingSpool(true);
            // Make a copy of provided spoolItem
            spoolItemCopy = ko.mapping.toJS(spoolItem);
            self.spoolItemForEditing.update(spoolItemCopy);
        }
        self.spoolDialog.modal({
            //minHeight: function() { return Math.max($.fn.modal.defaults.maxHeight() - 80, 250); }
            keyboard: false,
            clickClose: true,
            showClose: false,
            backdrop: "static"
        }).css({
            width: 'auto',
            'margin-left': function() { return -($(this).width() /2); }
        });

    };


    this.copySpoolItem = function(){
        self.isExistingSpool(false);
        spoolItemCopy = ko.mapping.toJS(self.spoolItemForEditing);
        self.spoolItemForEditing.update(spoolItemCopy);
        self.spoolItemForEditing.isTemplate(false);
        self.spoolItemForEditing.databaseId(null);
    }


    this.saveSpoolItem = function(){

        // Input validation
        var displayName = self.spoolItemForEditing.displayName();
        if (!displayName || displayName.trim().length === 0){
            alert("Displayname not entered!");
            return;
        }


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
            self.spoolDialog.modal('hide');
            self.closeDialogHandler(true);
        });
    }

    this.deleteSpoolItem = function(){
        var result = confirm("Do you really want to delete this spool?");
        if (result == true){
            self.apiClient.callDeleteSpool(self.spoolItemForEditing.databaseId(), function(responseData) {
                self.spoolDialog.modal('hide');
                self.closeDialogHandler(true);
            });
        }
    }
}
