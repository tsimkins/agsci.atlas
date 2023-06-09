// When the document is ready, configure cascading between widgets.

// IA Categories (Products)
$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_1');
        var category_level_2 = $('#form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_2');
        var category_level_3 = $('#form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_3');

        var educational_drivers = $('#form-widgets-IAtlasProductCategoryMetadata-atlas_educational_drivers');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2);
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
        var category_level_1 = $('#form-widgets-IAtlasPersonCategoryMetadata-atlas_category_level_1');
        var category_level_2 = $('#form-widgets-IAtlasPersonCategoryMetadata-atlas_category_level_2');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);

// EPAS (Updated)
$('document').ready(
    function () {

        // Establish the widget parent elements
        var category_level_1 = $('#form-widgets-IAtlasEPASMetadata-epas_unit');
        var category_level_2 = $('#form-widgets-IAtlasEPASMetadata-epas_team');
        var category_level_3 = $('#form-widgets-IAtlasEPASMetadata-epas_topic');

        // Configure cascading to child elements
        category_level_1.cascadesTo(category_level_2).cascadesTo(category_level_3);

        // Starting at the top level run an initial cascade
        category_level_1.cascadeSelections();

    }
);

// Attribute Sets
$('document').ready(
    function () {

        // Grab the Category Level 3 widget
        var category_level_3 = $('#form-widgets-IAtlasProductCategoryMetadata-atlas_category_level_3');

        // If our JSON dict is defined, initiate the child attribute set configuration
        if (typeof category_3_attribute_sets !== 'undefined') {
            category_level_3.initChildAttributeSets(category_3_attribute_sets);
        }

    }
);
