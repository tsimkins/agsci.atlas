$('document').ready(
    function () {

    console.log("HELLO IMAGES");

    $('.documentText img').each(function() {
        var data = $(this).attr('alt');
        console.log("HELLO SKUNK " + data);
        $(this)
            .wrap("<span class='auto-image-caption'></span>")
            .parent('.auto-image-caption')
            .attr('data-alt', data)
        ;
    });

});
