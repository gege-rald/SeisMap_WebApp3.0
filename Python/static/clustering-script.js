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
    // Rows,
    children(document.createElement('tr'),
      children(document.createElement('td'),
	add_row_button,
      ),
    ),
  );
  {
    const temp = Table.querySelector('td');
    temp.setAttribute('colspan', 6);
    temp.classList.add('add-row-cell');
  }

  return Table;
}

function add_row() {
  alert("here");
}

document.addEventListener("DOMContentLoaded", () => {
  const Table = generate_table();
  const dummy_table = document.querySelector('#dummy-table');

  replace_node(dummy_table, Table);
});
