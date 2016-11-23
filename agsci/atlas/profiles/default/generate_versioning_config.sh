#!/bin/bash

# This is a silly Bash script that generates repositorytool.xml and diff_tool.xml
# from the types/* files that have the versioning behavior.  It's run manually
# locally within the profiles/default folder, and overwrites those two files.
#
# Because lazy.

# repositorytool.xml
function generate_repositorytool() {
    echo "<?xml version=\"1.0\"?>"
    echo "<repositorytool>"
    echo "    <policymap>"

    for FOO in `grep -i plone.app.versioningbehavior.behaviors.IVersionable types/* | \
                awk -F: '{print $1}' | awk -F/ '{print $2}' | sort | uniq`
    do
        BAR=`echo $FOO  |sed 's/.xml//'`
        echo "        <type name=\"$BAR\">"
        echo "            <policy name=\"at_edit_autoversion\"/>"
        echo "            <policy name=\"version_on_revert\"/>"
        echo "        </type>"
    done

    echo "    </policymap>"
    echo "</repositorytool>"
}

generate_repositorytool > repositorytool.xml

# diff_tool.xml
function generate_diff_tool() {
    echo "<?xml version=\"1.0\"?>"
    echo "<object>"
    echo "  <difftypes>"

    for FOO in `grep -i plone.app.versioningbehavior.behaviors.IVersionable types/* | \
                awk -F: '{print $1}' | awk -F/ '{print $2}' | sort | uniq`
        do
            BAR=`echo $FOO  |sed 's/.xml//'`
            echo "        <type portal_type=\"$BAR\">"
            echo "            <field name=\"any\" difftype=\"Compound Diff for Dexterity types\"/>"
            echo "        </type>"
        done
    echo "  </difftypes>"
    echo "</object>"

}

generate_diff_tool > diff_tool.xml
