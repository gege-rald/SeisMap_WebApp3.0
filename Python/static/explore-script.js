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



const rangeInput = document.querySelectorAll(".range-input input"),
  priceInput = document.querySelectorAll(".price-input input"),
  range = document.querySelector(".slider .progress");
let priceGap = 0; // Adjust the gap between allowed values

function updateRange(minVal, maxVal) {
  priceInput[0].value = minVal.toFixed(1);
  priceInput[1].value = maxVal.toFixed(1);
  range.style.left = ((minVal / rangeInput[0].max) * 100) + "%";
  range.style.right = 100 - (maxVal / rangeInput[1].max) * 100 + "%";
}

function validateInput(value, min, max) {
  // Restrict input values within the allowed range
  return Math.min(Math.max(value, min), max);
}

priceInput.forEach(input => {
  input.addEventListener("input", e => {
    let minPrice = parseFloat(validateInput(priceInput[0].value, 1.0, 7.4));
    let maxPrice = parseFloat(validateInput(priceInput[1].value, 1.0, 7.4));

    if ((maxPrice - minPrice >= priceGap) && maxPrice <= rangeInput[1].max) {
      if (e.target === priceInput[0]) {
        rangeInput[0].value = minPrice;
      } else {
        rangeInput[1].value = maxPrice;
      }
      updateRange(minPrice, maxPrice);
    } else {
      // Enforce minimum gap between min and max values
      if (maxPrice - minPrice < priceGap) {
        if (e.target === priceInput[0]) {
          priceInput[0].value = maxPrice - priceGap;
        } else {
          priceInput[1].value = minPrice + priceGap;
        }
      }
      updateRange(validateInput(priceInput[0].value, 1.0, 7.4), validateInput(priceInput[1].value, 1.0, 7.4));
    }
  });
});

rangeInput.forEach(input => {
  input.addEventListener("input", e => {
    let minVal = parseFloat(rangeInput[0].value);
    let maxVal = parseFloat(rangeInput[1].value);

    if ((maxVal - minVal) < priceGap) {
      if (e.target === rangeInput[0]) {
        rangeInput[0].value = maxVal - priceGap;
      } else {
        rangeInput[1].value = minVal + priceGap;
      }
    } else {
      updateRange(minVal, maxVal);
    }
  });
});


//Depth Range picker

const rangeInputDepth = document.querySelectorAll(".range-input-depth input"),
priceInputDepth = document.querySelectorAll(".price-input-depth input"),
rangeDepth = document.querySelector(".slider-depth .progress-depth");
let priceGapDepth = 1000;

priceInputDepth.forEach(input =>{
    input.addEventListener("input", e =>{
        let minPrice = parseInt(priceInputDepth[0].value),
        maxPrice = parseInt(priceInputDepth[1].value);
        
        if((maxPrice - minPrice >= priceGapDepth) && maxPrice <= rangeInputDepth[1].max){
            if(e.target.className === "input-min-depth"){
                rangeInputDepth[0].value = minPrice;
                range.style.left = ((minPrice / rangeInputDepth[0].max) * 100) + "%";
            }else{
                rangeInputDepth[1].value = maxPrice;
                range.style.right = 100 - (maxPrice / rangeInputDepth[1].max) * 100 + "%";
            }
        }
    });
});

rangeInputDepth.forEach(input =>{
    input.addEventListener("input", e =>{
        let minVal = parseInt(rangeInputDepth[0].value),
        maxVal = parseInt(rangeInputDepth[1].value);

        if((maxVal - minVal) < priceGapDepth){
            if(e.target.className === "range-min-depth"){
                rangeInputDepth[0].value = maxVal - priceGapDepth
            }else{
                rangeInputDepth[1].value = minVal + priceGapDepth;
            }
        }else{
            priceInputDepth[0].value = minVal;
            priceInputDepth[1].value = maxVal;
            range.style.left = ((minVal / rangeInputDepth[0].max) * 100) + "%";
            range.style.right = 100 - (maxVal / rangeInputDepth[1].max) * 100 + "%";
        }
    });
});
