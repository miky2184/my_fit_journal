(() => {
  const hasDesktopNote = document.querySelector('.desktop-note');
  if (!hasDesktopNote) {
    return;
  }

  if (window.innerWidth < 880) {
    const hint = document.createElement('p');
    hint.className = 'muted';
    hint.textContent = 'Suggerimento: per creare programmi complessi usa schermo desktop.';
    hasDesktopNote.appendChild(hint);
  }
})();
