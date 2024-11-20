$(document).ready(function() {
    $('body.userrole-manager h1.documentFirstHeading').each(
        function () {
            var h1_title = $(this).text();

            $.ajax(
                'https://tools.agsci.psu.edu/chicago-title/',
                {
                    method: "POST",
                    data: JSON.stringify({title: h1_title}),
                    success: function(data, textStatus, jqXHR) {
                        if (jqXHR.status == 200) {
                            if (data.updated) {
                                var diff_div = $('<div class="chicago-title"></div>');
                                diff_div.html(data.diff.html)
                                $('body.userrole-manager h1.documentFirstHeading').after(diff_div);
                            }
                        }
                    },
                    dataType: 'json',
                    contentType: 'application/json'
                }
            );
        }
    );
});

$(document).ready(function() {
    var post_data = [];

    $('body.userrole-manager #content-core .documentText').children('h2, h3, h4, h5, h6').each(
        function () {

            var title = $(this).text();
            var uuid = crypto.randomUUID();

            $(this).attr('data-chicago', uuid);

            post_data.push({
                title: title,
                identifier: uuid
            })

        }
    );

    $.ajax(
        'https://tools.agsci.psu.edu/chicago-title/',
        {
            method: "POST",
            data: JSON.stringify(post_data),
            success: function(data, textStatus, jqXHR) {
                if (jqXHR.status == 200) {
                    for (el of data) {
                        if (el.updated) {
                            var diff_div = $('<div class="chicago-title"></div>');
                            diff_div.html(el.diff.html)
                            selector = 'body.userrole-manager #content-core .documentText [data-chicago="' +  el.identifier +'"]';
                            $(selector).after(diff_div);
                        }
                    }
                }
                else {
                    console.log("Chicago Title Status: " + jqXHR.status);
                }
            },
            dataType: 'json',
            contentType: 'application/json'
        }
    );

});
