/* -----------------------------------------------------------------------------
    jQuery methods that are used to manipulate and cascade information between
    cascading select boxes in the Plone multiselect widget.
----------------------------------------------------------------------------- */

// sortChildren(): Within a select list, sort options or optgroups alphabetically by value.
(function( $ ) {
    $.fn.sortChildren = function (s) {

        var items = this.children(s).remove();

        var sorted_items = items.sort(
            function(a, b) {

                // Push disabled options to the bottom
                var a_disabled = ($(a).attr('disabled') == 'disabled');
                var b_disabled = ($(b).attr('disabled') == 'disabled');

                if (b_disabled && ! a_disabled) {
                    return -1;
                }

                // Otherwise, sort by value or label. Value is default.
                var sort_key = 'value';

                // If we're an optgroup, set the `sort_key` to `label`
                if ($(a).prop('tagName') == 'OPTGROUP') {
                    sort_key == 'label';
                }

                var aVal = $(a).attr(sort_key);
                var bVal = $(b).attr(sort_key);

                return (aVal < bVal) ? -1 : (aVal > bVal) ? 1 : 0;
            }
        );

        $(sorted_items).appendTo(this);
    }
}( jQuery ));


// setOptionGroups(): Within a select list, add option groups
(function( $ ) {
    $.fn.setOptionGroups = function () {

        // Sort the child <option> elements
        this.sortChildren('option');

        // If we're the first level, we won't have option groups.  Just return
        // the existing element
        if (! this.getParentField().cascadeFromElement().size() ) {
            return this;
        }

        // Remove all options, and pull them into an array
        var options = this.find('option').remove();

        // Remove all optgroups, and pull them into an array
        var optgroups = this.children('optgroup').remove();

        // Iterate through teach option
        $(options).each(
            function () {

                // Put the '<option>' tag as the `option` variable
                var option = $(this);

                // Assign the 'value' attribute of the option to `val`
                var val = option.attr('value');

                // Find the position of the last delimiter
                var last_delimiter = val.lastIndexOf(':');

                // Split the value into part1 and part 2
                var part1 = val.substr(0,last_delimiter);
                var part2 = val.substr(last_delimiter+1,val.length);

                // Set HTML contents of option to be part 2
                option.html(part2);

                // Iterate through the option groups, and if the data attribute
                // of 'value' matches the `part1` variable, append it and set
                // `found_value` to true.
                var found_value = false;

                optgroups.each(
                    function () {
                        var optgroup = $(this);

                        if (optgroup.data('value') == part1) {
                            optgroup.append(option);
                            found_value = true;
                        }
                    }
                );

                // If we didn't find an optgroup with the specified value, create
                // one, append the option, and append it to optgroups.
                if (! found_value) {
                    var optgroup = $('<optgroup label="' + part1 + '"></optgroup>');

                    // Set the 'value' data attribute of the optgroup to `part1
                    optgroup.data('value', part1);

                    // Append the current <option> element to this optgroup
                    optgroup.append(option);

                    // Append this optgroup to the optgroups array
                    optgroups.push(optgroup);
                }
            }
        );

        // Append option groups to select box if it has children of <option>
        for (var i=0; i<optgroups.length; i++) {

            // Get optgroup element
            var optgroup = $(optgroups[i]);

            // If there are options underneath the optgroup
            if (optgroup.children('option').size()) {

                // Show option group element and removed 'disabled' attribute
                optgroup.show();
                optgroup.removeAttr('disabled');

                // If we don't have any non-disabled children, set disabled
                // attribute, and hide
                if (! optgroup.children('option:not([disabled="disabled"])').size()) {
                    optgroup.attr('disabled', 'disabled');
                    optgroup.hide();
                }

                // Append optgroup to select list
                this.append(optgroup);
            }
        }

        // Sort option groups
        this.sortChildren('optgroup');
        
        // Sort the options inside the option groups
        this.children('optgroup').each(
            function () {
                $(this).sortChildren('option');
            }
        );

        return this

    }
}( jQuery ));


// isValidChild(): Determines if this option value is a valid child of the parent
// "To" box.
(function( $ ) {
    $.fn.isValidChild = function () {

        var val = this.attr('value');
        var selected_values = this.getParentField().cascadeFromElement().getSelectedValues();

        for (var i=0; i<selected_values.length; i++) {
            var v = selected_values[i];

            if (val.indexOf(v + ':') == 0) {
                return true;
            }
        }

        return false;

    }
}( jQuery ));


// getFromSelectBox(): Return the "From" selection element for a widget
(function( $ ) {
    $.fn.getFromSelectBox = function () {

        return this.find('select[id$="-from"]');

    }
}( jQuery ));


// getToSelectBox(): Return the "To" selection element for a widget
(function( $ ) {
    $.fn.getToSelectBox = function () {

        return this.find('select[id$="-to"]');
    }
}( jQuery ));


// getSelectOptionValues(): Given the id of a select box, return a list of strings in that element
(function( $ ) {
    $.fn.getSelectOptionValues = function () {

        var option_values = [];

        this.find('option').each(
            function () {
                option_values.push($(this).attr('value'));
            }
        );

        return option_values;

    }
}( jQuery ));


