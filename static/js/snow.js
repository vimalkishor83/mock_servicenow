/* Auto-submit filter forms after select changes */
document.querySelectorAll(".card-body select").forEach(sel => {
  sel.addEventListener("change", () => sel.closest("form").submit());
});
