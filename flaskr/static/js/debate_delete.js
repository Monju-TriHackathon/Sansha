document.getElementById('delete-btn').addEventListener('click', function() {
    if (!confirm('本当にこの議論を削除しますか？')) {
        return;
    }

    const debateId = this.dataset.debateId;

    // サーバーに削除リクエストを送信
    fetch('/debates/' + debateId + '/delete', {
        method: 'POST'
    })
    .then(function(response) {
        if (response.ok) {
            location.href = '/debates';
        } else {
            alert('削除に失敗しました。');
        }
    })
    .catch(function() {
        alert('通信エラーが発生しました。');
    });
});
