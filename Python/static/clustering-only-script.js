document.addEventListener('DOMContentLoaded', () => {
  const clustering_select = document.querySelector('#clustering-algorithm');
  const clusters_input = document.querySelector('#clusters');

  clustering_select.addEventListener('input', () => {
    if (clustering_select.value == "dbscan") {
      clusters_input.disabled = true;
    } else {
      clusters_input.disabled = false;
    }
  });

  document.getElementById('submit-button').addEventListener('click', handle_submit_button);
});

// sending of data to the flask server 
function handle_submit_button() {
  const algorithm = document.getElementById('clustering-algorithm').value;
  const clusters = document.getElementById('clusters').value;
  const magnitudeMin = document.querySelector('.input-min').value;
  const magnitudeMax = document.querySelector('.input-max').value;
  const depthMin = document.querySelector('.input-min-depth').value;
  const depthMax = document.querySelector('.input-max-depth').value;
  const startDate = document.getElementById('start-date').value;
  const endDate = document.getElementById('end-date').value;

  const data = {
      algorithm: algorithm,
      clusters: clusters,
      magnitudeRange: { min: magnitudeMin, max: magnitudeMax },
      depthRange: { min: depthMin, max: depthMax },
      dateRange: { start: startDate, end: endDate }
  };

  fetch('/perform-clustering', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
  })
  .then(response => {
      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
  })
  .then(data => {
      console.log('Success:', data);
  })
  .catch((error) => {
      console.error('Error:', error);
  });
}

