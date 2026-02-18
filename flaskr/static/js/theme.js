// テーマ切替（ライト/ダーク）
(function () {
  var STORAGE_KEY = 'sansha-theme';
  var html = document.documentElement;
  var icon = document.getElementById('theme-icon');

  function syncIcon() {
    if (icon) {
      var current = html.getAttribute('data-bs-theme') || 'light';
      icon.className = current === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }
  }

  // アイコンだけ同期（テーマ自体は head 内のインラインスクリプトで適用済み）
  syncIcon();

  var btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', function () {
      var current = html.getAttribute('data-bs-theme') || 'light';
      var next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-bs-theme', next);
      localStorage.setItem(STORAGE_KEY, next);
      syncIcon();
    });
  }
})();