// getAvailableValues(): Returns the values in the "From" box
(function( $ ) {

    $.fn.getAvailableValues = function () {
        return this.getFromSelectBox().getSelectOptionValues();
    }

}( jQuery ));


// getSelectedValues(): Returns the values in the "To" box
(function( $ ) {
    $.fn.getSelectedValues = function () {
        return this.getToSelectBox().getSelectOptionValues();
    }
}( jQuery ));


// filterAvailableValues(): Hide values in "From" box if the parent box doesn't have them selected.
(function( $ ) {

    $.fn.filterAvailableValues = function() {

        // Get child from and to elements
        var child_element = this.cascadeToElement()

        if (! child_element.size()) {
            return false;
        }

        var child_from = child_element.getFromSelectBox();
        var child_to = child_element.getToSelectBox();

        // Iterate through the option elements in the "To" box and verify that it's
        // a valid child.  If it's not, select it.
        $(child_from).find('option').each(
            function () {

                var val = $(this).val();

                $(this).prop("selected", false);
                $(this).selected = false;

                if ( ! $(this).isValidChild() ) {
                    $(this).attr('disabled', 'disabled');
                }
                else {
                    $(this).removeAttr('disabled');
                }
            }
        );
    }

}( jQuery ));


// filterSelectedValues(): For values that are selected, but do not match the parent selection,
// move them back to the available box.
(function( $ ) {

    $.fn.filterSelectedValues = function () {

        // Get child from and to elements
        var child_element = this.cascadeToElement()

        if (! child_element.size() ) {
            return false;
        }

        var child_from = child_element.getFromSelectBox();
        var child_to = child_element.getToSelectBox();

        // Iterate through the option elements in the "To" box and verify that it's
        // a valid child.  If it's not, select it.
        $(child_to).find('option').each(
            function () {

                var val = $(this).val();

                if ( ! $(this).isValidChild() ) {
                    $(this).prop("selected", true);
                    $(this).selected = true;
                }
                else {
                    $(this).prop("selected", false);
                    $(this).selected = false;
                }
            }
        );

        // If any of the children in the 'to' box are selected, send them back to
        // the "From" box
        if ($(child_to).find('option:selected').size()) {
            to2from($(child_to).getParentTable().attr('id'));
        }

        // Deselect all items in the child "From" box
        $(child_from).find('option').each(
            function () {
                $(this).prop("selected", false);
                $(this).selected = false;
            }
        );
    }

}( jQuery ));


// cascadeSelections(): Called to cascade selections from parents to children
// recursively
(function( $ ) {

    $.fn.cascadeSelections = function () {

        // Filter selected and available values
        this.filterSelectedValues();
        this.filterAvailableValues();

        // Cascade down to child selections if a child exists. Yay, recursion!
        var cascade_to = this.cascadeToElement();

        if (cascade_to.size()) {
            this.cascadeToElement().cascadeSelections() ;
        }

        // Run the routine to hide or show the element based on if it has
        // visible children
        this.toggleElementVisibility();

        // Configure the option groups in the select boxes
        this.getFromSelectBox().setOptionGroups()
        this.getToSelectBox().setOptionGroups()
    }

}( jQuery ));


// toggleElementVisibility(): Hides parent element if nothing is available or
// selected. Shows it if there is.
(function( $ ) {
    $.fn.toggleElementVisibility = function () {

        // Show the element first, since a hidden element's children will always
        // be considered invisible.
        this.show();

        if (! this.find('option:not([disabled="disabled"])').size() ) {
            this.hide();
        }

        return this;
    }
}( jQuery ));


// cascadeToElement(): Returns the element that this element will cascade *to*.
(function( $ ) {

    $.fn.cascadeToElement = function() {
        return $('#' + this.data('cascade-to-id'));
    };

}( jQuery ));


// cascadeFromElement(): Returns the element that this element will cascade *from*.
(function( $ ) {

    $.fn.cascadeFromElement = function() {
        return $('#' + this.data('cascade-from-id'));
    };

}( jQuery ));


// getParentField(): Returns the parent ".field" element that the element
// is inside.
(function( $ ) {
    $.fn.getParentField = function () {

        return this.closest('.field');
    }
}( jQuery ));


// getParentTable(): Returns the parent "table" element that the element
// is inside.
(function( $ ) {
    $.fn.getParentTable = function () {

        return this.closest('table');
    }
}( jQuery ));


