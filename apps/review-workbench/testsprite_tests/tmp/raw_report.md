
# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** review-workbench
- **Date:** 2026-03-23
- **Prepared by:** TestSprite AI Team

---

## 2️⃣ Requirement Validation Summary

#### Test TC001 Portfolio dashboard loads with job table, status badges, and deadline sidebar
- **Test Code:** [TC001_Portfolio_dashboard_loads_with_job_table_status_badges_and_deadline_sidebar.py](./TC001_Portfolio_dashboard_loads_with_job_table_status_badges_and_deadline_sidebar.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/03fd68bb-b722-45d4-af01-038021673cf5
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC002 Navigate from a job row to the Job Flow Inspector
- **Test Code:** [TC002_Navigate_from_a_job_row_to_the_Job_Flow_Inspector.py](./TC002_Navigate_from_a_job_row_to_the_Job_Flow_Inspector.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/600d6ece-4de4-42ae-bcc8-f82322f9c01a
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC005 Load Job Flow Inspector and render pipeline timeline with stage status dots
- **Test Code:** [TC005_Load_Job_Flow_Inspector_and_render_pipeline_timeline_with_stage_status_dots.py](./TC005_Load_Job_Flow_Inspector_and_render_pipeline_timeline_with_stage_status_dots.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/d7e6091e-fd51-44c5-92e1-511e5aa7439c
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC006 Pending HITL stage is visually indicated on the timeline
- **Test Code:** [TC006_Pending_HITL_stage_is_visually_indicated_on_the_timeline.py](./TC006_Pending_HITL_stage_is_visually_indicated_on_the_timeline.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/3601fe97-e076-4fdf-b094-095cd2e2ec21
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC007 GO TO REVIEW CTA navigates to Match review stage
- **Test Code:** [TC007_GO_TO_REVIEW_CTA_navigates_to_Match_review_stage.py](./TC007_GO_TO_REVIEW_CTA_navigates_to_Match_review_stage.py)
- **Test Error:** TEST FAILURE

ASSERTIONS:
- Evidence element not found on /jobs/tu_berlin/201397/match — expected UI element 'Evidence' is missing.
- Extracted page content does not contain the word 'Evidence' or any nearby labels indicating an evidence section.
- Review stage navigation succeeded (URL contains '/jobs/tu_berlin/201397/match' and 'Match' text visible) but the required 'Evidence' feature is not present.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/8c9d1fe1-c683-4169-a39c-d031c1b05423
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC008 Timeline error state shows an error banner when timeline fails
- **Test Code:** [TC008_Timeline_error_state_shows_an_error_banner_when_timeline_fails.py](./TC008_Timeline_error_state_shows_an_error_banner_when_timeline_fails.py)
- **Test Error:** TEST FAILURE

ASSERTIONS:
- 'Unable to load timeline' error text not found on the job page.
- 'Retry' element or button for reloading the timeline is not present on the job page.
- No explicit 'Error' banner indicating the timeline failed to load is visible on the page.
- The page displays normal timeline content (e.g., 'HUMAN REVIEW REQUIRED — REVIEW_MATCH'), indicating the timeline did not report a load failure state.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/7573a836-bfbc-4cd0-87bb-1d31fdc4441b
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC011 Scrape diagnostics shows metadata and collapsed source preview by default
- **Test Code:** [TC011_Scrape_diagnostics_shows_metadata_and_collapsed_source_preview_by_default.py](./TC011_Scrape_diagnostics_shows_metadata_and_collapsed_source_preview_by_default.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/2dfaccf9-7e41-4047-a266-42b5f8c6d0a2
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC012 Expand source text preview to show full content
- **Test Code:** [TC012_Expand_source_text_preview_to_show_full_content.py](./TC012_Expand_source_text_preview_to_show_full_content.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/472979ba-89a7-496c-92d7-2d5850d173a6
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC013 Advance from scrape to extract stage
- **Test Code:** [TC013_Advance_from_scrape_to_extract_stage.py](./TC013_Advance_from_scrape_to_extract_stage.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/b80a9efc-7b4b-4623-9975-730c6fc5edb3
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC015 Advance is blocked when required source text is unavailable
- **Test Code:** [TC015_Advance_is_blocked_when_required_source_text_is_unavailable.py](./TC015_Advance_is_blocked_when_required_source_text_is_unavailable.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/68f9a2d1-15ae-4086-8b12-12b264333957
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC018 Extract page renders source text pane with line numbers and requirements list
- **Test Code:** [TC018_Extract_page_renders_source_text_pane_with_line_numbers_and_requirements_list.py](./TC018_Extract_page_renders_source_text_pane_with_line_numbers_and_requirements_list.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/491bd626-b789-467e-8b63-3bdee5c1115d
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC019 Clicking a requirement shows its JSON/details in the control panel
- **Test Code:** [TC019_Clicking_a_requirement_shows_its_JSONdetails_in_the_control_panel.py](./TC019_Clicking_a_requirement_shows_its_JSONdetails_in_the_control_panel.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/39a47cae-53ba-44ce-be5b-caf4f469198f
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC021 Match graph renders with nodes and score badges
- **Test Code:** [TC021_Match_graph_renders_with_nodes_and_score_badges.py](./TC021_Match_graph_renders_with_nodes_and_score_badges.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/e4f9f5eb-0d9e-4808-ac0b-674f0662d194
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC022 Clicking a graph node shows JSON in the control panel
- **Test Code:** [TC022_Clicking_a_graph_node_shows_JSON_in_the_control_panel.py](./TC022_Clicking_a_graph_node_shows_JSON_in_the_control_panel.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/2b5299a6-08f1-460c-ae97-4148805c7191
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC025 Load Generate Documents and verify the three document tabs are visible
- **Test Code:** [TC025_Load_Generate_Documents_and_verify_the_three_document_tabs_are_visible.py](./TC025_Load_Generate_Documents_and_verify_the_three_document_tabs_are_visible.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/61b64853-30b3-466e-bc58-4cb0dd2cb861
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC026 Switch between document tabs and confirm content changes
- **Test Code:** [TC026_Switch_between_document_tabs_and_confirm_content_changes.py](./TC026_Switch_between_document_tabs_and_confirm_content_changes.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/63efcc6f-90fd-4a95-a3c6-1273ec8a6752
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC027 Edit markdown and see dirty state indicator appear
- **Test Code:** [TC027_Edit_markdown_and_see_dirty_state_indicator_appear.py](./TC027_Edit_markdown_and_see_dirty_state_indicator_appear.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/d9f1130f-7f91-4519-b791-9bbb43d4f7e5
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC029 Submit regeneration request and see success message
- **Test Code:** [TC029_Submit_regeneration_request_and_see_success_message.py](./TC029_Submit_regeneration_request_and_see_success_message.py)
- **Test Error:** TEST FAILURE

ASSERTIONS:
- No visible success confirmation message (e.g., toast or 'Regeneration requested') displayed after submitting the regeneration modal.
- Regeneration modal submission occurred (textarea contains 'Please regenerate with stronger impact and clearer structure.' and CONFIRM REGEN was clicked) but no success indicator was displayed.
- Searching the page for common success keywords ('success', 'Regeneration requested') returned no matches.
- No new toast or confirmation elements appeared within the observed wait period after submission.
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/4f0c60d7-cb0e-4098-b6ba-7c50e273c3a4
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC031 Package and Deployment page renders mission summary, checklist, and package files
- **Test Code:** [TC031_Package_and_Deployment_page_renders_mission_summary_checklist_and_package_files.py](./TC031_Package_and_Deployment_page_renders_mission_summary_checklist_and_package_files.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/71149dc4-2732-49de-9337-9307bf6b7e45
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC032 Mark as deployed happy path navigates back to dashboard
- **Test Code:** [TC032_Mark_as_deployed_happy_path_navigates_back_to_dashboard.py](./TC032_Mark_as_deployed_happy_path_navigates_back_to_dashboard.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/b08b9872-fdee-4a87-8187-723ac3cd70e4
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC033 Deployment confirmation shows mock/UI-only simulation messaging
- **Test Code:** [TC033_Deployment_confirmation_shows_mockUI_only_simulation_messaging.py](./TC033_Deployment_confirmation_shows_mockUI_only_simulation_messaging.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/ec23b316-5c0b-4278-a009-3ac01a3a1c61
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC038 Open Data Explorer and verify split-pane layout is visible
- **Test Code:** [TC038_Open_Data_Explorer_and_verify_split_pane_layout_is_visible.py](./TC038_Open_Data_Explorer_and_verify_split_pane_layout_is_visible.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/aeb52461-b1c6-4402-b4b0-2871064078f1
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC039 Expand a folder in the tree to reveal child items
- **Test Code:** [TC039_Expand_a_folder_in_the_tree_to_reveal_child_items.py](./TC039_Expand_a_folder_in_the_tree_to_reveal_child_items.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/3e00b576-7974-40de-ba12-de0521cf1d9d
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC041 Preview a JSON file and verify CodeMirror JSON preview is shown
- **Test Code:** [TC041_Preview_a_JSON_file_and_verify_CodeMirror_JSON_preview_is_shown.py](./TC041_Preview_a_JSON_file_and_verify_CodeMirror_JSON_preview_is_shown.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/90b95d1d-1642-4f70-82d8-12f754c0c582
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC043 Use breadcrumb navigation to return to a parent directory
- **Test Code:** [TC043_Use_breadcrumb_navigation_to_return_to_a_parent_directory.py](./TC043_Use_breadcrumb_navigation_to_return_to_a_parent_directory.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/40a0889d-fdb1-40f8-b8dd-ef9a2cd97725
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC044 Unsupported file preview shows a 'Preview not available' placeholder
- **Test Code:** [TC044_Unsupported_file_preview_shows_a_Preview_not_available_placeholder.py](./TC044_Unsupported_file_preview_shows_a_Preview_not_available_placeholder.py)
- **Test Error:** TEST FAILURE

ASSERTIONS:
- Directory is empty; no files available to select for preview
- No interactive elements found on the page (0 interactive elements), preventing clicks and file selection
- Explorer UI shows placeholder 'SELECT_A_FILE_OR_FOLDER' and 'DIRECTORY_EMPTY' indicating no testable files
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/ee57b05d-dfb5-4801-ad0b-d1454f4d7482
- **Status:** ❌ Failed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC046 Open Base CV Editor and verify the CV graph canvas loads with nodes
- **Test Code:** [TC046_Open_Base_CV_Editor_and_verify_the_CV_graph_canvas_loads_with_nodes.py](./TC046_Open_Base_CV_Editor_and_verify_the_CV_graph_canvas_loads_with_nodes.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/e9e055d1-03aa-4301-b8c9-dcbd01bf6824
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC047 Open NodeInspector by selecting an entry node
- **Test Code:** [TC047_Open_NodeInspector_by_selecting_an_entry_node.py](./TC047_Open_NodeInspector_by_selecting_an_entry_node.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/27bd11bd-da74-4514-a816-e12b647e11c3
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC003 Dashboard table shows multiple job statuses
- **Test Code:** [TC003_Dashboard_table_shows_multiple_job_statuses.py](./TC003_Dashboard_table_shows_multiple_job_statuses.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/d4245d1e-8770-4e04-99dd-882345853df3
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---

#### Test TC004 Deadline sidebar renders upcoming items and remains visible after scrolling the job list
- **Test Code:** [TC004_Deadline_sidebar_renders_upcoming_items_and_remains_visible_after_scrolling_the_job_list.py](./TC004_Deadline_sidebar_renders_upcoming_items_and_remains_visible_after_scrolling_the_job_list.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/9fb78310-448b-480e-a912-51e885206f02/5c9e5080-376b-480f-b2f8-c437e4679d68
- **Status:** ✅ Passed
- **Analysis / Findings:** {{TODO:AI_ANALYSIS}}.
---


## 3️⃣ Coverage & Matching Metrics

- **86.67** of tests passed

| Requirement        | Total Tests | ✅ Passed | ❌ Failed  |
|--------------------|-------------|-----------|------------|
| ...                | ...         | ...       | ...        |
---


## 4️⃣ Key Gaps / Risks
{AI_GNERATED_KET_GAPS_AND_RISKS}
---