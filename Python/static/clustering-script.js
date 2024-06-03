document.addEventListener("paste", event => {
  const pasted_value = event.clipboardData.getData("text");
  show_paste_interface(pasted_value);
});

let pasted_data;
function show_paste_interface(pasted_value) {
  const max_characters_to_show = 100;

  let preview_paste = pasted_value.split('\n')[0];
  if (preview_paste.length > max_characters_to_show) {
    preview_paste = preview_paste.slice(0, max_characters_to_show);
  }
  preview_paste += "...";

  const paste_preview = document.querySelector('#pasted-value-preview');
  paste_preview.textContent = preview_paste;

  pasted_data = pasted_value;

  const paste_interface_popup = document.querySelector('#paste-interface-popup');
  paste_interface_popup.showModal();
}

function add_pasted_values({ override = false }) {
  if (!pasted_data) {
    return;
  }

  if (override) {
    data_rows = [];
  }

  const dataset_row_obj = parse_pasted_value(pasted_data);
  for (const generated_row of dataset_row_obj) {
    data_rows.push(generate_row(generated_row));
  }
  const new_table = generate_table(data_rows);

  replace_node(dataset_table_element, new_table);
  dataset_table_element = new_table;

  const paste_interface_popup = document.querySelector('#paste-interface-popup');
  const dataset_popup = document.querySelector('#dataset-updater-popup');

  paste_interface_popup.close();
  dataset_popup.showModal();
}

function parse_pasted_value(string) {
  const possible_separators = ["\t", ","];
  const arguments_to_parse = 6;
  let separator;

  const lines = string.split("\n");
  const first_line = lines[0];

  console.log("contains?", first_line.search(/\t/));
  for (const sep of possible_separators) {
    const value = first_line.split(sep).length;

    if (value == arguments_to_parse) {
      separator = sep;
    }
  }

  if (!separator) {
    alert("invalid pasted value: could not parse input.");
    return;
  }

  const parsed_values = [];
  for (const line of lines) {
    const arguments = line.split(separator).map(arg => arg.trim());
    let [date_time, latitude, longitude, depth, magnitude, location] = arguments;
    console.log(arguments);

    const date_in_millis = Date.parse(date_time.replace("-", ","));
    console.log(date_in_millis);
    if (isNaN(date_in_millis)) {
      throw new Error("Parsing of date failed.");
    }

    // solution in: https://stackoverflow.com/questions/30166338/setting-value-of-datetime-local-from-date/61082536#61082536
    {
      now = new Date(date_in_millis);
      now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
      date_time = now.toISOString().slice(0,16);
    }

    latitude = parseFloat(latitude);
    longitude = parseFloat(longitude);
    depth = parseInt(depth);
    magnitude = parseFloat(magnitude);
    
    parsed_values.push({
      date_time,
      latitude,
      longitude,
      depth,
      magnitude,
      location,
    });
  }

  return parsed_values;
}

let data_rows = [generate_row({})];
function generate_table(rows) {
  const Header = children(document.createElement('tr'),
    [
      "Date - Time (Philippine Time)",
      "Latitude (ºN)",
      "Longitude (ºE)",
      "Depth (km)",
      "Magnitude",
      "Location"
    ].map(text => {
      const result = document.createElement('th');
      result.textContent = text;

      return result;
    }),
  );

  const add_row_button = document.createElement('button');
  add_row_button.classList.add('add-row-button');
  add_row_button.textContent = "Add row";
  add_row_button.addEventListener("click", () => {
    data_rows.push(generate_row({}));
    const new_table = generate_table(data_rows);
    console.log(new_table);

    replace_node(dataset_table_element, new_table);
    dataset_table_element = new_table;
  });

  const table_children = [];
  if (rows) {
    table_children.push(rows);
  }

  const add_row_cell = document.createElement('td');
  add_row_cell.setAttribute('colspan', 6);
  add_row_cell.classList.add('add-row-cell');

  const add_row_table_row = children(document.createElement('tr'),
    children(add_row_cell,
      add_row_button,
    ),
  );
  table_children.push(add_row_table_row);

  const Table = children(document.createElement("table"),
    Header,
    table_children,
  );

  return Table;
}

function add_row() {
  alert("here");
}

function generate_row({
    date_time = "2024-01-01T00:00",
    latitude = 21.1,
    longitude = 21.1,
    depth = 0,
    magnitude = 5.0,
    location = "",
}) {
  const form_elements = [];
  {
    const DateTime = document.createElement('input');
    DateTime.setAttribute('type', 'datetime-local');

    DateTime.setAttribute('value', date_time);
    form_elements.push(DateTime);
  }
  {
    const Latitude = document.createElement('input');
    Latitude.setAttribute('type', 'number');
    Latitude.setAttribute('min', -90);
    Latitude.setAttribute('max', 90);

    Latitude.setAttribute('value', latitude);
    form_elements.push(Latitude);
  }
  {
    const Longitude = document.createElement('input');
    Longitude.setAttribute('type', 'number');
    Longitude.setAttribute('min', -180);
    Longitude.setAttribute('max', 180);

    Longitude.setAttribute('value', longitude);
    form_elements.push(Longitude);
  }
  {
    const Depth = document.createElement('input');
    Depth.setAttribute('type', 'number');
    Depth.setAttribute('min', 0);
    Depth.setAttribute('max', 999);

    Depth.setAttribute('value', depth);
    form_elements.push(Depth);
  }
  {
    const Magnitude = document.createElement('input');
    Magnitude.setAttribute('type', 'number');
    Magnitude.setAttribute('min', 1.0);
    Magnitude.setAttribute('max', 10.0);
    Magnitude.setAttribute('step', 0.1);

    Magnitude.setAttribute('value', magnitude);
    form_elements.push(Magnitude);
  }
  {
    const Location = document.createElement('input');
    Location.setAttribute('type', 'text');
    Location.setAttribute('minlength', 5);
    Location.setAttribute('maxlength', 255);
    Location.setAttribute('size', 20);

    Location.setAttribute('placeholder', location);
    form_elements.push(Location);
  }
 
  const Row = children(document.createElement('tr'),
    form_elements.map(input_el => {
      return children(document.createElement('td'),
	input_el
      );
    }),
  );
  return Row;
}

let dataset_table_element;
document.addEventListener("DOMContentLoaded", () => {
  const Table = generate_table(data_rows);
  const dummy_table = document.querySelector('#dummy-table');

  replace_node(dummy_table, Table);
  dataset_table_element = Table;
});
