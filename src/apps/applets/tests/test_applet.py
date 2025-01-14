import asyncio
import collections
import http
import json
import uuid
from copy import deepcopy

from apps.activities import errors as activity_errors
from apps.shared.test import BaseTest
from apps.workspaces.errors import AppletCreationAccessDenied
from config import settings
from infrastructure.utility import FCMNotificationTest


class TestApplet(BaseTest):
    fixtures = [
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
    applet_duplicate_url = f"{applet_detail_url}/duplicate"
    applet_report_config_url = f"{applet_detail_url}/report_configuration"
    activity_report_config_url = f"{applet_detail_url}/activities/{{activity_id}}/report_configuration"
    flow_report_config_url = f"{applet_detail_url}/flows/{{flow_id}}/report_configuration"
    applet_publish_url = f"{applet_detail_url}/publish"
    applet_conceal_url = f"{applet_detail_url}/conceal"
    applet_set_encryption_url = f"{applet_detail_url}/encryption"
    applet_unique_name_url = f"{applet_list_url}/unique_name"
    histories_url = f"{applet_detail_url}/versions"
    history_url = f"{applet_detail_url}/versions/{{version}}"
    history_changes_url = f"{applet_detail_url}/versions/{{version}}/changes"
    applet_base_info_url = f"{applet_detail_url}/base_info"
    access_link_url = f"{applet_detail_url}/access_link"

    public_applet_detail_url = "/public/applets/{key}"
    public_applet_base_info_url = f"{public_applet_detail_url}/base_info"

    async def test_creating_applet(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        create_data = {
            "displayName": "7ee3617f-fe7f-49bc-8e0c-da6730a2d1cd",
            "encryption": {
                "publicKey": "publicKey",
                "prime": "privateKey",
                "base": "[2]",
                "accountId": str(tom.id),
            },
            "description": {"en": "Central granddaughter unfortunate"},
            "about": {"en": "channels indexing noisily"},
            "activities": [
                {
                    "items": [
                        {
                            "name": "AT_single_select",
                            "question": {"en": "How do you feel today?"},
                            "config": {
                                "removeBackButton": True,
                                "skippableItem": True,
                                "randomizeOptions": True,
                                "addScores": True,
                                "setAlerts": True,
                                "addTooltip": True,
                                "setPalette": True,
                                "additionalResponseOption": {
                                    "textInputOption": True,
                                    "textInputRequired": True,
                                },
                            },
                            "responseValues": {
                                "options": [
                                    {
                                        "text": "very bad",
                                        "isHidden": False,
                                        "score": 1,
                                        "image": "image.jpg",
                                        "tooltip": "backing",
                                        "color": "#123",
                                        "value": 0,
                                    },
                                    {
                                        "text": "bad",
                                        "isHidden": False,
                                        "score": 20,
                                        "image": "image.jpg",
                                        "tooltip": "Generic",
                                        "color": "#456",
                                        "value": 1,
                                    },
                                    {
                                        "text": "normally",
                                        "isHidden": False,
                                        "score": 30,
                                        "image": "image.jpg",
                                        "tooltip": "Gasoline",
                                        "color": "#789",
                                        "value": 2,
                                    },
                                    {
                                        "text": "perfect",
                                        "isHidden": False,
                                        "score": 100,
                                        "image": "image.jpg",
                                        "tooltip": "payment",
                                        "color": "#234",
                                        "value": 3,
                                    },
                                ]
                            },
                            "responseType": "singleSelect",
                        },
                        {
                            "name": "AT_multi_select",
                            "question": {"en": "How do you feel today?"},
                            "config": {
                                "removeBackButton": True,
                                "skippableItem": True,
                                "randomizeOptions": True,
                                "addScores": True,
                                "setAlerts": True,
                                "addTooltip": True,
                                "setPalette": True,
                                "additionalResponseOption": {
                                    "textInputOption": True,
                                    "textInputRequired": True,
                                },
                            },
                            "responseValues": {
                                "options": [
                                    {
                                        "text": "very bad",
                                        "isHidden": False,
                                        "score": 30,
                                        "image": "image.jpg",
                                        "tooltip": "Music",
                                        "color": "#567",
                                        "value": 0,
                                    },
                                    {
                                        "text": "bad",
                                        "isHidden": False,
                                        "score": 1,
                                        "image": "image.jpg",
                                        "tooltip": "East",
                                        "color": "#876",
                                        "value": 1,
                                    },
                                    {
                                        "text": "normally",
                                        "isHidden": False,
                                        "score": 20,
                                        "image": "image.jpg",
                                        "tooltip": "Sodium",
                                        "color": "#923",
                                        "value": 2,
                                    },
                                    {
                                        "text": "perfect",
                                        "isHidden": False,
                                        "score": 100,
                                        "image": "image.jpg",
                                        "tooltip": "Electronics",
                                        "color": "#567",
                                        "value": 3,
                                    },
                                ]
                            },
                            "responseType": "multiSelect",
                        },
                        {
                            "name": "AT_slider",
                            "question": {"en": "How do you feel today?"},
                            "responseType": "slider",
                            "config": {
                                "removeBackButton": True,
                                "skippableItem": True,
                                "addScores": True,
                                "setAlerts": True,
                                "showTickMarks": True,
                                "showTickLabels": True,
                                "continuousSlider": True,
                                "additionalResponseOption": {
                                    "textInputOption": True,
                                    "textInputRequired": True,
                                },
                            },
                            "responseValues": {
                                "minLabel": "very bad",
                                "maxLabel": "extremely good",
                                "minValue": 0,
                                "maxValue": 10,
                                "minImage": "image.jpg",
                                "maxImage": "image.jpg",
                                "scores": [
                                    0,
                                    10,
                                    20,
                                    30,
                                    40,
                                    50,
                                    60,
                                    70,
                                    80,
                                    90,
                                    100,
                                ],
                            },
                        },
                        {
                            "name": "AT_text",
                            "question": {"en": "How do you feel today?"},
                            "config": {
                                "removeBackButton": True,
                                "skippableItem": True,
                                "maxResponseLength": 50,
                                "correctAnswerRequired": True,
                                "correctAnswer": "perfect",
                                "numericalResponseRequired": True,
                                "responseDataIdentifier": True,
                                "responseRequired": True,
                                "isIdentifier": True,
                            },
                            "responseValues": None,
                            "responseType": "text",
                        },
                    ],
                    "name": "white",
                    "key": "19a78ace-5fe5-4a98-8c66-454f973f7f9a",
                    "isHidden": False,
                    "description": {"en": "Recumbent hacking Steel"},
                    "showAllAtOnce": True,
                    "isSkippable": True,
                    "responseIsEditable": True,
                    "isReviewable": True,
                    "image": "image.jpg",
                    "splashScreen": "image.jpg",
                    "reportIncludedItemName": "AT_single_select",
                }
            ],
            "activityFlows": [
                {
                    "name": "Metal",
                    "description": {"en": "East Coupe Northeast"},
                    "items": [{"activityKey": "19a78ace-5fe5-4a98-8c66-454f973f7f9a"}],
                    "reportIncludedActivityName": "white",
                    "reportIncludedItemName": "AT_single_select",
                    "isHidden": False,
                }
            ],
        }
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=create_data,
        )
        assert response.status_code == http.HTTPStatus.CREATED, response.json()

        response = await client.get(self.applet_detail_url.format(pk=response.json()["result"]["id"]))
        assert response.status_code == http.HTTPStatus.OK

    async def test_creating_applet_failed_by_duplicate_activity_name(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        create_data = dict(
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
                    name="AAA",
                    key="577dbbda-3afc-4962-842b-8d8d11588bfe",
                    description=dict(
                        en="Understand morning feelings.",
                        fr="Understand morning feelings.",
                    ),
                    items=[
                        dict(
                            name="morning_activity_item",
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            response_type="text",
                            response_values=None,
                            is_hidden=True,
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
                            name="morning_activity_item_2",
                            question=dict(
                                en="How had you woke?",
                                fr="How had you woke?",
                            ),
                            response_type="slider",
                            response_values=dict(
                                min_label="Not at all",
                                max_label="Very much",
                                min_value=1,
                                max_value=5,
                                min_image=None,
                                max_image=None,
                                scores=None,
                            ),
                            config=dict(
                                add_scores=False,
                                set_alerts=False,
                                show_tick_marks=False,
                                show_tick_labels=False,
                                continuous_slider=False,
                                timer=None,
                                remove_back_button=False,
                                skippable_item=True,
                                additional_response_option=dict(
                                    text_input_option=False,
                                    text_input_required=False,
                                ),
                            ),
                        ),
                    ],
                ),
                dict(
                    name="AAA",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            name="evening_activity_item",
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            response_type="singleSelect",
                            response_values=dict(
                                paletteName="default",
                                options=[
                                    dict(
                                        id="41dfea7e-4496-42b3-ab24-3dd7cce71312",
                                        text="Very well",
                                        image=None,
                                        score=None,
                                        tooltip=None,
                                        is_hidden=False,
                                        color=None,
                                    ),
                                    dict(
                                        id="41dfea7e-4496-42b3-ab24-3dd7cce71313",
                                        text="Well",
                                        image=None,
                                        score=None,
                                        tooltip=None,
                                        is_hidden=False,
                                        color=None,
                                    ),
                                ],
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=True,
                                randomize_options=False,
                                timer=None,
                                add_scores=False,
                                set_alerts=False,
                                add_tooltip=False,
                                set_palette=False,
                                additional_response_option=dict(
                                    text_input_option=False,
                                    text_input_required=False,
                                ),
                            ),
                        ),
                        dict(
                            name="evening_activity_item",
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            response_type="multiSelect",
                            response_values=dict(
                                paletteName=None,
                                options=[
                                    dict(
                                        id="41dfea7e-4496-42b3-ab24-3dd7cce71312",
                                        text="Very well",
                                        image=None,
                                        score=None,
                                        tooltip=None,
                                        is_hidden=False,
                                        color=None,
                                    ),
                                    dict(
                                        id="41dfea7e-4496-42b3-ab24-3dd7cce71313",
                                        text="Well",
                                        image=None,
                                        score=None,
                                        tooltip=None,
                                        is_hidden=False,
                                        color=None,
                                    ),
                                ],
                            ),
                            config=dict(
                                remove_back_button=False,
                                skippable_item=True,
                                randomize_options=False,
                                timer=None,
                                add_scores=False,
                                set_alerts=False,
                                add_tooltip=False,
                                set_palette=False,
                                additional_response_option=dict(
                                    text_input_option=False,
                                    text_input_required=False,
                                ),
                            ),
                        ),
                        dict(
                            name="evening_activity_item33",
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            response_type="photo",
                            response_values=None,
                            config=dict(
                                remove_back_button=False,
                                skippable_item=True,
                                timer=None,
                                additional_response_option=dict(
                                    text_input_option=False,
                                    text_input_required=False,
                                ),
                            ),
                        ),
                    ],
                ),
            ],
        )
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=create_data,
        )
        assert response.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_creating_applet_failed_by_duplicate_activity_item_name(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        create_data = dict(
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
                    name="AAA",
                    key="577dbbda-3afc-4962-842b-8d8d11588bfe",
                    description=dict(
                        en="Understand morning feelings.",
                        fr="Understand morning feelings.",
                    ),
                    items=[
                        dict(
                            name="aaa",
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            response_type="text",
                            response_values=None,
                            is_hidden=True,
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
                            name="aaa",
                            question=dict(
                                en="How had you woke?",
                                fr="How had you woke?",
                            ),
                            response_type="slider",
                            response_values=dict(
                                min_label="Not at all",
                                max_label="Very much",
                                min_value=1,
                                max_value=5,
                                min_image=None,
                                max_image=None,
                                scores=None,
                            ),
                            config=dict(
                                add_scores=False,
                                set_alerts=False,
                                show_tick_marks=False,
                                show_tick_labels=False,
                                continuous_slider=False,
                                timer=None,
                                remove_back_button=False,
                                skippable_item=True,
                                additional_response_option=dict(
                                    text_input_option=False,
                                    text_input_required=False,
                                ),
                            ),
                        ),
                    ],
                )
            ],
        )
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=create_data,
        )
        assert response.status_code == http.HTTPStatus.UNPROCESSABLE_ENTITY

    async def test_create_duplicate_name_applet(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        create_data = dict(
            display_name="Applet 1",
            encryption=dict(
                public_key=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
            ),
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
                            name="evening_activity_item",
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
                    ],
                ),
                dict(
                    name="Evening activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            name="evening_activity_item",
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
                    items=[dict(activity_key="577dbbda-3afc-" "4962-842b-8d8d11588bfe")],
                )
            ],
        )
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=create_data,
        )
        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        assert response.json()["result"][0]["message"] == "Applet already exists."

    async def test_create_duplicate_case_sensitive_name_applet(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        create_data = dict(
            display_name="AppleT 1",
            encryption=dict(
                public_key=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
            ),
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
                            name="evening_activity_item",
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
                    ],
                ),
                dict(
                    name="Evening activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            name="evening_activity_item",
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
                    items=[dict(activity_key="577dbbda-3afc-" "4962-842b-8d8d11588bfe")],
                )
            ],
        )
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=create_data,
        )
        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        assert response.json()["result"][0]["message"] == "Applet already exists."

    async def test_update_applet(self, client, tom, device_tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        update_data = dict(
            stream_enabled=True,
            stream_ip_address="127.0.0.1",
            stream_port=8881,
            display_name="Applet 1",
            encryption=dict(
                public_key=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
            ),
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
                    id="09e3dbf0-aefb-4d0e-9177-bdb321bf3611",
                    name="Morning activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bfe",
                    description=dict(
                        en="Understand morning feelings.",
                        fr="Understand morning feelings.",
                    ),
                    items=[
                        dict(
                            id="a18d3409-2c96-4a5e-a1f3-1c1c14be0011",
                            name="evening_activity_item",
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
                            name="evening_activity_item2",
                            question=dict(
                                en="How was your breakfast?",
                                fr="How was your breakfast?",
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
                            id="a18d3409-2c96-4a5e-a1f3-1c1c14be0012",
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
                    ],
                ),
                dict(
                    name="Evening activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            question=dict(
                                en="How had you spent your time?",
                                fr="How had you spent your time?",
                            ),
                            name="evening_activity_item3",
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
                            id="7941b770-b649-42fc-832a-870e11bdd402",
                            activity_key="577dbbda-" "3afc-4962-842b-8d8d11588bfe",
                        )
                    ],
                )
            ],
        )
        activity_key = update_data["activity_flows"][0]["items"][0]["activity_key"]
        wrong_activity_key = uuid.uuid4()
        update_data["activity_flows"][0]["items"][0]["activity_key"] = wrong_activity_key

        response = await client.put(
            self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
            data=update_data,
        )
        assert response.status_code == activity_errors.FlowItemActivityKeyNotFoundError.status_code
        assert response.json()["result"][0]["message"] == activity_errors.FlowItemActivityKeyNotFoundError.message

        update_data["activity_flows"][0]["items"][0]["activity_key"] = activity_key
        response = await client.put(
            self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
            data=update_data,
        )
        assert response.status_code == http.HTTPStatus.OK, response.json()

        # TODO: move to fixtures
        assert len(FCMNotificationTest.notifications) == 1
        assert device_tom in FCMNotificationTest.notifications
        notification = json.loads(FCMNotificationTest.notifications[device_tom][0])
        assert notification["title"] == "Applet is updated."
        FCMNotificationTest.notifications = collections.defaultdict(list)

        data = response.json()
        response = await client.put(
            self.activity_report_config_url.format(
                pk="92917a56-d586-4613-b7aa-991f2c4b15b1",
                activity_id="09e3dbf0-aefb-4d0e-9177-bdb321bf3611",
            ),
            data=dict(report_included_item_name="evening_activity_item3"),
        )
        assert response.status_code == http.HTTPStatus.OK

        flow_id = data["result"]["activityFlows"][0]["id"]
        response = await client.put(
            self.flow_report_config_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1", flow_id=flow_id),
            data=dict(
                report_included_activity_name="Morning activity",
                report_included_item_name="evening_activity_item3",
            ),
        )
        assert response.status_code == http.HTTPStatus.OK

        # get applet and check stream settings
        response = await client.get(self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"))
        assert response.status_code == 200
        assert response.json()["result"]["streamEnabled"] is True
        assert response.json()["result"]["streamIpAddress"] == update_data["stream_ip_address"]
        assert response.json()["result"]["streamPort"] == update_data["stream_port"]

    async def test_duplicate_applet(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")

        response = await client.post(
            self.applet_duplicate_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
            data=dict(
                display_name="New name",
                encryption=dict(
                    public_key=uuid.uuid4().hex,
                    account_id=str(uuid.uuid4()),
                    prime=uuid.uuid4().hex,
                    base=uuid.uuid4().hex,
                ),
            ),
        )
        assert response.status_code == http.HTTPStatus.CREATED, response.json()

        response = await client.get(self.applet_list_url)
        assert len(response.json()["result"]) == 4
        assert response.json()["result"][0]["displayName"] == "New name"

        response = await client.post(
            self.applet_duplicate_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
            data=dict(
                display_name="New name",
                encryption=dict(
                    public_key=uuid.uuid4().hex,
                    account_id=str(uuid.uuid4()),
                    prime=uuid.uuid4().hex,
                    base=uuid.uuid4().hex,
                ),
            ),
        )
        assert response.status_code == http.HTTPStatus.BAD_REQUEST

    async def test_set_applet_report_configuration(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")

        report_configuration = dict(
            report_server_ip="ipaddress",
            report_public_key="public key",
            report_recipients=["recipient1", "recipient1"],
            report_include_user_id=True,
            report_include_case_id=True,
            report_email_body="email body",
        )

        response = await client.post(
            self.applet_report_config_url.format(
                pk="92917a56-d586-4613-b7aa-991f2c4b15b1",
            ),
            report_configuration,
        )
        assert response.status_code == http.HTTPStatus.OK, response.json()

        response = await client.get(self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"))
        assert response.status_code == http.HTTPStatus.OK
        assert response.json()["result"]["reportServerIp"] == report_configuration["report_server_ip"]
        assert response.json()["result"]["reportPublicKey"] == report_configuration["report_public_key"]
        assert response.json()["result"]["reportRecipients"] == report_configuration["report_recipients"]
        assert response.json()["result"]["reportIncludeUserId"] == report_configuration["report_include_user_id"]
        assert response.json()["result"]["reportIncludeCaseId"] == report_configuration["report_include_case_id"]
        assert response.json()["result"]["reportEmailBody"] == report_configuration["report_email_body"]

    async def test_publish_conceal_applet(self, client, tom):
        # NOTE: only superadmin can publish an applet
        await client.login(self.login_url, settings.super_admin.email, settings.super_admin.password)
        response = await client.post(self.applet_publish_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"))
        assert response.status_code == http.HTTPStatus.OK, response.json()

        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        response = await client.get(self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"))
        assert response.status_code == http.HTTPStatus.OK
        assert response.json()["result"]["isPublished"] is True

        # NOTE: only superadmin can conceal an applet
        await client.login(self.login_url, settings.super_admin.email, settings.super_admin.password)
        response = await client.post(self.applet_conceal_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"))
        assert response.status_code == http.HTTPStatus.OK, response.json()

        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        response = await client.get(self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"))
        assert response.status_code == http.HTTPStatus.OK
        assert response.json()["result"]["isPublished"] is False

    async def test_set_encryption(self, client):
        await client.login(self.login_url, "bob@gmail.com", "Test1234!")

        response = await client.post(
            self.applet_set_encryption_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b4"),
            data=dict(
                public_key=uuid.uuid4().hex,
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
            ),
        )
        assert response.status_code == http.HTTPStatus.OK, response.json()

        response = await client.post(
            self.applet_set_encryption_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b4"),
            data=dict(
                public_key=uuid.uuid4().hex,
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
            ),
        )
        assert response.status_code == 403, response.json()

    async def test_applet_list(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        response = await client.get(self.applet_list_url)

        assert response.status_code == http.HTTPStatus.OK, response.json()
        assert len(response.json()["result"]) == 3
        assert response.json()["result"][0]["id"] == "92917a56-d586-4613-b7aa-991f2c4b15b5"
        assert response.json()["result"][1]["id"] == "92917a56-d586-4613-b7aa-991f2c4b15b2"
        assert response.json()["result"][2]["id"] == "92917a56-d586-4613-b7aa-991f2c4b15b1"

    async def test_applet_delete(self, client, tom, device_tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        response = await client.delete(
            self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
        )

        assert response.status_code == 204, response.json()

        response = await client.delete(
            self.applet_detail_url.format(pk="00000000-0000-0000-0000-000000000000"),
        )

        assert response.status_code == 404, response.json()

        # TODO: move to the fixtures
        assert len(FCMNotificationTest.notifications) == 1
        assert device_tom in FCMNotificationTest.notifications
        notification = json.loads(FCMNotificationTest.notifications[device_tom][0])
        assert notification["title"] == "Applet is deleted."
        FCMNotificationTest.notifications = collections.defaultdict(list)

    async def test_applet_delete_by_manager(self, client):
        await client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await client.delete(
            self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
        )

        assert response.status_code == 204

    async def test_applet_delete_by_coordinator(self, client):
        await client.login(self.login_url, "bob@gmail.com", "Test1234!")
        response = await client.delete(
            self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
        )

        assert response.status_code == 403

    async def test_applet_list_with_invalid_token(self, client, tom):
        from config import settings

        current_access_token_expiration = settings.authentication.access_token.expiration

        settings.authentication.access_token.expiration = 0.05
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        await asyncio.sleep(4)
        response = await client.get(self.applet_list_url)

        settings.authentication.access_token.expiration = current_access_token_expiration
        assert response.status_code == 401, response.json()

    async def test_applet_list_with_expired_token(self, client):
        response = await client.get(
            self.applet_list_url,
            headers=dict(Authorization="Bearer invalid_token"),
        )

        assert response.status_code == 401, response.json()

    async def test_applet_list_by_filters(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        response = await client.get(self.applet_list_url, dict(ordering="id", owner_id=1, limit=1))

        assert response.status_code == http.HTTPStatus.OK
        assert len(response.json()["result"]) == 1
        assert response.json()["result"][0]["id"] == "92917a56-d586-4613-b7aa-991f2c4b15b1"

    async def test_applet_detail(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        response = await client.get(self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"))
        assert response.status_code == http.HTTPStatus.OK
        result = response.json()["result"]
        assert result["id"] == "92917a56-d586-4613-b7aa-991f2c4b15b1"
        assert result["displayName"] == "Applet 1"
        assert len(result["activities"]) == 1
        assert len(result["activityFlows"]) == 2
        assert len(result["activityFlows"][0]["activityIds"]) == 1
        assert len(result["activityFlows"][1]["activityIds"]) == 1

    async def test_public_applet_detail(self, client):
        response = await client.get(self.public_applet_detail_url.format(key="51857e10-6c05-4fa8-a2c8-725b8c1a0aa6"))
        assert response.status_code == http.HTTPStatus.OK
        result = response.json()["result"]
        assert result["id"] == "92917a56-d586-4613-b7aa-991f2c4b15b1"
        assert result["displayName"] == "Applet 1"
        assert len(result["activities"]) == 1
        assert len(result["activityFlows"]) == 2
        assert len(result["activityFlows"][0]["activityIds"]) == 1
        assert len(result["activityFlows"][1]["activityIds"]) == 1

    async def test_creating_applet_history(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        create_data = dict(
            display_name="User daily behave",
            encryption=dict(
                public_key=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
            ),
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
                            name="morning_activity_item1",
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
                    ],
                ),
                dict(
                    name="Evening activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            name="evening_activity_item1",
                            question=dict(
                                en="How had you spent your time?",
                                fr="How had you spent your time?",
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
                    items=[dict(activity_key="577dbbda-3afc-" "4962-842b-8d8d11588bfe")],
                )
            ],
        )
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=create_data,
        )
        assert response.status_code == http.HTTPStatus.CREATED, response.json()

        version = response.json()["result"]["version"]
        applet_id = response.json()["result"]["id"]

        response = await client.get(self.histories_url.format(pk=applet_id))

        assert response.status_code == http.HTTPStatus.OK, response.json()
        versions = response.json()["result"]
        assert len(versions) == 1
        assert versions[0]["version"] == version

    async def test_versions_for_not_existed_applet(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        response = await client.get(self.histories_url.format(pk=uuid.uuid4()))

        assert response.status_code == 404, response.json()

    async def test_updating_applet_history(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        update_data = dict(
            display_name="Applet 1",
            encryption=dict(
                public_key=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
            ),
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
                    id="09e3dbf0-aefb-4d0e-9177-bdb321bf3611",
                    name="Morning activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bfe",
                    description=dict(
                        en="Understand morning feelings.",
                        fr="Understand morning feelings.",
                    ),
                    items=[
                        dict(
                            id="a18d3409-2c96-4a5e-a1f3-1c1c14be0011",
                            name="morning_activity_item132",
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
                            name="morning_activity_item133",
                            question=dict(
                                en="How was your breakfast?",
                                fr="How was your breakfast?",
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
                    ],
                ),
                dict(
                    name="Evening activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            name="evening_activity_item132",
                            question=dict(
                                en="How had you spent your time?",
                                fr="How had you spent your time?",
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
                            id="7941b770-b649-42fc-832a-870e11bdd402",
                            activity_key="577dbbda-" "3afc-4962-842b-8d8d11588bfe",
                        )
                    ],
                )
            ],
        )
        response = await client.put(
            self.applet_detail_url.format(pk="92917a56-d586-4613-b7aa-991f2c4b15b1"),
            data=update_data,
        )
        assert response.status_code == http.HTTPStatus.OK, response.json()

        applet_id = response.json()["result"]["id"]

        assert response.json()["result"]["version"] == "2.0.0"

        response = await client.get(self.histories_url.format(pk=applet_id))

        assert response.status_code == http.HTTPStatus.OK, response.json()
        versions = response.json()["result"]
        assert len(versions) == 3
        assert versions[0]["version"] == "2.0.0"
        assert versions[1]["version"] == "1.9.9"
        assert versions[2]["version"] == "1.0.0"

        response = await client.get(self.history_url.format(pk=applet_id, version="1.9.9"))

        assert response.status_code == http.HTTPStatus.OK, response.json()
        applet = response.json()["result"]
        assert applet["version"] == "1.9.9"

        response = await client.get(self.history_url.format(pk=applet_id, version="1.0.0"))

        assert response.status_code == http.HTTPStatus.OK, response.json()
        applet = response.json()["result"]
        assert applet["version"] == "1.0.0"

        response = await client.get(self.history_url.format(pk=applet_id, version="0.0.0"))

        assert response.status_code == 404, response.json()

    async def test_history_changes(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        create_data = dict(
            display_name="User daily behave",
            encryption=dict(
                public_key=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
            ),
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
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            name="morning_activity_item132",
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
                    ],
                ),
                dict(
                    name="Evening activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            question=dict(
                                en="How had you spent your time?",
                                fr="How had you spent your time?",
                            ),
                            name="evening_activity_item132",
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
                    items=[dict(activity_key="577dbbda-3afc-" "4962-842b-8d8d11588bfe")],
                )
            ],
        )
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=create_data,
        )

        update_data = dict(
            display_name="User daily behave updated",
            encryption=dict(
                public_key=uuid.uuid4().hex,
                account_id=str(uuid.uuid4()),
                prime=uuid.uuid4().hex,
                base=uuid.uuid4().hex,
            ),
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
                    id="09e3dbf0-aefb-4d0e-9177-bdb321bf3615",
                    name="Morning activity new",
                    key="577dbbda-3afc-4962-842b-8d8d11588bfe",
                    description=dict(
                        en="Understand morning feelings.",
                        fr="Understand morning feelings.",
                    ),
                    items=[
                        dict(
                            question=dict(
                                en="How had you slept?",
                                fr="How had you slept?",
                            ),
                            name="morning_activity_item132",
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
                            question=dict(
                                en="How was your breakfast?",
                                fr="How was your breakfast?",
                            ),
                            name="morning_activity_item133",
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
                            name="morning_activity_item_2",
                            question=dict(
                                en="How had you woke?",
                                fr="How had you woke?",
                            ),
                            response_type="slider",
                            response_values=dict(
                                min_label="Not at all",
                                max_label="Very much",
                                min_value=1,
                                max_value=5,
                                min_image=None,
                                max_image=None,
                                scores=[0, 1, 2, 3, 4],
                            ),
                            config=dict(
                                add_scores=True,
                                set_alerts=False,
                                show_tick_marks=False,
                                show_tick_labels=False,
                                continuous_slider=False,
                                timer=None,
                                remove_back_button=False,
                                skippable_item=True,
                                additional_response_option=dict(
                                    text_input_option=False,
                                    text_input_required=False,
                                ),
                            ),
                        ),
                    ],
                    scores_and_reports=dict(
                        generateReport=True,
                        showScoreSummary=True,
                        reports=[
                            dict(
                                name="morning_activity_item_2",
                                type="score",
                                id="morning_activity_item_2",
                                calculationType="sum",
                                minScore=0,
                                maxScore=3,
                                itemsScore=["morning_activity_item_2"],
                                message="Hello",
                                itemsPrint=["morning_activity_item_2"],
                                conditionalLogic=[
                                    dict(
                                        name="morning_activity_item_2",
                                        id="morning_activity_item_2",
                                        flagScore=True,
                                        message="Hello2",
                                        match="any",
                                        conditions=[
                                            dict(
                                                item_name=("morning_activity_item_2"),
                                                type="GREATER_THAN",
                                                payload=dict(
                                                    value=1,
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            dict(
                                name="morning_activity_item_2",
                                type="section",
                                messages="Hello from the other side",
                                itemsPrint=[
                                    "morning_activity_item_2",
                                ],
                                conditionalLogic=dict(
                                    match="all",
                                    conditions=[
                                        dict(
                                            item_name=("morning_activity_item_2"),
                                            type="GREATER_THAN",
                                            payload=dict(
                                                value=1,
                                            ),
                                        ),
                                        dict(
                                            item_name=("morning_activity_item_2"),
                                            type="EQUAL_TO_OPTION",
                                            payload=dict(
                                                option_value="1",  # noqa E501
                                            ),
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                dict(
                    name="Evening activity",
                    key="577dbbda-3afc-4962-842b-8d8d11588bff",
                    description=dict(
                        en="Understand evening feelings.",
                        fr="Understand evening feelings.",
                    ),
                    items=[
                        dict(
                            question=dict(
                                en="How had you spent your time?",
                                fr="How had you spent your time?",
                            ),
                            name="evening_activity_item132",
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
                            activity_key="577dbbda-" "3afc-4962-842b-8d8d11588bfe",
                        )
                    ],
                )
            ],
        )
        response = await client.put(
            self.applet_detail_url.format(pk=response.json()["result"]["id"]),
            data=update_data,
        )

        assert response.status_code == http.HTTPStatus.OK, response.json()

        version = response.json()["result"]["version"]
        applet_id = response.json()["result"]["id"]

        response = await client.get(self.history_changes_url.format(pk=applet_id, version=version))
        assert response.status_code == http.HTTPStatus.OK
        assert response.json()["result"]["displayName"] == "Applet User daily behave updated updated"
        assert len(response.json()["result"]["activities"]) == 4

    async def test_get_applet_unique_name(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")

        response = await client.post(self.applet_unique_name_url, data=dict(name="Applet 1"))

        assert response.status_code == http.HTTPStatus.OK
        assert response.json()["result"]["name"] == "Applet 1 (1)"

    async def test_get_applet_unique_name_case_insensitive(self, client, tom):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")

        response = await client.post(self.applet_unique_name_url, data=dict(name="AppleT 1"))

        assert response.status_code == http.HTTPStatus.OK
        assert response.json()["result"]["name"] == "AppleT 1 (1)"

    async def test_get_applet_activities_info(self, client, tom, applet_minimal_data):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        # create applet with minimal data
        multi_select = deepcopy(applet_minimal_data.activities[0].items[0])
        multi_select.name = "test_multiSelect"
        multi_select.response_type = "multiSelect"
        multi_select.is_hidden = True
        applet_minimal_data.activities[0].items.append(multi_select)
        response = await client.post(self.applet_create_url.format(owner_id=tom.id), data=applet_minimal_data)

        new_applet_id = response.json()["result"]["id"]
        response = await client.get(self.applet_base_info_url.format(pk=new_applet_id))
        assert response.status_code == 200
        assert response.json()["result"]["displayName"] == applet_minimal_data.display_name
        # check if hidden item is not shown
        assert "singleSelect" in response.json()["result"]["activities"][0]["containsResponseTypes"]
        assert "multiSelect" not in response.json()["result"]["activities"][0]["containsResponseTypes"]
        assert isinstance(response.json()["result"]["activities"][0]["itemCount"], int)
        assert response.json()["result"]["activities"][0]["itemCount"] == 1

    async def test_get_public_applet_activities_info(self, client, tom, applet_minimal_data):
        await client.login(self.login_url, tom.email_encrypted, "Test1234!")
        # create applet with minimal data
        multi_select = deepcopy(applet_minimal_data.activities[0].items[0])
        multi_select.name = "test_multiSelect"
        multi_select.response_type = "multiSelect"
        multi_select.is_hidden = True
        applet_minimal_data.activities[0].items.append(multi_select)
        response = await client.post(self.applet_create_url.format(owner_id=tom.id), data=applet_minimal_data)

        new_applet_id = response.json()["result"]["id"]
        print("new applet id", new_applet_id)
        data = {"require_login": False}
        response = await client.post(
            self.access_link_url.format(pk=new_applet_id),
            data=data,
        )

        key_link = response.json()["result"]["link"]
        key = key_link.split("/")[-1]
        response = await client.get(self.public_applet_base_info_url.format(key=key))

        assert response.status_code == 200
        assert response.json()["result"]["displayName"] == applet_minimal_data.display_name
        assert "singleSelect" in response.json()["result"]["activities"][0]["containsResponseTypes"]
        assert "multiSelect" not in response.json()["result"]["activities"][0]["containsResponseTypes"]
        assert isinstance(response.json()["result"]["activities"][0]["itemCount"], int)
        assert response.json()["result"]["activities"][0]["itemCount"] == 1

    async def test_create_applet_in_another_workspace_not_owner(self, client, applet_minimal_data, tom):
        await client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=applet_minimal_data,
        )
        assert response.status_code == http.HTTPStatus.CREATED

    async def test_create_applet_in_another_workspace_not_owner_user_is_not_invited(
        self, client, applet_minimal_data, bob
    ):
        await client.login(self.login_url, "lucy@gmail.com", "Test123")
        response = await client.post(
            self.applet_create_url.format(owner_id=bob.id),
            data=applet_minimal_data,
        )
        assert response.status_code == http.HTTPStatus.FORBIDDEN
        result = response.json()["result"]
        assert len(result) == 1
        assert result[0]["message"] == AppletCreationAccessDenied.message

    async def test_create_applet_in_another_workspace_not_owner_user_does_not_have_role_to_create_applet(
        self, client, applet_minimal_data, tom
    ):
        await client.login(self.login_url, "bob@gmail.com", "Test1234!")
        response = await client.post(
            self.applet_create_url.format(owner_id=tom.id),
            data=applet_minimal_data,
        )
        assert response.status_code == http.HTTPStatus.FORBIDDEN
        result = response.json()["result"]
        assert len(result) == 1
        assert result[0]["message"] == AppletCreationAccessDenied.message
