(function() {
    var POLL_INTERVAL_MS = 3000;
    var container = document.getElementById('exchanges');
    var debateId = container.dataset.debateId;
    var knownCount = container.querySelectorAll('.exchange-item').length;

    function renderExchange(ex) {
        var li = document.createElement('li');
        li.className = 'exchange-item';
        var strong = document.createElement('strong');
        strong.textContent = ex.sender;
        li.appendChild(strong);
        if (ex.turn_number !== null && ex.turn_number !== undefined) {
            li.appendChild(document.createTextNode(' (ターン ' + ex.turn_number + ')'));
        }
        li.appendChild(document.createElement('br'));
        li.appendChild(document.createTextNode(ex.message));
        li.appendChild(document.createElement('br'));
        var small = document.createElement('small');
        small.textContent = ex.sent_at || '';
        li.appendChild(small);
        return li;
    }

    function poll() {
        fetch('/debates/' + debateId + '/exchanges')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.status !== 'success') return;

                // 新しいメッセージがあれば更新
                if (data.exchanges.length !== knownCount) {
                    // リストを再構築
                    container.innerHTML = '';
                    if (data.exchanges.length === 0) {
                        var p = document.createElement('p');
                        p.textContent = 'まだ意見はありません。';
                        container.appendChild(p);
                    } else {
                        var ul = document.createElement('ul');
                        data.exchanges.forEach(function(ex) {
                            ul.appendChild(renderExchange(ex));
                        });
                        container.appendChild(ul);
                    }
                    knownCount = data.exchanges.length;
                }

                // 議論が終了・投票に移行した場合はリロード
                if (data.state !== 1) {
                    location.reload();
                    return;
                }
            })
            .catch(function() { /* ネットワークエラーは次回ポーリングで再試行 */ });
    }

    setInterval(poll, POLL_INTERVAL_MS);
})();
