var map; 
var markers; //array of leaflet markers
var selected_marker; //global to hold index of selected marker
var segments; //array of leaflet line segments
var locked_status; //boolean array  - same length as markers
var marker_icons = {}; // to hold the marker icons
var polyline; //the line that shows the route


function initialize(){
    map = L.map('map').setView(L.latLng( 43.647103, -72.318701), 13);
    
    
    
    
    
    /*
    L.tileLayer('https://eric.talbot.cartodb.com/api/v1/map/073bdf02969a55b0ef0c3430c2aec8b6/{z}/{x}/{y}.png', {
        attribution: 'open street map',
        maxZoom: 18
    }).addTo(map); 
    
    
    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'open street map',
        maxZoom: 18
    }).addTo(map);*/ 
    
    
    cartodb.createLayer(map, 'https://ericstalbot.cartodb.com/api/v2/viz/a4aac29e-f4f0-11e5-854c-0e787de82d45/viz.json', {legends: false})
        .addTo(map)
        .on('done', function(layer) {
          //do stuff
        })
        .on('error', function(err) {
          alert("some error occurred: " + err);
        });
    
    
  
    map.on('click', onMapClick)
    
    document.addEventListener('keydown',onKeyDown, false);
    markers = [];
    segments = [];
    locked_status = [];

    marker_icons[true] = L.icon({iconUrl:'/static/locked.png', iconSize: [20,20]});
    marker_icons[false] = L.icon({iconUrl:'/static/notlocked.png', iconSize: [20,20]});
    
    polyline = L.polyline([], {color: '#00FF00', weight: 10, opacity: 0.9, clickable: false});
    polyline.addTo(map);

}


function onKeyDown(e){
    
    var mapping = {66: onBackSpace,
                   46: onDelete,
                   13: onEnter}
               
    
    for (keyCode in mapping){
        if (keyCode == e.keyCode){
            mapping[keyCode]();
        }
    
    }
    
}
    
    


function onDelete(){

    if (markerIsSelected()){
        deleteMarker(selected_marker);
        
    }

}

    
function onBackSpace(){    
    if (markers.length > 0){
        deleteMarker(markers[markers.length - 1]);
    }
}






function deleteMarker(m){

    
    
    var i = markers.indexOf(m);
    markers.splice(i, 1);
    locked_status.splice(i, 1);
    
    
    map.removeLayer(m);
    
    updateCrowLine();

    unselectMarker(m);


}

function markerIsSelected(){
    return(selected_marker !== undefined);
}

function unselectMarker(m){
    if (selected_marker == m){
        selected_marker = undefined;
        m.setOpacity(0.5)
    }   
}

function selectMarker(m){
    if (markerIsSelected()){
        unselectMarker(selected_marker);
    }
    selected_marker = m;
    selected_marker.setOpacity(0.9)

}

function onMapClick(e){

    addMarker(e.latlng);

}


function insert(arr, elem, i){
    arr.splice(i, 0, elem);
}


function addMarker(latlng, i){

    var m = L.marker(latlng,
             {draggable: true, icon: marker_icons[false]}).addTo(map);
             

    if (i == null){
        markers.push(m);
        locked_status.push(false);
    }
    else {
        insert(markers, m, i);
        insert(locked_status, false, i);
    }
    
    m.addEventListener('click', onMarkerClick)
    m.addEventListener('drag', updateCrowLine)
    //m.addEventListener('dragstart', onMarkerClick)

    updateCrowLine();
    

    selectMarker(m);
    

    
}



function onMarkerClick(e){
    
    
    if (markerIsSelected()){
        unselectMarker(selected_marker);
        
    }
    selectMarker(e.target);

    if (e.originalEvent.shiftKey){
    
        toggleLock(e.target);
    
    }
    

    
    
}


function toggleLock(m){

    var i = markers.indexOf(m);
    
    locked_status[i] = !locked_status[i];
    
    m.setIcon(marker_icons[locked_status[i]]);



}


function updateCrowLine(){

    

    for (i in segments){
        map.removeLayer(segments[i]);
    }
    
    segments = [];

    if (markers.length < 2){
        return(null);
    }
    
    
    for (var i = 0; i < (markers.length - 1); i++){

        var segment = L.polyline([markers[i].getLatLng(),
                                  markers[i+1].getLatLng()], {color: 'grey', opacity: 0.5,
                                                              dashArray: "5, 10"})
                                  
        segment.addTo(map);
        
        segment.addEventListener("click", onSegmentClick);
        
        segments.push(segment);
                                  
    
    }
    
      

}

function onSegmentClick(e){

    var i = segments.indexOf(e.target);
    

    addMarker(e.latlng, i + 1);


}



function updateShape(response, status){
    
    var latlngs = [];
        
    for (i = 0; i < response.coords.length; i++){
        
        latlngs.push(new L.latLng(response.coords[i][1],
                              response.coords[i][0]));
        
    
    }
    polyline.setLatLngs(latlngs);
    polyline.bringToFront();
}


function onEnter(){
    getShape()

}



function getShape(){
    // it all starts here
    
    polyline.setLatLngs([]);

    var xy;
    xy = [];
    
    for (i = 0; i < markers.length; i++) {
        ll = markers[i].getLatLng()
        xy.push([ll.lng, ll.lat])
    }    

    var query = buildQuery(xy);
                
    simpleHttpRequest(query, updateShape)
                    

}




function buildQuery(xy){
    
    return '/path?waypoints='+JSON.stringify(xy) 
}


function makeHttpObject() {
  try {return new XMLHttpRequest();}
  catch (error) {}
  try {return new ActiveXObject("Msxml2.XMLHTTP");}
  catch (error) {}
  try {return new ActiveXObject("Microsoft.XMLHTTP");}
  catch (error) {}

  throw new Error("Could not create HTTP request object.");
}


function simpleHttpRequest(url, success, failure) {
  var request = makeHttpObject();
  
  request.open("GET", url, true);
  request.responseType = 'json';

  request.onreadystatechange = function() {
    
    if (request.readyState == 4) {

      if (request.status == 200){
        
        success(request.response);}
      else if (failure){
        failure(request.status, request.response);
      }
    }
  };
  
  request.send(null);
}


function add_listeners(req, callback){

    req.addEventListener("load", function(){
        if (req.status < 400)
            callback(req.response);
        else 
            callback(null, new Error("Request failed: " + req.statusText));
    });
    
    req.addEventListener("error", function(){
        callback(null, new Error("Network error"));
    });


}