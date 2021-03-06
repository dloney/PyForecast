//
// Script Name:     mapbox.js
// Script Author:   Kevin Foley, Civil Engineer, Reclamation
// Last Modified:   Apr 4, 2018
//
// Description:     'mapbox.js' is the javascript portion of a web map application used
//                  to select stations and datasets in the PyForecast application. This
//                  script uses the MapboxGL javascript API to map GeoJSON files located
//                  in the GIS folder

///////////////// DEFINE STARTUP VARIABLES /////////////////////////////////
// This section defines all the variables that are called when the webpage
// initially loads. These variables are available to the javascript as
// global variables (with the 'window' handle) throughout the session

// Set up an initial map with a basic basemap
var grayMap = L.tileLayer('http://{s}.tiles.wmflabs.org/bw-mapnik/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'});
var terrainMap =  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
	attribution: 'Tiles &copy; Esri'});
var streetMap =  L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
	maxZoom: 18,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'});

var map = L.map('map',
    {zoomControl: true,
    layers: [terrainMap]}).setView([ 43, -113], 6); // Set up a map centered on the U.S. at zoom level 4

// Store the basemaps in a dict
var baseMaps = {'Grayscale': grayMap,
                'Terrain': terrainMap, 
                'Streets': streetMap};

// Create map panes
map.createPane("HUCPane")
map.createPane("ClimDivPane")
map.createPane("PointsPane")


// Load the local JSON files
var HUC8 = new Object();
var CLIM_DIV = new Object();
var USGS = new Object();
var SNOTEL = new Object();
var SNOWCOURSE = new Object();
var USBR_POLY = new Object();
var USBR_POINTS = new Object();
var USBR_AGMET = new Object();
var NCDC = new Object();

loadJSON('../../Resources/GIS/WATERSHEDS/HUC8_WGS84.json', function(response) {
    // Parse data into object
    window.HUC8 = JSON.parse(response);
});
loadJSON('../../Resources/GIS/CLIMATE_DIVISION/CLIMATE_DIVISION_GEOJSON.json', function(response){
    // Parse data into object
    window.CLIM_DIV = JSON.parse(response);
});
loadJSON('../../Resources/GIS/USGS_SITES/STREAMGAGES.json', function(response) {
    // Parse data into object
    window.USGS = JSON.parse(response);
});
loadJSON('../../Resources/GIS/NRCS_SITES/SNOTEL.json', function(response) {
    // Parse data into object
    window.SNOTEL = JSON.parse(response);
});
loadJSON('../../Resources/GIS/NRCS_SITES/SNOWCOURSE.json', function(response) {
    // Parse data into object
    window.SNOWCOURSE = JSON.parse(response);
});
loadJSON('../../Resources/GIS/RECLAMATION_SITES/RESERVOIRS2.json', function(response) {
    // Parse data into object
    window.USBR_POINTS = JSON.parse(response);
});
loadJSON('../../Resources/GIS/RECLAMATION_SITES/AGRIMET.json', function(response) {
    // Parse data into object
    window.USBR_AGMET = JSON.parse(response);
});
loadJSON('../../Resources/GIS/NCDC_SITES/NCDC.json', function(response) {
    // Parse data into object
    window.NCDC = JSON.parse(response);
});



// Add the USGS Sites
var USGSLayer = L.geoJSON( window.USGS, {

    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
            pane: "PointsPane",
            fillColor: "#23ff27",
            color: "#000000",
            weight: 1,
            radius: 7,
            fillOpacity: 1
            })
        },
    }).addTo(map);

// Add the SNOTEL sites
var SNOTELLayer = L.geoJSON( window.SNOTEL, {
    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
            pane: "PointsPane",
            fillColor: "#4cffed",
            color: "#000000",
            radius: 7,
            weight: 1,
            fillOpacity: 1
            })
        }
    }).addTo(map);

// Add the SnowCourse Sites
var SNOWCOURSELayer = L.geoJSON( window.SNOWCOURSE, {
    
    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
            pane: "PointsPane",
            fillColor: "#00beff",
            color: "#000000",
            weight:1,
            radius: 7,
            fillOpacity: 1
            })
        }
    }).addTo(map);

// Add the USBR sites
var USBR_POINTS_RESLayer = L.geoJSON( window.USBR_POINTS, {

    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
            pane: "PointsPane",
            fillColor: "#2268ff",
            color: "#000000",
            radius: 7,
            weight:1,
            fillOpacity: 1
            })
        }
    }).addTo(map);

