
function SpoolManagerImportDialog(){

    var self = this;

    this.apiClient = null;

    this.importSpoolItemDialog = null;
    this.closeDialogHandler = null;

    this.importInProgress = ko.observable(false);
    this.importStatus = ko.observable();
    this.currentLineNumber = ko.observable();
    this.backupFilePath = ko.observable();
    this.backupSnapshotFilePath = ko.observable();
    this.successMessages = ko.observable();
    this.errorMessages = ko.observable();
    this.shouldTableReload = false;
    /////////////////////////////////////////////////////////////////////////////////////////////////// INIT

    this.init = function(apiClient){
        self.apiClient = apiClient;

        self.importSpoolItemDialog = $("#dialog_spoolManager_csvImportStatus");

    }

    this.isInitialized = function() {
        return self.apiClient != null;
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////// SHOW DIALOG
    this.showDialog = function(closeDialogHandler){

        self.closeDialogHandler = closeDialogHandler;

        // reset message
        self.importInProgress(false);
        self.importStatus("");
        self.currentLineNumber("");
        self.backupFilePath("");
        self.backupSnapshotFilePath("");
        self.successMessages("");
        self.errorMessages("");
        self.shouldTableReload = false;

        self.importSpoolItemDialog.modal({
            //minHeight: function() { return Math.max($.fn.modal.defaults.maxHeight() - 80, 250); }
            keyboard: false,
            clickClose: false,
            showClose: false,
            backdrop: "static"
        }).css({
            width: 'auto',
            'margin-left': function() { return -($(this).width() /2); }
        });
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////// UPDATE TEXT
    this.updateText = function(importData){

                if (importData.importStatus) {
                    self.importStatus(importData.importStatus);
                    switch (importData.importStatus){
                        case "running":
                            self.currentLineNumber(importData.currenLineNumber);
                            self.successMessages(importData.successMessages);
                            errorMessage = importData.errorCollection.join(" <br> ")
                            self.errorMessages(errorMessage);
                            self.importInProgress(true);
                            break;
                        case "finished":
                            // Final message statistic
                            self.importInProgress(false);
                            self.backupFilePath(importData.backupFilePath);
                            self.backupSnapshotFilePath(importData.backupSnapshotFilePath);
                            self.successMessages(importData.successMessages);
                            errorMessage = importData.errorCollection.join(" <br> ")
                            self.errorMessages(errorMessage);

                            self.shouldTableReload = true;

                            // enable close button in dialog
//                            self.csvImportStatusDialog.modal('hide');
//                            self.csvImportInProgress(false);
                            break;
                        default:
                    }
                }
                return;
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////// CLOSE
    this.closeDialog  = function(){
        self.importSpoolItemDialog.modal('hide');

        self.closeDialogHandler(self.shouldTableReload);
    }
}
