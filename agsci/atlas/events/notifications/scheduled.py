<?xml version="1.0" encoding="UTF-8"?>
<object name="portal_workflow" meta_type="Plone Workflow Tool">

    <property name="title">Contains workflow definitions for your portal</property>

    <object name="product_workflow" meta_type="Workflow" />
    <object name="event_group_workflow" meta_type="Workflow" />
    <object name="publication_workflow" meta_type="Workflow" />
    <object name="online_course_workflow" meta_type="Workflow" />
    <object name="cvent_workflow" meta_type="Workflow" />
    <object name="product_container_workflow" meta_type="Workflow" />
    <object name="person_workflow" meta_type="Workflow" />
    <object name="news_item_workflow" meta_type="Workflow" />
    
    <bindings>

        <!-- Default Workflow -->
        <default>
            <bound-workflow workflow_id="simple_publication_workflow" />
        </default>

        <!-- Article -->
        <type type_id="atlas_article">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <!-- Article Contents -->
        <type type_id="atlas_article_page">
            <bound-workflow workflow_id="" />
        </type>
        <type type_id="atlas_article_slideshow">
            <bound-workflow workflow_id="" />
        </type>
        <type type_id="atlas_article_video">
            <bound-workflow workflow_id="" />
        </type>

        <!-- News Item -->
        <type type_id="atlas_news_item">
            <bound-workflow workflow_id="news_item_workflow" />
        </type>

        <!-- Publication -->
        <type type_id="atlas_publication">
            <bound-workflow workflow_id="publication_workflow" />
        </type>

        <!-- Program -->
        <type type_id="atlas_program">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <!-- Program Link -->
        <type type_id="atlas_program_link">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <!-- Video -->
        <type type_id="atlas_video">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <!-- Curriculum -->
        <type type_id="atlas_curriculum">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <!-- Online Course -->
        <type type_id="atlas_online_course">
            <bound-workflow workflow_id="online_course_workflow" />
        </type>

        <!-- App -->
        <type type_id="atlas_app">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <!-- Smart Sheet -->
        <type type_id="atlas_smart_sheet">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <!-- Event Groups -->
        <type type_id="atlas_webinar_group">
            <bound-workflow workflow_id="event_group_workflow" />
        </type>

        <type type_id="atlas_workshop_group">
            <bound-workflow workflow_id="event_group_workflow" />
        </type>

        <type type_id="atlas_online_course_group">
            <bound-workflow workflow_id="online_course_workflow" />
        </type>

        <type type_id="atlas_conference_group">
            <bound-workflow workflow_id="event_group_workflow" />
        </type>

        <!-- Events -->
        <type type_id="atlas_conference">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <type type_id="atlas_cvent_event">
            <bound-workflow workflow_id="cvent_workflow" />
        </type>

        <type type_id="atlas_workshop">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <type type_id="atlas_webinar">
            <bound-workflow workflow_id="product_workflow" />
        </type>

        <type type_id="atlas_webinar_recording">
            <bound-workflow workflow_id="" />
        </type>

        <type type_id="atlas_webinar_file">
            <bound-workflow workflow_id="" />
        </type>

        <!-- Plone Types -->
        <type type_id="Folder">
            <bound-workflow workflow_id="" />
        </type>

        <type type_id="File">
            <bound-workflow workflow_id="" />
        </type>

        <type type_id="Image">
            <bound-workflow workflow_id="" />
        </type>

        <!-- Categories -->
        <type type_id="atlas_category_level_1">
            <bound-workflow workflow_id="product_container_workflow" />
        </type>

        <type type_id="atlas_category_level_2">
            <bound-workflow workflow_id="product_container_workflow" />
        </type>

        <type type_id="atlas_category_level_3">
            <bound-workflow workflow_id="product_container_workflow" />
        </type>

        <!-- Extension Structure -->
        <type type_id="atlas_program_team">
            <bound-workflow workflow_id="" />
        </type>

        <type type_id="atlas_state_extension_team">
            <bound-workflow workflow_id="" />
        </type>

        <!-- County -->
        <type type_id="atlas_county">
            <bound-workflow workflow_id="one_state_workflow" />
        </type>

        <!-- Directory and Person -->
        <type type_id="directory">
            <bound-workflow workflow_id="" />
        </type>

        <type type_id="person">
            <bound-workflow workflow_id="person_workflow" />
        </type>

    </bindings>
</object>
