
function ComponentFactory(pluginId) {

    this.pluginId = pluginId
    this.COMPONENT_PREFIX = "component_";

/*
    <component_printstatusselection-bla></component_printstatusselection-bla>

            blaViewModel = self.componentFactory.createHelloWorldComponent("bla");
            blaViewModel.hello("SUPER!!!!");

*/
    this.createHelloWorldComponent = function(name){

        componentName = this.COMPONENT_PREFIX + "printstatusselection-" + name;

        var componentViewModel = {
            hello: ko.observable("World")
        }

        componentTemplate = "<b>Hello <span data-bind='text: hello'></span></b>";

        ko.components.register(componentName, {
            viewModel: { instance: componentViewModel },
            template: componentTemplate
        });
        return componentViewModel;
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////// DATETIME - PICKER
    /*
    <div class="input-append datetime">
        <input id="DueDate" type="text" value="13.11.2017 13:24" class="input-large; text-right"><span class="add-on" id="DueDate-Icon"><i class="icon-th"></i></span>
    </div>
    */
    this.createDateTimePicker = function(elementId, showTimePicker){

        if (showTimePicker == null){
            showTimePicker = true;
            dateTimeFormat = 'd.m.Y H:i';
        }
        if (showTimePicker == false){
            dateTimeFormat = 'd.m.Y';
        }

        var componentViewModel = {
            currentDateTime: ko.observable(),
            isEnabled: ko.observable(true)
        }

        var elementSelector = "#" + elementId ;
        // Build defualt widget
        var datePicker = $(elementSelector).datetimepicker({
            format:dateTimeFormat,
            closeOnDateSelect:true,
            closeOnTimeSelect:false,
            timepicker:showTimePicker,
            weeks:true
        });

        $($(elementSelector).parent().find('span[class=add-on]')[0]).on('click', function () {
            if (componentViewModel.isEnabled() == true){
                $(elementSelector).datetimepicker('show');
            }
        });


        // sync: jquery -> observable

        return componentViewModel;
    }


    ////////////////////////////////////////////////////////////////////////////////////////////////////// DATE - PICKER
    /* DEPRECATED use createDateTimePicker */
    this.createDatePicker = function(elementId){

       var componentViewModel = {
            currentDate: ko.observable(new Date())
        }

        var elementSelector = "#" + elementId ;
        // Build defualt widget
        var datePicker = $(elementSelector).datepicker({
            // TODO set datepicker options like dateformat
            autoHide: true,
            language: 'de-DE',
            format: "dd.mm.yyyy"
        });

        // sync: jquery -> observable
        datePicker.on('pick.datepicker', function (event) {
            newDate = event.date;
            if (componentViewModel.currentDate() == null || newDate.getTime() != componentViewModel.currentDate().getTime() ){
                componentViewModel.currentDate(newDate);
            }
            // new future date
            //  if (e.date < new Date()) {
            //    e.preventDefault(); // Prevent to pick the date
            //  }
        });

        // sync: observable -> jquery
        componentViewModel.currentDate.subscribe(function(newDate){
            currentDate = datePicker.datepicker('getDate');
            if (newDate == null){
                datePicker.datepicker('reset');
            } else {
                newDateTime = newDate.getTime();
                if (componentViewModel.currentDate() == null || newDateTime != currentDate.getTime()){
                    if (newDate != null){
                        datePicker.datepicker('setDate', newDate);
                    } else {
                        datePicker.datepicker('reset');
                    }
                }
            }
        });

        return componentViewModel;
    }


    ///////////////////////////////////////////////////////////////////////////////////////////////////////////// LABELS
    this.createLabels = function(elementId, dropDownParent){

        var elementSelector = "#" + elementId ;
        // Build Widget
        var labels = $(elementSelector).select2({
          dropdownParent: dropDownParent,
          multiple: true,
          placeholder: "Add a Label...",
//          allowClear: true,
          width: '400px',
          tags: true,
          dropdownAutoWidth: true
//          maximumSelectionLength: 2
        });


        // Widget Model
        var componentViewModel = {
            allOptions: ko.observableArray(),
            selectedOptions: ko.observableArray(),
//            labelsWidget: labels
        }

        // sync: observable -> jquery
        var fired = [false];
        componentViewModel.selectedOptions.subscribe(function(newSelections){
            if (fired[0] == false){
                fired[0] = true;
                labels.val(newSelections);
                labels.trigger('change');
            } else {
                fired[0] = false;
            }
        });


        return componentViewModel;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////// SELECT WITH FILTER
    this.createSelectWithFilter = function(elementId, dropDownParent){

        var elementSelector = "#" + elementId;
        // Build Widget
        var select2 = $(elementSelector).select2({
          dropdownParent: dropDownParent,
          placeholder: "Choose...",
          tags: true
        });

        // Widget Model
        var componentViewModel = {
            allOptions: ko.observableArray(),
            selectedOption: ko.observable(),
            select2Element: select2
        }

        // sync: observable -> jquery
        componentViewModel.selectedOption.subscribe(function(newSelection){
            select2.val(newSelection);
            select2.trigger('change');
        });
        return componentViewModel;
    }

    ///////////////////////////////////////////////////////////////////////////////////////////////////// COLOR - PICKER
    this.createColorPicker = function(elementId){

        // Widget Model
        var componentViewModel = {
            selectedColor: ko.observable(),
        }

        var elementSelector = "#" + elementId;
        var pickColor = $(elementSelector).pickAColor({
            showSpectrum          : false,
            showSavedColors       : false,
            saveColorsPerElement  : false,
            fadeMenuToggle        : true,
            showAdvanced          : true,
            showBasicColors       : true,
            showHexInput          : true,
            allowBlank            : false,
            basicColors           : {
                  white     : 'ffffff',
                  black     : '000000',
                  red       : 'ff0000',
                  green     : '008000',
                  blue      : '0000ff',
                  yellow    : 'ffff00',
                  orange    : 'ffa500',
                  purple    : '800080',
                  gray      : '808080',
                  darkgray  : 'A9A9A9',
                  lightgray : 'D3D3D3',
                  violet    : 'EE82EE',
                  pink      : 'FFC0CB',
                  brown     : 'A52A2A',
                  burlyWood : 'DEB887'
                }
        });

        // sync: jquery -> observable
        pickColor.on("change", function () {
            var newColor = ""+$(this).val();
            if (newColor.startsWith("#") == false){
                newColor = "#" + $(this).val();
            }
            componentViewModel.selectedColor(newColor);
        });

        // sync: observable -> jquery SELCETED_OPTIONS
        componentViewModel.selectedColor.subscribe(function(newColor){
            // check if new color already selected
            currentColor = "#" + pickColor.val();
            if (currentColor != newColor){
                newColorCode = newColor.substr(1);
                pickColor.setColor(newColorCode);
            }

        });


        return componentViewModel;
    };


    //////////////////////////////////////////////////////////////////////////////////////////////////////// NOTE EDITOR
    this.createNoteEditor = function(elementId){

        // Widget Model
//        var componentViewModel = {
//            noteText: ko.observable(),
//            noteDeltaFormat: ko.observable(),
//            noteHtml: ko.observable(),
//        }

        var elementSelector = "#" + elementId;
        var noteEditor = new Quill(elementSelector, {
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

        var NoteEditorController = function(providedNoteEditor){
            var noteEditor = providedNoteEditor;

            this.getText = function(){
                return noteEditor.getText();
            };

            this.getHtml = function(){
                return noteEditor.getHtml();
            };

            this.getDeltaFormat = function(){
                return noteEditor.getContents();
            };

            this.setDeltaFormat = function(newDeltaFormat){
                noteEditor.setContents(newDeltaFormat, 'api');
            };
        };
        return new NoteEditorController(noteEditor);

//        // write to editor
//        deltaFormat = JSON.parse(printJobItemForEdit.noteDeltaFormat());
//        self.noteEditor.setContents(deltaFormat, 'api');
//
//        // write to item
//        var noteText = self.noteEditor.getText();
//        var noteDeltaFormat = self.noteEditor.getContents();
//        var noteHtml = self.noteEditor.getHtml();
//        self.printJobItemForEdit.noteText(noteText);
//        self.printJobItemForEdit.noteDeltaFormat(noteDeltaFormat);
//        self.printJobItemForEdit.noteHtml(noteHtml);

//        // sync: jquery -> observable
//        noteEditor.on('text-change', function(delta, oldDelta, source) {
////            debugger
//            newDeltaAsString = JSON.stringify(delta);
//            currentDeltaAsString = JSON.stringify(componentViewModel.noteDeltaFormat());
//            if (newDeltaAsString != currentDeltaAsString){
//                componentViewModel.noteText(noteEditor.getText());
//                componentViewModel.noteDeltaFormat(delta);
//                componentViewModel.noteHtml(noteEditor.getHtml());
//            }
//        });
//
//        // sync: observable -> jquery SELCETED_OPTIONS
//        componentViewModel.noteDeltaFormat.subscribe(function(newDelta){
////            debugger
//            // check if new text already assigned
//            newDeltaAsString = JSON.stringify(newDelta);
//            currentDeltaAsString = JSON.stringify(noteEditor.getContents());
//            if (newDeltaAsString != currentDeltaAsString){
//                noteEditor.setContents(newDelta, 'api');
//            }
//        });
//
//
//        return componentViewModel;
    };

}
