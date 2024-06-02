function children(root, ...children) {
	if (children.length === 0 || children == null) return root;

	return children.flat().reduce((acc, el) => {
		acc.appendChild(el);
		return acc;
	}, root);
}

function replace_inside(root, replacement_element) {
	root.innerHTML = "";
	root.appendChild(replacement_element);
}

function replace_node(dummy_element, replacement_element) {
	const parent = dummy_element.parentNode;

	parent.insertBefore(replacement_element, dummy_element);
	parent.removeChild(dummy_element);
}
