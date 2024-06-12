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
});
