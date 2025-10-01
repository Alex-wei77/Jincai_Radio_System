$(document).ready(function () {
    // 获取 CSRF token
    var csrfToken = $('meta[name="csrf-token"]').attr('content');

    $('#history').submit(function (event) {
        event.preventDefault();
        $.ajax({
            type: 'POST',
            url: '/edit_fetch_history_manage',
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
            url: '/edit_fetch_current_manage',
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
                '<td class="invisibility">' + row[10] + '</td>' + //隐藏性
                '<td>' + row[1] + '</td>' + //日期
                '<td id="name">' + row[2] + '</td>' + //歌名
                '<td>' + row[3] + '</td>' + //作曲者
                '<td>' + row[4] + '</td>' + //点歌对象
                '<td>' + row[5] + '</td>' + //点歌者
                '<td id="note">' + row[6] + '</td>' + //点歌者
                '<td class="birthday">' + row[9] + '</td>' + //生日
                '<td id="manage"><div class="container">' +
                '<form class="table" method="post" action="/delete"><input type="hidden" value="' + row[0] + '" name="id"><input type="hidden" name="csrf_token" value="' + csrfToken + '"><input type="submit" value="删除"></form>' +
                '<form class="table" method="post" action="/edit"><input type="hidden" value="' + row[0] + '" name="id"><input type="hidden" name="csrf_token" value="' + csrfToken + '"><input type="submit" value="修改"></form>' +
                '<form class="table" method="post" action="/alter"><input type="hidden" value="' + row[0] + '" name="id"><input type="hidden" name="csrf_token" value="' + csrfToken + '"><input type="submit" value="修改隐藏"></form>' +
                '<form class="table" method="post" action="/detail"><input type="hidden" value="' + row[0] + '" name="id"><input type="hidden" name="csrf_token" value="' + csrfToken + '"><input type="submit" value="更多信息"></form>' +
                '</div></td>' +
                '</tr>');
        });
    }
});
