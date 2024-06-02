document.addEventListener("paste", event => {
  const pasted_value = event.clipboardData.getData("text");
  alert(`got value: ${pasted_value}`);
  console.log(pasted_value);

  parse_pasted_value(pasted_value);
});

const data = [];

function parse_pasted_value(string) {
  const possible_separators = ["\t", ","];
  const arguments_to_parse = 6;
  let separator;

  const lines = string.split("\n");
  const first_line = lines[0];

  console.log("contains?", first_line.search(/\t/));
  for (const sep of possible_separators) {
    const value = first_line.split(sep).length;
    console.log(value);

    if (value == arguments_to_parse) {
      separator = sep;
    }
  }

  if (!separator) {
    alert("invalid pasted value: could not parse input.");
    return;
  }
  alert("success!");
  console.log("values:", first_line.split(separator));
}

function generate_table(_rows) {
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
  add_row_button.addEventListener("click", add_row);

  const Table = children(document.createElement("table"),
    Header,
    generate_row(),
    children(document.createElement('tr'),
      children((() => {
	const add_row_cell = document.createElement('td');
	add_row_cell.setAttribute('colspan', 6);
	add_row_cell.classList.add('add-row-cell');

	return add_row_cell;
      })(),
	add_row_button,
      ),
    ),
  );

  return Table;
}

function add_row() {
  alert("here");
}

function generate_row(_idx) {
  const form_elements = [];
  {
    const DateTime = document.createElement('input');
    DateTime.setAttribute('type', 'datetime-local');

    form_elements.push(DateTime);
  }
  {
    const Longitude = document.createElement('input');
    Longitude.setAttribute('type', 'number');
    Longitude.setAttribute('min', -180);
    Longitude.setAttribute('max', 180);

    Longitude.setAttribute('value', 0);
    form_elements.push(Longitude);
  }
  {
    const Latitude = document.createElement('input');
    Latitude.setAttribute('type', 'number');
    Latitude.setAttribute('min', -90);
    Latitude.setAttribute('max', 90);

    Latitude.setAttribute('value', 0);
    form_elements.push(Latitude);
  }
  {
    const Depth = document.createElement('input');
    Depth.setAttribute('type', 'number');
    Depth.setAttribute('min', 0);
    Depth.setAttribute('max', 999);

    Depth.setAttribute('value', 2);
    form_elements.push(Depth);
  }
  {
    const Magnitude = document.createElement('input');
    Magnitude.setAttribute('type', 'number');
    Magnitude.setAttribute('min', 1.0);
    Magnitude.setAttribute('max', 10.0);
    Magnitude.setAttribute('step', 0.1);

    Magnitude.setAttribute('value', 5.0);
    form_elements.push(Magnitude);
  }
  {
    const Location = document.createElement('input');
    Location.setAttribute('type', 'text');
    Location.setAttribute('minlength', 5);
    Location.setAttribute('maxlength', 255);
    Location.setAttribute('size', 20);

    Location.setAttribute('placeholder', "25km coast of Bohol...");
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

document.addEventListener("DOMContentLoaded", () => {
  const Table = generate_table();
  const dummy_table = document.querySelector('#dummy-table');

  replace_node(dummy_table, Table);
});