// initializeWidget(): Apply customizations and overrides to the widget if
// data property of 'initialized' is not set.
(function( $ ) {
    $.fn.initializeWidget = function () {

        // Only initialize if we have not already been initialized
        if (! this.data('initialized')) {

            // Add class of 'cascade-select'
            this.addClass('cascade-select');

            // Remove the up/down buttons from the element
            this.find('[name="upButton"]').remove();
            this.find('[name="downButton"]').remove();

            // Get the from/to buttons
            var from2toButton = this.find('[name="from2toButton"]');
            var to2fromButton = this.find('[name="to2fromButton"]');

            // Remove and override the onclick attributes with an event handler
            from2toButton.removeAttr('onclick');
            to2fromButton.removeAttr('onclick');

            // Bind updated click handler to buttons
            from2toButton.bind('click',
                function () {
                    from2to($(this).getParentTable().attr('id'));
                    $(this).getParentField().cascadeSelections();
                }
            );

            to2fromButton.bind('click',
                function () {
                    to2from($(this).getParentTable().attr('id'));
                    $(this).getParentField().cascadeSelections();
                }
            );

            // Bind double click on 'from' options to be a click on the left
            // arrow button.
            this.getFromSelectBox().bind('dblclick',

                function() {
                    $(this).getParentField().find('[name="from2toButton"]').click();
                }

            );

            // Bind double click on 'to' options to be a click on the right
            // arrow button.
            this.getToSelectBox().bind('dblclick',

                function() {
                    $(this).getParentField().find('[name="to2fromButton"]').click();
                }

            );

            // Set the value of 'initialized' on this element to true
            this.data('initialized', true)
        }

        return this;

    }
}( jQuery ));


// cascadesTo(): Initializes cascading from a parent to a child element.
(function( $ ) {

    $.fn.cascadesTo = function(to_el) {

        var from_id = this.attr('id');
        var to_id = to_el.attr('id');

        // Add a 'cascade-to-id' attribute for the *to* widget
        this.data('cascade-to-id', to_id);

        // Add a 'cascade-from-id' attribute for the *from* widget
        to_el.data('cascade-from-id', from_id);

        // Initialize both to and from widgets
        this.initializeWidget();
        to_el.initializeWidget();

        // Returns the cascaded *to* element, so we can chain the cascades
        return to_el;

    };

}( jQuery ));

/*
--------------------------------------------------------------------------------
  From cascading to determining visibility of child attributesets
--------------------------------------------------------------------------------
*/

// initChildAttributeSets(): Initializes the showing or hiding of child attribute sets.
(function( $ ) {

    $.fn.initChildAttributeSets = function(c) {

        this.data('child-attribute-config', c);

        // Get the from/to buttons
        var from2toButton = this.find('[name="from2toButton"]');
        var to2fromButton = this.find('[name="to2fromButton"]');

        // Remove and override the onclick attributes with an event handler
        from2toButton.removeAttr('onclick');
        to2fromButton.removeAttr('onclick');

        // Bind updated click handler to buttons
        from2toButton.bind('click',
            function () {
                $(this).getParentField().updateChildAttributeSets();
            }
        );

        to2fromButton.bind('click',
            function () {
                $(this).getParentField().updateChildAttributeSets();
            }
        );

        this.updateChildAttributeSets();

        return this;

    };

}( jQuery ));

// updateChildAttributeSets(): Does showing or hiding of child attribute sets.
(function( $ ) {

    $.fn.updateChildAttributeSets = function() {

        // Get the "To" box from this widget
        var to_select = this.getToSelectBox();

        // Get the values selected
        var selected_values = to_select.getSelectOptionValues();

        // Get the config dictionary
        var c = this.data('child-attribute-config');

        // Initialize the "All" and "Show" lists
        var all_children = [];
        var show_children = [];

        // Go through the config, and append all child attribute sets 
        // (uniquely) to all_children
        for (var i in c) {
            var child_fields = c[i];

            if (child_fields) {

                for (var j=0; j<child_fields.length; j++) {
                    var cf = child_fields[j];
    
                    if (all_children.indexOf(cf) < 0) {
                        all_children.push(cf);
                    }
                }
            }
        }

        // Go through the selected values and lookup up the child attribute set
        // fields from the config, and append (uniquely) to show_children
        for (var i=0; i<selected_values.length; i++) {
            var v = selected_values[i]
            var child_fields = c[v];
            if (child_fields) {
                for (var j=0; j<child_fields.length; j++) {
                    var cf = child_fields[j];
    
                    if (show_children.indexOf(cf) < 0) {
                        show_children.push(cf);
                    }
                }
            }
        }

        // Itereate through all of the potential children         
        for (var i in all_children) {

            // Get the id selector for the child
            var child_id = all_children[i];
            
            var child_obj = $(child_id);

            // If the child isn't in the "Show" list
            if (show_children.indexOf(child_id) < 0) {

                // Get child "To" select box
                var child_to_select = child_obj.getToSelectBox();
                
                // Get child "From" select box
                var child_from_select = child_obj.getFromSelectBox();

                // If the child "To" has any options selected
                
                if (child_to_select.children('option').size()) {
                    
                    // Select all of the "To" options
                    child_to_select.children('option').each(
                        function () {
                            $(this).prop("selected", true);
                            $(this).selected = true;
                        }
                    );

                    // Click the left arrow to send them back
                    child_obj.find('[name="to2fromButton"]').click();
                }

                // Delect all of the child "From" options
                child_from_select.children('option').each(
                    function () {
                        $(this).prop("selected", false);
                        $(this).selected = false;
                    }
                );

                // Hide the child object
                child_obj.hide();
            }
            else {
                // Show the child object
                child_obj.show();
            }
        }

        return this;

    };

}( jQuery ));