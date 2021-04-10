let {PythonShell} = require('python-shell');
let $ = require('jquery');

$('#send').on('click', () => {
    let sender = $('#sender').val();
    let recipient = $('#recipient').val();
    let amount = $('#amount').val();

    let options = {
        pythonOptions: ['-u'],
        args: [sender, recipient, amount]
    }
});

$('#check').on('click', () => {
    let key = $('#key').val();
});


