// 通知ポップアップ（ドロップダウン）
(function () {
  var POLL_INTERVAL_MS = 15000;
  var badge = document.getElementById('notification-badge');
  var list = document.getElementById('notification-list');

  function fetchNotifications() {
    fetch('/notification/api/recent')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        // 未読バッジ更新
        if (data.unread_count > 0) {
          badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
          badge.classList.remove('d-none');
        } else {
          badge.classList.add('d-none');
        }

        // リスト描画
        if (data.notifications.length === 0) {
          list.innerHTML = '<p class="text-center text-muted py-3 mb-0">通知はありません</p>';
          return;
        }

        var html = '';
        data.notifications.forEach(function (n) {
          var cls = n.is_read ? '' : 'bg-body-secondary';
          html += '<div class="dropdown-item-text border-bottom px-3 py-2 ' + cls + '">'
            + '<div class="small">' + escapeHtml(n.message) + '</div>'
            + '<div class="text-muted" style="font-size:.75rem">' + n.created_at + '</div>'
            + '</div>';
        });
        list.innerHTML = html;
      })
      .catch(function () { /* ネットワークエラーは次回ポーリングで再試行 */ });
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
  }

  // ドロップダウンを開いたとき既読にする
  var bell = document.getElementById('notification-bell');
  if (bell) {
    bell.addEventListener('shown.bs.dropdown', function () {
      fetch('/notification/api/mark_read', { method: 'POST' })
        .then(function () {
          badge.classList.add('d-none');
        });
    });
  }

  // 初回取得 + ポーリング
  fetchNotifications();
  setInterval(fetchNotifications, POLL_INTERVAL_MS);
})();
