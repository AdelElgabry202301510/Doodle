document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const themeButton = document.getElementById('theme-toggle');
  const savedTheme = localStorage.getItem('doodle-theme');

  if (savedTheme === 'dark') {
    body.classList.add('dark-theme');
    themeButton.textContent = 'Light';
  }

  if (themeButton) {
    themeButton.addEventListener('click', () => {
      const dark = body.classList.toggle('dark-theme');
      themeButton.textContent = dark ? 'Light' : 'Dark';
      localStorage.setItem('doodle-theme', dark ? 'dark' : 'light');
    });
  }

  const queryInput = document.getElementById('query-input');
  if (queryInput) {
    let debounceTimer;
    queryInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        if (!queryInput.value.trim()) {
          return;
        }
        fetchSuggestions(queryInput.value.trim());
      }, 140);
    });
  }
});

function fetchSuggestions(value) {
  fetch('/autocomplete?q=' + encodeURIComponent(value))
    .then((response) => response.json())
    .then((suggestions) => {
      const list = document.getElementById('suggestions');
      if (!list) {
        return;
      }
      list.innerHTML = '';
      suggestions.forEach((text) => {
        const option = document.createElement('option');
        option.value = text;
        list.appendChild(option);
      });
    })
    .catch(() => {
      // keep experience smooth even if autocomplete fails
    });
}
