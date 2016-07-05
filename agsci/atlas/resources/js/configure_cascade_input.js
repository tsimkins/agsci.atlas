// When the document is ready, configure cascading between widgets.
$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#formfield-form-widgets-IAtlasMetadata-atlas_category_level_1');
        var category_level_2 = $('#formfield-form-widgets-IAtlasMetadata-atlas_category_level_2');
        var category_level_3 = $('#formfield-form-widgets-IAtlasMetadata-atlas_category_level_3');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2).cascadesTo(category_level_3);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);

$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#formfield-form-widgets-IAtlasMetadata-atlas_state_extension_team');
        var category_level_2 = $('#formfield-form-widgets-IAtlasMetadata-atlas_program_team');
        var category_level_3 = $('#formfield-form-widgets-IAtlasMetadata-atlas_curriculum');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2).cascadesTo(category_level_3);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);