/* Set different font colors for table cells containing '✓' and '✗'. */

$(window).bind("load", function() {
  for (let cell of $('td')) {
    if (cell.textContent.match("✓")) {
      cell.style.color = "#1E432E";
    }
    if (cell.textContent.match("✗")) {
      cell.style.color = "#BBA";
    }
  }
});
