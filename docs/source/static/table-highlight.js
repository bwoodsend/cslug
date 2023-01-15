/* Set different font colors for table cells containing '✓' and '✗'. */

window.onload = function() {
  for (let cell of document.getElementsByTagName('td')) {
    if (cell.textContent.match("✓")) {
      cell.style.color = "#1E432E";
    }
    if (cell.textContent.match("✗")) {
      cell.style.color = "#BBA";
    }
  }
};
