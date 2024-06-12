
    // Function to fetch earthquake forecast data
    function fetchForecastData() {
        // Get selected algorithm and start date
        var algorithm = document.getElementById('forecast-algorithm').value;
        var startDate = document.getElementById('prediction-start-date').value;

        // Send AJAX request to the server
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/perform-clustering', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            if (xhr.status === 200) {
                // Parse response data
                var data = JSON.parse(xhr.responseText);
                // Update the table with the forecast data
                updateForecastTable(data);
            } else {
                console.error('Error fetching forecast data: ' + xhr.statusText);
            }
        };
        xhr.onerror = function () {
            console.error('Network error while fetching forecast data');
        };
        xhr.send(JSON.stringify({
            algorithm: algorithm,
            startDate: startDate
        }));
    }

    // Function to update the forecast table with the fetched data
    function updateForecastTable(data) {
        var forecastTable = document.getElementById('forecast-table');
        // Loop through the forecast data and update the table rows
        data.forEach(function (entry, index) {
            var actualDataCell = forecastTable.rows[1].cells[index];
            var forecastDataCell = forecastTable.rows[2].cells[index];
            actualDataCell.textContent = entry.actual_value;
            forecastDataCell.textContent = entry.predicted_value;
        });
    }

    // Trigger the AJAX request when the page loads
    window.onload = function () {
        fetchForecastData();
    };