// Add the USBR AGRIMET sites
var USBR_POINTS_AGMETLayer = L.geoJSON( window.USBR_AGMET, {

    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
            pane: "PointsPane",
            fillColor: "#CB9F5B",
            color: "#000000",
            radius: 7,
            weight:1,
            fillOpacity: 1
            })
        }
    }).addTo(map);

// Add the NOAA NCDC sites
var NCDCLayer = L.geoJSON( window.NCDC, {

    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
            pane: "PointsPane",
            fillColor: "#FFCCFF",
            color: "#000000",
            radius: 7,
            weight:1,
            fillOpacity: 1
            })
        }
    });

// Add the popups for the USGS sites
USGSLayer.on("click",function(e) {
    var id = e.layer.feature.properties.site_no;
    var name = e.layer.feature.properties.station_nm;
    var huc = ("0" + e.layer.feature.properties.huc_cd).slice(-8);
    var elev = e.layer.feature.properties.alt_va;
    var por = e.layer.feature.properties.begin_date;
    var url = "https://waterdata.usgs.gov/nwis/inventory/?site_no="+id;
    var popHTML = "<strong>USGS Streamgage Site</strong>" + 
                  "<p>ID: " + id +
                  "</br>Name: " + name +
                  "</br>HUC8: " + huc + 
                  "</br>Elevation: " + elev + 
                  "</br>POR: " + por + 
                  '</br><a id="paramURL" href = ' + url + '>Website' +
                  '</a></p><button type="button" onclick="buttonPress()">Add Site</button>' + 
                  '<p hidden id="info" style="margin:0">USGS|'+id+'|'+name+'|Streamflow</p>';
    var pop = L.popup().setLatLng(e.latlng).setContent(popHTML).addTo(map)

});

// Add the popups for the SNOTEL sites
SNOTELLayer.on("click",function(e) {
    var id = e.layer.feature.properties.ID;
    var name = e.layer.feature.properties.Name;
    var huc = ("0" + e.layer.feature.properties.HUC).slice(-8);
    var elev = e.layer.feature.properties.Elevation_ft;
    var por = e.layer.feature.properties.POR_START;
    if (window.soilSites.indexOf(parseInt(id)) > -1) {
        option3 = '<option value="SOIL">Soil Moisture</option>'
    } else {
        option3 = "";
    };
    var url = "https://wcc.sc.egov.usda.gov/nwcc/site?sitenum="+id;
    var popHTML = "<strong>NRCS SNOTEL Site</strong>" + 
                  "<p>ID: " + id +
                  "</br>Name: " + name +
                  "</br>HUC8: " + huc + 
                  "</br>Elevation: " + elev + 
                  "</br>POR: " + por + 
                  '</br><a id="paramURL" href = ' + url + '>Website' +
                  '</a></p>' + 
                  '<select id="param"><option value="SWE">SWE (in)</option><option value="Precip">Precip (in)</option>' + option3 + '</select>' +
                  '<button type="button" onclick="buttonPress()">Add Site</button>' + 
                  '<p hidden id="info" style="margin:0">SNOTEL|'+id+'|'+name+'</p>';
    var pop = L.popup().setLatLng(e.latlng).setContent(popHTML).addTo(map);

});

// Add the popups for the SNOWCOURSE sites
SNOWCOURSELayer.on("click",function(e) {
    var id = e.layer.feature.properties.ID;
    var name = e.layer.feature.properties.Name;
    var huc = ("0" + e.layer.feature.properties.HUC).slice(-8);
    var elev = e.layer.feature.properties.Elevation_ft;
    var por = e.layer.feature.properties.POR_START;
    var popHTML = "<strong>NRCS Snow Course Site</strong>" + 
                  "<p>ID: " + id +
                  "</br>Name: " + name +
                  "</br>HUC8: " + huc + 
                  "</br>Elevation: " + elev + 
                  "</br>POR: " + por +  
                  '</p><button type="button" onclick="buttonPress()">Add Site</button>' + 
                  '<p hidden id="info" style="margin:0">SNOWCOURSE|'+id+'|'+name+'|SWE_SnowCourse</p>';
    var pop = L.popup().setLatLng(e.latlng).setContent(popHTML).addTo(map)

});

