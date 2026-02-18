(function() {
    var POLL_INTERVAL_MS = 3000;
    var container = document.getElementById('exchanges');
    var debateId = container.dataset.debateId;
    var knownCount = container.querySelectorAll('.exchange-item').length;

    function formatDateTime(isoString) {
        if (!isoString) return '';
        var d = new Date(isoString);
        var pad = function(n) { return n < 10 ? '0' + n : n; };
        return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    }

    function renderExchange(ex, posterId) {
        var isPoster = ex.sender_id === posterId;
        var wrapper = document.createElement('div');
        wrapper.className = 'd-flex mb-3 exchange-item' + (isPoster ? '' : ' flex-row-reverse');

        var card = document.createElement('div');
        card.className = 'card ' + (isPoster ? 'bg-body-secondary' : 'bg-primary-subtle');
        card.style.maxWidth = '75%';

        var cardBody = document.createElement('div');
        cardBody.className = 'card-body py-2 px-3';

        var header = document.createElement('div');
        header.className = 'd-flex justify-content-between align-items-center mb-1';
        var strong = document.createElement('strong');
        strong.className = 'small';
        var link = document.createElement('a');
        link.href = '/user/' + ex.sender_id;
        link.className = 'text-decoration-none';
        link.textContent = ex.sender;
        strong.appendChild(link);
        header.appendChild(strong);

        if (ex.turn_number !== null && ex.turn_number !== undefined) {
            var badge = document.createElement('span');
            badge.className = 'badge bg-body-tertiary text-body-emphasis ms-2';
            badge.textContent = 'ターン ' + ex.turn_number;
            header.appendChild(badge);
        }

        var msgP = document.createElement('p');
        msgP.className = 'mb-1';
        msgP.textContent = ex.message;

        var small = document.createElement('small');
        small.className = 'text-muted';
        small.textContent = formatDateTime(ex.sent_at);

        cardBody.appendChild(header);
        cardBody.appendChild(msgP);
        cardBody.appendChild(small);
        card.appendChild(cardBody);
        wrapper.appendChild(card);
        return wrapper;
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
                        p.className = 'text-muted text-center mb-0';
                        p.textContent = 'まだ意見はありません。';
                        container.appendChild(p);
                    } else {
                        data.exchanges.forEach(function(ex) {
                            container.appendChild(renderExchange(ex, data.poster_id));
                        });
                    }
                    knownCount = data.exchanges.length;
                }

                // ターン表示を更新
                var turnIndicator = document.getElementById('turn-indicator');
                if (turnIndicator && data.method === 0) {
                    turnIndicator.textContent = 'ターン ' + (data.current_turn || 1) + ' / ' + (data.max_turns || '∞');
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
