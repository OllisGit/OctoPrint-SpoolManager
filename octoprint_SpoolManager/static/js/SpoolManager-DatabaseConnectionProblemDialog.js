
function DatabaseConnectionProblemDialog(){

    var self = this;

    self.apiClient = null;

    self.problemDialog = null;
    self.closeDialogHandler = null;

    self.dialogTitle = ko.observable();
    self.dialogMessage = ko.observable();

    self.isVisible = false;

    /////////////////////////////////////////////////////////////////////////////////////////////////// INIT

    self.init = function(apiClient){
        self.apiClient = apiClient;

        self.problemDialog = $("#dialog_spoolManager_databaseConnectionProblem");
    }

    self.isInitialized = function() {
        return self.apiClient != null;
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////// SHOW DIALOG
    self.showDialog = function(problemResponseData, closeDialogHandler){
        if (this.isVisible == true){
            return; // already visible
        }
        self.closeDialogHandler = closeDialogHandler;
        // Bind problem message
        var title = problemResponseData.title;
        var message = problemResponseData.message;
        var problemMessage = title + "<br/>" + message;

        self.dialogTitle(title);
        self.dialogMessage(message);

        self.problemDialog.modal({
            //minHeight: function() { return Math.max($.fn.modal.defaults.maxHeight() - 80, 250); }
            keyboard: false,
            clickClose: false,
            showClose: false,
            backdrop: "static"
        }).css({
            width: 'auto',
            'margin-left': function() { return -($(this).width() /2); }
        });
        self.isVisible = true;
    }


    /////////////////////////////////////////////////////////////////////////////////////////////////// CLOSE
    self.closeDialog  = function(){
        self.apiClient.confirmDatabaseProblemMessage(function(response){
            // nothing special to do
        });
        self.problemDialog.modal('hide');
        self.isVisible = false;
        self.closeDialogHandler();
    }
}