// Add the popups for the USBR sites
USBR_POINTS_RESLayer.on("click",function(e) {
    var id = e.layer.feature.properties.USBR_ID;
    var name = e.layer.feature.properties.NAME;
    var elev = e.layer.feature.properties.MeanElevation;
    var huc = e.layer.feature.properties.HUC_CODE;
    var region = e.layer.feature.properties.REGION;
    var pcode = e.layer.feature.properties.PCODE;
    var url = "https://www.usbr.gov/pn-bin/inventory.pl?ui=true&interval=daily&site="+id;
    if (region == "GP") {
        url = "https://www.usbr.gov/gp/hydromet/"+id+".html";
    }
    if (region == "UC") {
        url = "https://www.usbr.gov/uc/water/ff/RESERVOIR_DATA/"+id+"/dashboard.html#huc";
    }
    if (region == "LC") {
        url = "https://www.usbr.gov/uc/water/ff/RESERVOIR_DATA/"+id+"/dashboard.html#huc";
    }
    var popHTML = "<strong>USBR Reservoir Site</strong>" +
                  "<p>ID: " + id +
                  "</br>Name: " + name +
                  "</br>Elevation: " + Math.round(elev) +
                  "</br>HUC: " + huc +
                  "</br>Region: " + region +
                  '</br><a id="paramURL" href = ' + url + '>Website</a>' +
                  '</p><button type="button" onclick="buttonPress()">Add Site</button>' +
                  '<p hidden id="info" style="margin:0">USBR|'+id+'|'+name+'|Inflow|' + region + '|' + pcode + '</p>';
    var pop = L.popup().setLatLng(e.latlng).setContent(popHTML).addTo(map)

});

// Add the popups for the USBR AGRIMET sites
USBR_POINTS_AGMETLayer.on("click",function(e) {
    var id = e.layer.feature.properties.USBR_ID;
    var name = e.layer.feature.properties.NAME;
    var elev = e.layer.feature.properties.MeanElevation;
    var huc = e.layer.feature.properties.HUC_CODE;
    var region = e.layer.feature.properties.REGION;
    var pcode = e.layer.feature.properties.HASPRECIP;
    if (pcode == "TRUE") {
        option3 = '<option value="PP">Precipitation (in)</option>'
    } else {
        option3 = "";
    };
    var url = "https://www.usbr.gov/pn-bin/inventory.pl?ui=true&interval=daily&site="+id;
    var popHTML = "<strong>USBR Agrimet Site</strong>" +
                  "<p>ID: " + id +
                  "</br>Name: " + name +
                  "</br>Elevation: " + Math.round(elev) +
                  //"</br>HUC: " + huc +
                  //"</br>Region: " + region +
                  '</br><a id="paramURL" href = ' + url + '>Website</a>' +
                  '</p><select id="paramAgmet"><option value="MN">Minimum Temperatures (degF)</option><option value="MM">Average Temperatures (degF)</option><option value="MX">Maximum Temperatures (degF)</option>' + option3 + '</select>' +
                  '<button type="button" onclick="buttonPress()">Add Site</button>' +
                  '<p hidden id="info" style="margin:0">AGMET|'+id+'|'+name+'|Weather|' + region + '|' + pcode + '</p>';
    var pop = L.popup().setLatLng(e.latlng).setContent(popHTML).addTo(map)

});

// Add the popups for the NOAA NCDC sites
NCDCLayer.on("click",function(e) {
    var id = e.layer.feature.properties.ID;
    var name = e.layer.feature.properties.NAME;
    var elev = e.layer.feature.properties.ELEV;
    var state = e.layer.feature.properties.STATE;
    var dtypes = e.layer.feature.properties.DATATYPES.split(",");
    //alert(dtypes);
    var dtypeDropDown = ''
    if (dtypes.indexOf('PRCP') >= 0) {
        dtypeDropDown = dtypeDropDown + "<option value='PRCP'>PRCP - Precipitation</option>";
    }
    if (dtypes.indexOf('WESD') >= 0) {
        dtypeDropDown = dtypeDropDown + "<option value='WESD'>WESD - SWE</option>";
    }
    if (dtypes.indexOf('TMIN') >= 0) {
        dtypeDropDown = dtypeDropDown + "<option value='TMIN'>TMIN - Min Temps</option>";
    }
    if (dtypes.indexOf('TAVG') >= 0) {
        dtypeDropDown = dtypeDropDown + "<option value='TAVG'>TAVG - Avg Temps</option>";
    }
    if (dtypes.indexOf('TMAX') >= 0) {
        dtypeDropDown = dtypeDropDown + "<option value='TMAX'>TMAX - Max Temps</option>";
    }
    var url = "https://www.ncdc.noaa.gov/cdo-web/datasets/GHCND/stations/GHCND:"+id+"/detail";
    var popHTML = "<strong>NOAA NCDC Meteorologic Site</strong>" +
                  "<p>ID: " + id +
                  "</br>Name: " + name +
                  "</br>Elevation: " + Math.round(elev) +
                  "</br>State: " + state +
                  //"</br>Region: " + region +
                  '</br><a id="paramURL" href = ' + url + '>Click here</a> to figure out what data is available for this site before selecting from the drop-down box below' +
                  //'</p><select id="paramNcdc"><option value="TMIN">TMIN - Minimum Temperatures</option><option value="TAVG">TAVG - Average Temperatures</option><option value="TMAX">TMAX - Maximum Temperatures</option>' +
                  //'<option value="PRCP">PRCP - Precipitation</option><option value="WESD">WESD - SWE</option></select>' +
                  '</p><select id="paramNcdc">' + dtypeDropDown + '</select>' +
                  '<button type="button" onclick="buttonPress()">Add Site</button>' +
                  '<p hidden id="info" style="margin:0">NCDC|'+id+'|'+name+'|Weather|' + state + '</p>';
    var pop = L.popup().setLatLng(e.latlng).setContent(popHTML).addTo(map)

});

