$('document').ready(
    function () {

    $('.documentText img, body.template-view #content-core img').each(function() {
        var data = $(this).attr('alt');

        $(this)
            .wrap("<span class='auto-image-caption'></span>")
            .parent('.auto-image-caption')
            .attr('data-alt', data)
        ;
    });

});
