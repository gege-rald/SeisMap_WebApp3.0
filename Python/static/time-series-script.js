const prediction_date_length = 15;
const lookup_month = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

document.addEventListener('DOMContentLoaded', () => {
  const predict_input = document.querySelector('#prediction-start-date');
  predict_input.addEventListener('input', update_forecast_dates);

  update_forecast_dates({ target: predict_input });

  iframe_send_notification({ title: "Model updating...", timer: true });
});

function update_forecast_dates(event) {
  const first_month = document.querySelector('.forecast-months .first');
  const second_month = document.querySelector('.forecast-months .second');
  const dates = document.querySelectorAll('.forecast-dates th');

  const { months, days, possible_second_month_index } = get_forecast_dates(event.target.value);

  for (const [i, date] of dates.entries()) {
    date.innerHTML = days[i];
  }
  const first_month_h2 = first_month.querySelector('h2');
  first_month_h2.innerHTML = lookup_month[months.shift()];

  if (months.length === 0) {
    first_month.setAttribute('colspan', prediction_date_length);
    second_month.classList.add('hidden');
    return;
  }

  const second_month_h2 = second_month.querySelector('h2');
  second_month_h2.innerHTML = lookup_month[months.shift()];

  const first_month_days = possible_second_month_index;
  const second_month_days = prediction_date_length - possible_second_month_index;
  
  first_month.setAttribute('colspan', first_month_days);
  second_month.setAttribute('colspan', second_month_days);
  second_month.classList.remove('hidden');
}

function get_forecast_dates(start_date) {
  const prediction_dates = [];

  for (let date_offset = 0; date_offset < prediction_date_length; date_offset++) {
    // increment_date function from explore-script.js
    prediction_dates.push(increment_date(start_date, date_offset));
  }
  const days = prediction_dates.map(prediction_date => prediction_date.getDate());

  const first_month = prediction_dates[0].getMonth();
  const months = [];
  months.push(first_month);

  const possible_second_month_index = prediction_dates.findIndex(date => {
    return date.getMonth() !== first_month;
  });
  if (possible_second_month_index !== -1) {
    months.push(prediction_dates[possible_second_month_index].getMonth());
  }

  return { months, days, possible_second_month_index };
}