// Load the map with all the HUCs, streamgages, SNOTEL sites, SNOW Courses, and USBR sites
var HUCLayer = L.geoJSON( window.HUC8, {
    style: {pane: "HUCPane",
            fillColor: "#4286f4",
            weight: 1,
            opacity: .8, 
            color: "#4286f4", 
            fillOpacity: 0.0},
    onEachFeature: window.onHUCFeatures}).addTo(map);

var CLIM_DIV_Layer = L.geoJSON( window.CLIM_DIV, {
    style: {pane:"HUCPane",
            fillColor: "#f5bb3d",
            weight: 1,
            opacity: 0.8,
            color: "#f5bb3d",
            fillOpacity: 0},
    onEachFeature: window.onClimFeatures
});


// Add interactivity to the HUC boundaries
function onHUCFeatures( feature, layer ) {
    layer.on({
        mouseover: highlightHUC,
        mouseout: resetHighlightHUC,
        click: clickHUC
    });
};

function highlightHUC(e) {
    var layer = e.target;
    layer.setStyle({
        color:"#0000ff",
        weight:3
    });
};

function resetHighlightHUC(e) {
    window.HUCLayer.resetStyle(e.target);
};

function clickHUC(e) {
    var coordinates = getCenter(e.target.feature);
    var name = e.target.feature.properties.NAME;
    var num = e.target.feature.properties.HUC8;
    var popHTML = "<strong>Hydrologic Unit</strong>"+
                  "<p>Name: " + name +
                  "</br>HUC8: " + num +
                  "</p>Select dataset to add: </br>" +
                  '<select id="paramHUC"><option value="nrcc">NRCC Temperatures and Precipitation</option><option value="prism">PRISM Temperatures and Precipitation</option></select>' +
                  '<button type="button" onclick="buttonPress()">Add Site</button>' +
                  '<p hidden id="info" style="margin:0">HUC|'+num+'|'+name+'</p>';

    var pop = L.popup().setLatLng(coordinates).setContent(popHTML).addTo(map);
};

function onClimFeatures( feature, layer ) {
    layer.on({
        mouseover: highlightClim,
        mouseout: resetHighlightClim,
        click: clickClim
    });
};

function highlightClim(e) {
    var layer = e.target;
    layer.setStyle({
        color:"#f5be3d",
        weight:3
    });
};

function resetHighlightClim(e) {
    window.CLIM_DIV_Layer.resetStyle(e.target);
};

function clickClim(e) {
    var coordinates = getCenter(e.target.feature);
    var name = e.target.feature.properties.NAME;
    var num = e.target.feature.properties.STATE + ', ' + e.target.feature.properties.NAME;
    var popHTML = "<strong>Climate Division</strong>"+
                  "<p>Name: " + name +
                  "</br>Code: " + num +
                  "</p>Select dataset to add: </br>" +
                  '<select id="paramClim"><option value="pdsi">Palmer Drought Severity Index</option></select>' +
                  '<button type="button" onclick="buttonPress()">Add Site</button>' +
                  '<p hidden id="info" style="margin:0">CLIM|'+num+'|'+name+'</p>';

    var pop = L.popup().setLatLng(coordinates).setContent(popHTML).addTo(map);
};



