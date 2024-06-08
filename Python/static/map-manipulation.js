var map = L.map('map');
map.setView([51.505,-0.09],6.5);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

// Load JSON data using Fetch API
fetch('../resources/active_faults_2015.json')
  .then(response => response.json())
  .then(data => {
    displayFaultLines(data);
  });

navigator.geolocation.watchPosition(success, error);

let marker, circle, zoomed;

function success(pos){
  const lat = pos.coords.latitude;
  const lng = pos.coords.longitude;
  const accuracy = pos.coords.accuracy;

  if(marker){
    map.removeLayer(marker);
    map.removeLayer(circle);
  }

  marker = L.marker([lat, lng]).addTo(map);
  circle = L.circle([lat,lng], {radius: accuracy}).addTo(map);

  if (!zoomed){
    zoomed = map.fitBounds(circle.getBounds());
  }
  
  map.setView([lat, lng],4.5);
}

function error(err){
  if (err.code === 1){
    alert("Please allow geolocation success");
  } else {
    alert("Cannot get current location");
  }
}

