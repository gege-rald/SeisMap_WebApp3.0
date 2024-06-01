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




function updateRange(minVal, maxVal, price_elements, progress_element, reference) {
  if (reference.step == 1) {
    price_elements[0].value = parseInt(minVal);
    price_elements[1].value = parseInt(maxVal);
  } else {
    price_elements[0].value = minVal.toFixed(1);
    price_elements[1].value = maxVal.toFixed(1);
  }

  const true_min = reference.min;
  const true_max = reference.max;

  const min_val_ratio = (minVal - true_min) / (true_max - true_min);
  const max_val_ratio = (maxVal - true_min) / (true_max - true_min);

  progress_element.style["left"] = (min_val_ratio * 100) + "%";
  progress_element.style["right"] = 100 - (max_val_ratio * 100) + "%";
}

function validateInput(value, min, max) {
  // Restrict input values within the allowed range
  return Math.min(Math.max(value, min), max);
}

document.addEventListener("DOMContentLoaded", () => {
  const rangeInput = document.querySelectorAll(".range-input input");
  const priceInput = document.querySelectorAll(".price-input input");
  const range = document.querySelector(".slider .progress");

  let priceGap = 0; // Adjust the gap between allowed values
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
	updateRange(minPrice, maxPrice, priceInput, range, rangeInput[0]);
      } else {
	// Enforce minimum gap between min and max values
	if (maxPrice - minPrice < priceGap) {
	  if (e.target === priceInput[0]) {
	    priceInput[0].value = maxPrice - priceGap;
	  } else {
	    priceInput[1].value = minPrice + priceGap;
	  }
	}

	  const bounded_min = validateInput(priceInput[0].value, 1.0, 7.4);
	  const bounded_max = validateInput(priceInput[1].value, 1.0, 7.4);

	  updateRange(bounded_min, bounded_max, range, rangeInput[0]);
      }
	console.log(range);
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
	updateRange(minVal, maxVal, priceInput, range, rangeInput[0]);
      }
    });
  });
});

//Depth Range picker


document.addEventListener("DOMContentLoaded", () => {
  const rangeInputDepth = document.querySelectorAll(".range-input-depth input");
  const priceInputDepth = document.querySelectorAll(".price-input-depth input");
  const rangeDepth = document.querySelector(".slider-depth .progress-depth");

  let priceGapDepth = 0;

  priceInputDepth.forEach(input =>{
      input.addEventListener("input", e =>{
	  let minPrice = parseInt(priceInputDepth[0].value),
	  maxPrice = parseInt(priceInputDepth[1].value);
	  
	  if ((maxPrice - minPrice >= priceGapDepth) && maxPrice <= rangeInputDepth[1].max) {
	      if (e.target === priceInput[0]) {
		rangeInputDepth[0].value = minPrice;
	      } else {
		rangeInputDepth[1].value = maxPrice;
	      }
	      updateRange(minPrice, maxPrice, priceInputDepth, rangeDepth, rangeInputDepth[0]);
	  } else {
	      const bounded_min = validateInput(priceInputDepth[0].value, 0, 1068);
	      const bounded_max = validateInput(priceInputDepth[1].value, 0, 1068);

	      updateRange(bounded_min, bounded_max, rangeDepth, rangeInputDepth[0]);
	  }
      });
  });

  rangeInputDepth.forEach(input =>{
      input.addEventListener("input", e =>{
	  let minVal = parseInt(rangeInputDepth[0].value);
	  let maxVal = parseInt(rangeInputDepth[1].value);

	  if((maxVal - minVal) < priceGapDepth){
	      if(e.target.className === "range-min-depth"){
		  rangeInputDepth[0].value = maxVal - priceGapDepth
	      }else{
		  rangeInputDepth[1].value = minVal + priceGapDepth;
	      }
	      updateRange(minVal, maxVal, priceInputDepth, rangeDepth, rangeInputDepth[0]);
	  }else{
	      updateRange(minVal, maxVal, priceInputDepth, rangeDepth, rangeInputDepth[0]);
	  }
      });
  });

  const minVal = priceInputDepth[0].value;
  const maxVal = priceInputDepth[1].value;
  updateRange(minVal, maxVal, priceInputDepth, rangeDepth, rangeInputDepth[0]);
});

function increment_date(date_string, days) {
  console.log(date_string);
  const date = new Date(Date.parse(date_string));
  date.setDate(date.getDate() + days);

  const year = date.getFullYear();
  let month = date.getMonth() + 1;
  let day = date.getDay() + 1;

  if (month.toString().length == 1) {
    month = "0" + month;
  }

  if (day.toString().length == 1) {
    day = "0" + day;
  }

  const formatted_date = `${year}-${month}-${day}`;
  return formatted_date;
}

// Date range picker
document.addEventListener("DOMContentLoaded", () => {
  const [start_date_picker, end_date_picker] = document.querySelectorAll('.date-range-picker input[type="date"]');

  start_date_picker.addEventListener("input", () => {
    const incremented_date = increment_date(start_date_picker.value, 1);
    console.log(incremented_date);
    end_date_picker.min = incremented_date;
  });

  end_date_picker.addEventListener("input", () => {
    const incremented_date = increment_date(end_date_picker.value, -1);
    start_date_picker.max = incremented_date;
  });
});