var groupedOverlays = {
    "Stations":{
        "USGS Streamgages":USGSLayer,
        "NRCS SNOTEL Sites":SNOTELLayer,
        "NRCS Snow Course" :SNOWCOURSELayer,
        "USBR Natural Flow":USBR_POINTS_RESLayer,
        "USBR Agrimet":USBR_POINTS_AGMETLayer,
        "NOAA Sites":NCDCLayer
    },
    "Areas":{
        "Watersheds":window.HUCLayer,
        "Climate Divisions":window.CLIM_DIV_Layer,
    }
}

var options = {
    exclusiveGroups: ["Areas"],
    groupCheckboxes: false
}
// Add a basemap and layer selector
//L.control.layers(baseMaps, dataLayers).addTo(map);
//L.control.layers(polyLayers).addTo(map);

L.control.groupedLayers(baseMaps, groupedOverlays, options).addTo(map);

//window.HUCLayer.on("add", function(e){window.CLIM_DIV_Layer.remove()});
//window.HUCLayer.on("remove", function(e){window.CLIM_DIV_Layer.addTo(map);});
//window.CLIM_DIV_Layer.on("add", function(e){window.HUCLayer.remove()});
//window.CLIM_DIV_Layer.on("remove", function(e){window.HUCLayer.addTo(map);});

// Function to load local JSON file
function loadJSON(filename, callback) {   

    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open('GET', filename, false); // Replace 'my_data' with the path to your file
    xobj.onreadystatechange = function () {
          if (xobj.status == "0") {
            // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
            callback(xobj.responseText);
          }
    };
    xobj.send(null);  
};

// Function to send the site to the site list if the user selects it
function buttonPress() {
    var infoString = document.getElementById('info').innerHTML;
    var infoList = infoString.split('|');
    var type = infoList[0];
    if (type == 'SNOTEL') {
        var num = infoList[1];
        var name = infoList[2];
        var param = document.getElementById('param').value;
        var url = document.getElementById('paramURL').href;
        console.log('StationSelect|'+name+'|'+num+'|'+type+'|'+param+'|'+url);
    } else if (type == 'USBR') {
        var num = infoList[1];
        var name = infoList[2];
        var param = infoList[3];
        var region = infoList[4];
        var pcode = infoList[5];
        var url = document.getElementById('paramURL').href;
        console.log('StationSelect|'+name+'|'+num+'|'+type+'|'+param+'|'+region+'|'+pcode+'|'+url);
    } else if (type == 'AGMET') {
        var num = infoList[1];
        var name = infoList[2];
        //var type = infoList[3];
        var region = infoList[4];
        var pcode = infoList[5];
        var param = document.getElementById('paramAgmet').value;
        var url = document.getElementById('paramURL').href;
        console.log('StationSelect|'+name+'|'+num+'|'+type+'|Weather|'+region+'|'+param+'|'+url);
    } else if (type == 'NCDC') {
        var num = infoList[1];
        var name = infoList[2];
        //var type = infoList[3];
        var region = infoList[4];
        var pcode = infoList[5];
        var param = document.getElementById('paramNcdc').value;
        var url = document.getElementById('paramURL').href;
        console.log('StationSelect|'+name+'|'+num+'|'+type+'|Weather|'+region+'|'+param+'|'+url);
    } else if (type == 'CLIM') {
        var num = infoList[1];
        var name = infoList[2];
        var param = document.getElementById('paramClim').value;
        console.log(param+'|'+num+'|'+name);
    } else if (type == 'HUC') {
        var num = infoList[1];
        var name = infoList[2];
        var param = document.getElementById('paramHUC').value;
        console.log(param+'|'+num+'|'+name);
    } else if (type == 'USGS') {
        var num = infoList[1];
        var name = infoList[2];
        var param = infoList[3];
        var url = document.getElementById('paramURL').href;
        console.log('StationSelect|'+name+'|'+num+'|'+type+'|'+param+'|'+url);
    } else {
        var num = infoList[1];
        var name = infoList[2];
        var param = infoList[3];
        //var url = document.getElementById('paramURL').href;
        console.log('StationSelect|'+name+'|'+num+'|'+type+'|'+param+'|'+url);
    };
    
};

// Function to find center of polygon
function getCenter(feat) {
    lats = 0;
    longs = 0;
    for (i = 0; i < feat.geometry.coordinates[0].length; i++) {
        lats += feat.geometry.coordinates[0][i][1];
        longs += feat.geometry.coordinates[0][i][0];
    };
    meanLat = lats / feat.geometry.coordinates[0].length;
    meanLong = longs / feat.geometry.coordinates[0].length;
    coords = [meanLat, meanLong];
    return coords;
};