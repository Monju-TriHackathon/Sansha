document.getElementById('submit-btn').addEventListener('click', function() {
    const message = document.getElementById('message').value;
    const resultMsg = document.getElementById('result-msg');
    const debateId = document.getElementById('submit-btn').dataset.debateId;

    // サーバーに意見を送信
    fetch('/debates/' + debateId + '/post', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        resultMsg.textContent = data.message;
        if (data.status === 'success') {
            document.getElementById('message').value = '';
        }
    })
    .catch(function() {
        resultMsg.textContent = '通信エラーが発生しました。';
    });
});
