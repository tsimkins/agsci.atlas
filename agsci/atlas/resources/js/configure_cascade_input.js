// When the document is ready, configure cascading between widgets.

// IA Categories (Products)
$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#formfield-form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_1');
        var category_level_2 = $('#formfield-form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_2');
        var category_level_3 = $('#formfield-form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_3');

        var educational_drivers = $('#formfield-form-widgets-IAtlasProductCategoryMetadata-atlas_educational_drivers');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2).cascadesTo(category_level_3);
        category_level_2.cascadesTo(educational_drivers);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);

// IA Categories (Person)
$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#formfield-form-widgets-IAtlasPersonCategoryMetadata-atlas_category_level_1');
        var category_level_2 = $('#formfield-form-widgets-IAtlasPersonCategoryMetadata-atlas_category_level_2');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);

// EPAS (Product)
$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#formfield-form-widgets-IAtlasEPASMetadata-atlas_state_extension_team');
        var category_level_2 = $('#formfield-form-widgets-IAtlasEPASMetadata-atlas_program_team');
        var category_level_3 = $('#formfield-form-widgets-IAtlasEPASMetadata-atlas_curriculum');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2).cascadesTo(category_level_3);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);

// EPAS (Person)
$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#formfield-form-widgets-IAtlasPersonEPASMetadata-atlas_state_extension_team');
        var category_level_2 = $('#formfield-form-widgets-IAtlasPersonEPASMetadata-atlas_program_team');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);

// Attribute Sets
$('document').ready(
    function () {

        // Grab the Category Level 3 widget
        var category_level_3 = $('#formfield-form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_3');

        // If our JSON dict is defined, initiate the child attribute set configuration
        if (typeof category_3_attribute_sets !== 'undefined') {
            category_level_3.initChildAttributeSets(category_3_attribute_sets);
        }

    }
);