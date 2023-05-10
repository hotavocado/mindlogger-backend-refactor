from apps.shared.test import BaseTest
from infrastructure.database import rollback


class TestAppletActivityItems(BaseTest):
    fixtures = [
        "users/fixtures/users.json",
        "themes/fixtures/themes.json",
        "folders/fixtures/folders.json",
        "applets/fixtures/applets.json",
        "applets/fixtures/applet_histories.json",
        "applets/fixtures/applet_user_accesses.json",
        "activities/fixtures/activities.json",
        "activities/fixtures/activity_items.json",
        "activity_flows/fixtures/activity_flows.json",
        "activity_flows/fixtures/activity_flow_items.json",
    ]

    login_url = "/auth/login"
    applet_list_url = "applets"
    applet_create_url = "workspaces/{owner_id}/applets"
    applet_detail_url = f"{applet_list_url}/{{pk}}"

    @rollback
    async def test_creating_applet_with_activity_items(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        create_data = dict(
            password="Test1234!",
            display_name="User daily behave",
            description=dict(
                en="Understand users behave",
                fr="Comprendre le comportement des utilisateurs",
            ),
            about=dict(
                en="Understand users behave",
                fr="Comprendre le comportement des utilisateurs",
            ),
            activities=[
                dict(
                    name="Morning activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bfe",
                    description=dict(
                        en="Understand morning feelings.",
                        fr="Understand morning feelings.",
                    ),
                    items=[
                        dict(
                            name="activity_item_text",
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            response_type="text",
                            response_values=None,
                            config=dict(
                                max_response_length=200,
                                correct_answer_required=False,
                                correct_answer=None,
                                numerical_response_required=False,
                                response_data_identifier=False,
                                response_required=False,
                                remove_back_button=False,
                                skippable_item=True,
                            ),
                        ),
                        dict(
                            name="activity_item_message",
                            question={"en": "What is your name?"},
                            response_type="message",
                            response_values=None,
                            config=dict(
                                remove_back_button=False,
                                timer=1,
                            ),
                        ),
                        dict(
                            name="activity_item_number_selection",
                            question={"en": "What is your name?"},
                            response_type="numberSelect",
                            response_values=dict(
                                min_value=0,
                                max_value=10,
                            ),
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                            ),
                        ),
                        dict(
                            name="activity_item_time_range",
                            question={"en": "What is your name?"},
                            response_type="timeRange",
                            response_values=None,
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                                timer=1,
                            ),
                        ),
                        dict(
                            name="activity_item_time_range_2",
                            question={"en": "What is your name?"},
                            response_type="time",
                            response_values=None,
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                                timer=1,
                            ),
                        ),
                        dict(
                            name="activity_item_geolocation",
                            question={"en": "What is your name?"},
                            response_type="geolocation",
                            response_values=None,
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                            ),
                        ),
                        dict(
                            name="activity_item_photo",
                            question={"en": "What is your name?"},
                            response_type="photo",
                            response_values=None,
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                            ),
                        ),
                        dict(
                            name="activity_item_video",
                            question={"en": "What is your name?"},
                            response_type="video",
                            response_values=None,
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                            ),
                        ),
                        dict(
                            name="activity_item_date",
                            question={"en": "What is your name?"},
                            response_type="date",
                            response_values=None,
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                            ),
                        ),
                        dict(
                            name="activity_item_drawing",
                            question={"en": "What is your name?"},
                            response_type="drawing",
                            response_values=dict(
                                drawing_background="https://www.w3schools.com/css/img_5terre_wide.jpg",  # noqa E501
                                drawing_example="https://www.w3schools.com/css/img_5terre_wide.jpg",  # noqa E501
                            ),
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                                timer=1,
                                remove_undo_button=False,
                                navigation_to_top=False,
                            ),
                        ),
                        dict(
                            name="activity_item_audio",
                            question={"en": "What is your name?"},
                            response_type="audio",
                            response_values=dict(max_duration=200),
                            config=dict(
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                remove_back_button=False,
                                skippable_item=False,
                                timer=1,
                            ),
                        ),
                        dict(
                            name="activity_item_audioplayer",
                            question={"en": "What is your name?"},
                            response_type="audioPlayer",
                            response_values=dict(
                                file="https://www.w3schools.com/html/horse.mp3",  # noqa E501
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=False,
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                                play_once=False,
                            ),
                        ),
                        dict(
                            name="activity_item_sliderrows",
                            question={"en": "What is your name?"},
                            response_type="sliderRows",
                            response_values=dict(
                                rows=[
                                    {
                                        "label": "label1",
                                        "min_label": "min_label1",
                                        "max_label": "max_label1",
                                        "min_value": 0,
                                        "max_value": 10,
                                        "min_image": None,
                                        "max_image": None,
                                        "score": None,
                                    }
                                ]
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=False,
                                add_scores=False,
                                set_alerts=False,
                                timer=1,
                            ),
                        ),
                        dict(
                            name="activity_item_multiselectionrows",
                            question={"en": "What is your name?"},
                            response_type="multiSelectRows",
                            response_values=dict(
                                rows=[
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9df1",  # noqa E501
                                        "row_name": "row1",
                                        "row_image": None,
                                        "tooltip": None,
                                    },
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9df2",  # noqa E501
                                        "row_name": "row2",
                                        "row_image": None,
                                        "tooltip": None,
                                    },
                                ],
                                options=[
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9de1",  # noqa E501
                                        "text": "option1",
                                        "image": None,
                                        "tooltip": None,
                                    },
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9de2",  # noqa E501
                                        "text": "option2",
                                        "image": None,
                                        "tooltip": None,
                                    },
                                ],
                                data_matrix=[
                                    {
                                        "row_id": "17e69155-22cd-4484-8a49-364779ea9df1",  # noqa E501
                                        "options": [
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de1",  # noqa E501
                                                "score": 1,
                                                "alert": None,
                                            },
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de2",  # noqa E501
                                                "score": 2,
                                                "alert": None,
                                            },
                                        ],
                                    },
                                    {
                                        "row_id": "17e69155-22cd-4484-8a49-364779ea9df2",  # noqa E501
                                        "options": [
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de1",  # noqa E501
                                                "score": 3,
                                                "alert": None,
                                            },
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de2",  # noqa E501
                                                "score": 4,
                                                "alert": None,
                                            },
                                        ],
                                    },
                                ],
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=False,
                                add_scores=False,
                                set_alerts=False,
                                timer=1,
                                add_tooltip=False,
                            ),
                        ),
                        dict(
                            name="activity_item_singleselectionrows",
                            question={"en": "What is your name?"},
                            response_type="singleSelectRows",
                            response_values=dict(
                                rows=[
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9df1",  # noqa E501
                                        "row_name": "row1",
                                        "row_image": None,
                                        "tooltip": None,
                                    },
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9df2",  # noqa E501
                                        "row_name": "row2",
                                        "row_image": None,
                                        "tooltip": None,
                                    },
                                ],
                                options=[
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9de1",  # noqa E501
                                        "text": "option1",
                                        "image": None,
                                        "tooltip": None,
                                    },
                                    {
                                        "id": "17e69155-22cd-4484-8a49-364779ea9de2",  # noqa E501
                                        "text": "option2",
                                        "image": None,
                                        "tooltip": None,
                                    },
                                ],
                                data_matrix=[
                                    {
                                        "row_id": "17e69155-22cd-4484-8a49-364779ea9df1",  # noqa E501
                                        "options": [
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de1",  # noqa E501
                                                "score": 1,
                                                "alert": None,
                                            },
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de2",  # noqa E501
                                                "score": 2,
                                                "alert": None,
                                            },
                                        ],
                                    },
                                    {
                                        "row_id": "17e69155-22cd-4484-8a49-364779ea9df2",  # noqa E501
                                        "options": [
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de1",  # noqa E501
                                                "score": 3,
                                                "alert": None,
                                            },
                                            {
                                                "option_id": "17e69155-22cd-4484-8a49-364779ea9de2",  # noqa E501
                                                "score": 4,
                                                "alert": None,
                                            },
                                        ],
                                    },
                                ],
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=False,
                                add_scores=False,
                                set_alerts=False,
                                timer=1,
                                add_tooltip=False,
                            ),
                        ),
                        dict(
                            name="activity_item_singleselect",
                            question={"en": "What is your name?"},
                            response_type="singleSelect",
                            response_values=dict(
                                palette_name="palette1",
                                options=[
                                    {"text": "option1"},
                                    {"text": "option2"},
                                ],
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=False,
                                add_scores=False,
                                set_alerts=False,
                                timer=1,
                                add_tooltip=False,
                                set_palette=False,
                                randomize_options=False,
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                            ),
                        ),
                        dict(
                            name="activity_item_multiselect",
                            question={"en": "What is your name?"},
                            response_type="multiSelect",
                            response_values=dict(
                                palette_name="palette1",
                                options=[
                                    {"text": "option1"},
                                    {"text": "option2"},
                                ],
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=False,
                                add_scores=False,
                                set_alerts=False,
                                timer=1,
                                add_tooltip=False,
                                set_palette=False,
                                randomize_options=False,
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                            ),
                        ),
                        dict(
                            name="activity_item_slideritem",
                            question={"en": "What is your name?"},
                            response_type="slider",
                            response_values=dict(
                                min_value=0,
                                max_value=10,
                                min_label="min_label",
                                max_label="max_label",
                                min_image=None,
                                max_image=None,
                                scores=None,
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=False,
                                add_scores=False,
                                set_alerts=False,
                                timer=1,
                                show_tick_labels=False,
                                show_tick_marks=False,
                                continuous_slider=False,
                                additional_response_option={
                                    "text_input_option": False,
                                    "text_input_required": False,
                                },
                            ),
                        ),
                    ],
                ),
            ],
            activity_flows=[
                dict(
                    name="Morning questionnaire",
                    description=dict(
                        en="Understand how was the morning",
                        fr="Understand how was the morning",
                    ),
                    items=[
                        dict(
                            activity_key="577dbbda-3afc-"
                            "4962-842b-8d8d11588bfe"
                        )
                    ],
                )
            ],
        )
        response = await self.client.post(
            self.applet_create_url.format(
                owner_id="7484f34a-3acc-4ee6-8a94-fd7299502fa1"
            ),
            data=create_data,
        )
        assert response.status_code == 201, response.json()

        response = await self.client.get(
            self.applet_detail_url.format(pk=response.json()["result"]["id"])
        )
        assert response.status_code == 200