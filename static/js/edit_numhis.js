$(document).ready(function () {
    $('#history').submit(function (event) {
        event.preventDefault();
        $.ajax({
            type: 'POST',
            url: '/edit_fetch_history',
            data: $(this).serialize(),
            success: function (data) {
                updateHistoryTable(data);
                updateTextColor();
            },
            error: function (error) {
                console.log('Error:', error);
            }
        });
    });
    $('#current').submit(function (event) {
        event.preventDefault();

        $.ajax({
            type: 'POST',
            url: '/edit_fetch_current',
            data: $(this).serialize(),
            success: function (data) {
                updateCurrentTable(data);
                updateTextColor();
            },
            error: function (error) {
                console.log('Error:', error);
            }
        });
    });



    
    function updateCurrentTable(data) {
        updateTableRows('#currentTable', data.showed);
        updateTextColor();
    }

    function updateHistoryTable(data) {
        updateTableRows('#historyTable', data.expired);
        updateTextColor();
    }


    function updateTableRows(tableId, rows) {
        var table = $(tableId + ' tbody');
        table.find('tr:gt(0)').remove();
        $.each(rows, function (index, row) {
            table.append('<tr>' +
                '<td>' + row[0] + '</td>' +
                '<td id="name">' + row[1] + '</td>' +
                '<td>' + row[2] + '</td>' +
                '<td class="birthday">' + row[3] + '</td>' +
                '</tr>');
        });
    }
});
