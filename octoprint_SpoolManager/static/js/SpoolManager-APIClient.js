

function SpoolManagerAPIClient(pluginId, baseUrl) {

    this.pluginId = pluginId;
    this.baseUrl = baseUrl;


    // see https://gomakethings.com/how-to-build-a-query-string-from-an-object-with-vanilla-js/
    var _buildRequestQuery = function (data) {
        // If the data is already a string, return it as-is
        if (typeof (data) === 'string') return data;

        // Create a query array to hold the key/value pairs
        var query = [];

        // Loop through the data object
        for (var key in data) {
            if (data.hasOwnProperty(key)) {

                // Encode each key and value, concatenate them into a string, and push them to the array
                query.push(encodeURIComponent(key) + '=' + encodeURIComponent(data[key]));
            }
        }
        // Join each item in the array with a `&` and return the resulting string
        return query.join('&');

    };

    var _addApiKeyIfNecessary = function(urlContext){
        if (UI_API_KEY){
            urlContext = urlContext + "?apikey=" + UI_API_KEY;
        }
        return urlContext;
    }

    this.getExportUrl = function(exportType){
        return _addApiKeyIfNecessary("./plugin/" + this.pluginId + "/exportSpools/" + exportType);
    }

    this.getSampleCSVUrl = function(){
        return _addApiKeyIfNecessary("./plugin/" + this.pluginId + "/sampleCSV");
    }

    //////////////////////////////////////////////////////////////////////////////// LOAD AdditionalSettingsValues
    this.callAdditionalSettings = function (responseHandler){
        var urlToCall = this.baseUrl + "api/plugin/"+this.pluginId+"?action=additionalSettingsValues";
        $.ajax({
            url: urlToCall,
            type: "GET"
        }).always(function( data ){
            responseHandler(data)
        });
    }
    //////////////////////////////////////////////////////////////////////////////// LOAD DatabaseMetaData
    this.loadDatabaseMetaData = function (responseHandler){
        var urlToCall = this.baseUrl + "plugin/"+this.pluginId+"/loadDatabaseMetaData";
        $.ajax({
            url: urlToCall,
            type: "GET"
        }).always(function( data ){
            responseHandler(data)
        });
    }
    //////////////////////////////////////////////////////////////////////////////// TEST DatabaseConnection
    this.testDatabaseConnection = function (databaseSettings, responseHandler){
        jsonPayload = ko.toJSON(databaseSettings)

        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: this.baseUrl + "plugin/" + this.pluginId + "/testDatabaseConnection",
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            data: jsonPayload,
            type: "PUT"
        }).always(function( data ){
            responseHandler(data);
        });
    }

    //////////////////////////////////////////////////////////////////////////////// CONFIRM DatabaseConnectionPoblem
    this.confirmDatabaseProblemMessage = function (responseHandler){
        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: this.baseUrl + "plugin/" + this.pluginId + "/confirmDatabaseProblemMessage",
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            type: "PUT"
        }).always(function( data ){
            responseHandler(data);
        });
    }


    //////////////////////////////////////////////////////////////////////////////// LOAD FILTERED/SORTED PrintJob-Items
    this.callLoadSpoolsByQuery = function (tableQuery, responseHandler){
        query = _buildRequestQuery(tableQuery);
        urlToCall = this.baseUrl + "plugin/"+this.pluginId+"/loadSpoolsByQuery?"+query;
        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: urlToCall,
            type: "GET"
        }).always(function( data ){
            responseHandler(data)
            //shoud be done by the server to make sure the server is informed countdownDialog.modal('hide');
            //countdownDialog.modal('hide');
            //countdownCircle = null;
        });
    }


    //////////////////////////////////////////////////////////////////////////////////////////////////// SAVE Spool-Item
    this.callSaveSpool = function (spoolItem, responseHandler){
        jsonPayload = ko.toJSON(spoolItem)

        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: this.baseUrl + "plugin/" + this.pluginId + "/saveSpool",
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            data: jsonPayload,
            type: "PUT"
        }).always(function( data ){
            responseHandler();
        });
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////// DELETE Spool-Item
    this.callDeleteSpool = function (databaseId, responseHandler){
        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: this.baseUrl + "plugin/" + this.pluginId + "/deleteSpool/" + databaseId,
            type: "DELETE"
        }).always(function( data ){
            responseHandler();
        });
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////// SELECT Spool-Item
    this.callSelectSpool = function (databaseId, responseHandler){
        if (databaseId == null){
            databaseId = -1;
        }
        var jsonPayload = '{"databaseId":'+databaseId+'}';
        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: this.baseUrl + "plugin/" + this.pluginId + "/selectSpool",
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            data: jsonPayload,
            type: "PUT"
        }).always(function( data ){
            responseHandler( data );
        });
    }

    //////////////////////////////////////////////////////////////////////////////////////// ALLOWED TO PRINT Spool-Item
    this.allowedToPrint = function (responseHandler){

        $.ajax({
            url: this.baseUrl + "plugin/" + this.pluginId + "/allowedToPrint",
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            type: "GET"
        }).always(function( data ){
            responseHandler(data);
        });
    }

    //////////////////////////////////////////////////////////////////////////////////////////////////// DELETE Database
    this.callDeleteDatabase = function(databaseType, databaseSettings, responseHandler){
        jsonPayload = ko.toJSON(databaseSettings)
        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: this.baseUrl + "plugin/"+this.pluginId+"/deleteDatabase/"+databaseType,
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            data: jsonPayload,
            type: "POST"
        }).always(function( data ){
            responseHandler(data)
            //shoud be done by the server to make sure the server is informed countdownDialog.modal('hide');
            //countdownDialog.modal('hide');
            //countdownCircle = null;
        });
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////// DOWNLOAD Database
    this.getDownloadDatabaseUrl = function(exportType){
        return _addApiKeyIfNecessary("./plugin/" + this.pluginId + "/downloadDatabase");
    }

//    // deactivate the Plugin/Check
//    this.callDeactivatePluginCheck =  function (){
//        $.ajax({
//            url: this.baseUrl + "plugin/"+ this.pluginId +"/deactivatePluginCheck",
//            type: "PUT"
//        }).done(function( data ){
//            //responseHandler(data)
//        });
//    }





}
