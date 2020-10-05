async function sensor_info(sensorID) {
  console.log(`${sensorID} stats`)

  await $.ajax({
    url : '/get_df',
    dataType: "json",
    data: {jdata: JSON.stringify(sensorID)},
    contentType: 'application/json;charset=UTF-8',
    success: function (data) {
          console.log(data);
          var ctx = document.getElementById(`${sensorID} stats`);
          console.log(ctx)
          var plotData = data
                  var myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                      labels: plotData['timestamp'],
                      datasets: [{
                        data: plotData['PM10'],
                        label: 'PM10', 
                        borderColor: 'orange', 
                        fill: false
                      }, 
                      {
                        data: plotData['PM2_5'],
                        label: 'PM2.5',
                        borderColor: 'blue', 
                        fill: false
                      }]
                    },
                    options: {
                      responsive: true,
                      title: {
                        display: true,
                        text: `Werte am Sensor: ${sensorID}`
                      }, 
                       tooltips: {
                         mode: 'label', 
                       },
                       hover: {
                        mode: 'nearest',
                        intersect: false
                      },
                      scales: {
                        xAxes: [{
                          ticks: {
                            display: false,
                          }
                        }]
                      }
                    }
                  });
        }
    });


}

function passVar(json, apikey) {
  var sensors = json
  
  // Initialize the platform object:
  const api_key = apikey
  var platform = new H.service.Platform({
    'apikey': api_key
  });
    
  const lat = (51.4762 + 52.2396) / 2
  const long = (8.3255 + 9.5537) / 2

  // Obtain the default map types from the platform object
  var maptypes = platform.createDefaultLayers()
  maptypes.vector.normal.map.setMin(9)

  // Instantiate (and display) a map object:
  var map = new H.Map(
    document.getElementById('mapContainer'),
    maptypes.vector.normal.map,
    {
      zoom: 9.7,
      center: { lat: lat, lng: long },
      pixelRatio: window.devicePixelRatio || 1
    });

  window.addEventListener('resize', () => map.getViewPort().resize())

  // Behavior implements default interactions for pan/zoom 
  var behavior = new H.mapevents.Behavior(new H.mapevents.MapEvents(map))

  var ui = H.ui.UI.createDefault(map, maptypes)

  // drawing a marker for each sensor
  var json = JSON.parse(sensors)
  console.log(Object.keys(json).length)

  for(var i = 0; i < Object.keys(json).length; i++) {
    var sensor_lat = json[i]['latitude']
    var sensor_lon = json[i]['longitude']

    var outerElement = document.createElement('div')
    var innerElement = document.createElement('div')
    
    outerElement.style.color = 'white'
    outerElement.style.backgroundColor = 'green'
    if(json[i]['PM10'] >= 50 || json[i]['PM2_5'] >= 25) {
      outerElement.style.background = 'red'
    }
    else if(json[i]['PM10'] >= 40 || json[i]['PM2_5'] >= 20) {
      outerElement.style.backgroundColor = 'yellow'
    }
    outerElement.style.border = '2px solid black'
    outerElement.style.font = 'normal 10px arial'
    outerElement.style.borderRadius = '80%'
    outerElement.style.width = '3em'
    outerElement.style.height = '3.5em'
    outerElement.style.textAlign = 'center'
    outerElement.style.marginTop = '-1.75em'
    outerElement.style.marginLeft = '- 1.5em'
    
    innerElement.innerHTML = `<p>${ json[i]["PM10"] }<br>${ json[i]["PM2_5"] }</p>`
    innerElement.style.marginTop = '-0.5em'
    innerElement.style.textShadow = '0 0 2px #FF0000, 0 0 5px #0000FF'

    outerElement.appendChild(innerElement)
    var icon = new H.map.DomIcon(outerElement)
    var marker = new H.map.DomMarker({ lat: sensor_lat, lng: sensor_lon }, {icon: icon})

    // Adding eventListener to the marker
    const sensorData = json[i]
    marker.addEventListener('tap', function(evt) {
      console.log(sensorData);
      console.log(evt.target.getGeometry());
      map.setCenter(evt.target.getGeometry())
      map.setZoom(15)

      var bubbleHTML = document.createElement('div')
      //bubbleHTML.setAttribute("id", "sensor stats")
      bubbleHTML.innerHTML = `
        <p>Standort: ${sensorData['location']}, SensorID: ${sensorData['sensor_id']}, timestamp: ${sensorData['timestamp']}, PM10: ${sensorData['PM10']}, PM2.5: ${sensorData['PM2_5']}</p>
        <canvas id = '${sensorData['sensor_id']} stats' width= 550; height= 350;></canvas>
      `

      sensor_info(sensorData['sensor_id'])
      var bubble = new H.ui.InfoBubble(evt.target.getGeometry(), {
        content: bubbleHTML,
      })
      ui.addBubble(bubble)
    }, false);
    // Add the marker to the map:
    map.addObject(marker);
  }

  // Add bounds to the map so that the markers are always visible
  var bounds = new H.geo.Rect(51.4762, 8.3255, 52.2396, 9.5537)
  map.getViewModel().addEventListener('sync', function() {
    var center = map.getCenter();

    if (!bounds.containsPoint(center)) {
      if (center.lat > bounds.getTop()) {
        center.lat = bounds.getTop();
      } else if (center.lat < bounds.getBottom()) {
        center.lat = bounds.getBottom();
      }
      if (center.lng < bounds.getLeft()) {
        center.lng = bounds.getLeft();
      } else if (center.lng > bounds.getRight()) {
        center.lng = bounds.getRight();
      }
      map.setCenter(center);
    }
  });
}

