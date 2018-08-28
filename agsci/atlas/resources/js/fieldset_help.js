/* -----------------------------------------------------------------------------
    jQuery methods for adding help text and breaking fieldsets into sections
----------------------------------------------------------------------------- */

$('document').ready(
    function () {

        console.log("Starting fieldset_help");

        // If our JSON dict is defined, initiate the child attribute set configuration
        if (typeof fieldset_help !== 'undefined') {
            console.log("Found fieldset_help");
            
            for (var i in fieldset_help) {
                var j = fieldset_help[i];
                
                console.log(j);

                selector = j['selector'];
                heading = j['heading'];
                description = j['description'];
                
                var fieldset = $(selector);

                $('<h2>' + heading + '</h2>').insertBefore(fieldset);
                
                if (description) {

                    for (_i in description) {

                        $('<p>' + description[_i] + '</p>').insertBefore(fieldset);

                    }
                }
                        
                console.log(selector);
            }
        }

    }
);
