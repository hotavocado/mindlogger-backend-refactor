from typing import cast

import pytest

from apps.activities.domain.activity_create import ActivityItemCreate
from apps.activities.domain.conditional_logic import ConditionalLogic
from apps.activities.domain.conditions import (
    Condition,
    ConditionType,
    EqualCondition,
    EqualToOptionCondition,
    OptionPayload,
    ValuePayload,
)
from apps.activities.domain.custom_validation import validate_item_flow, validate_score_and_sections, validate_subscales
from apps.activities.domain.response_type_config import ResponseType, SingleSelectionConfig
from apps.activities.domain.scores_reports import (
    ReportType,
    Score,
    ScoreConditionalLogic,
    ScoresAndReports,
    Section,
    SectionConditionalLogic,
    Subscale,
    SubscaleItem,
    SubscaleItemType,
    SubscaleSetting,
)
from apps.activities.errors import (
    IncorrectConditionItemError,
    IncorrectConditionItemIndexError,
    IncorrectConditionLogicItemTypeError,
    IncorrectConditionOptionError,
    IncorrectScoreItemConfigError,
    IncorrectScoreItemError,
    IncorrectScoreItemTypeError,
    IncorrectScorePrintItemError,
    IncorrectScorePrintItemTypeError,
    IncorrectSectionConditionItemError,
    IncorrectSectionPrintItemError,
    IncorrectSectionPrintItemTypeError,
    IncorrectSubscaleInsideSubscaleError,
    IncorrectSubscaleItemError,
    SubscaleInsideSubscaleError,
    SubscaleItemScoreError,
    SubscaleItemTypeError,
)
from apps.test_data.service import TestDataService

ACTIVITY_ITEM_OPTIONS = [
    ResponseType.SINGLESELECT,
    ResponseType.MULTISELECT,
    ResponseType.SLIDER,
]


@pytest.fixture
def items() -> list[ActivityItemCreate]:
    items = []
    for index in range(1, 5):
        response_type = ACTIVITY_ITEM_OPTIONS[index % len(ACTIVITY_ITEM_OPTIONS)]
        response_config = TestDataService.generate_response_value_config(type_=response_type)

        item_name = f"activity_item_{index}"
        items.append(
            ActivityItemCreate(
                name=item_name,
                question=dict(
                    en=f"Activity item EN question {index}",
                    fr=f"Activity item FR question {index}",
                ),
                response_type=response_type,
                response_values=response_config["response_values"],
                config=response_config["config"],
                is_hidden=False,
                conditional_logic=ConditionalLogic(
                    conditions=[
                        EqualCondition(
                            item_name=item_name,
                            type=ConditionType.EQUAL,
                            payload=ValuePayload(value=1),
                        )
                    ]
                ),
            )
        )

    return items


class TestValidateItemFlow:
    def test_successful_validation(self, items: list[ActivityItemCreate]):
        values = {"items": items}
        assert values == validate_item_flow(values)

    def test_non_existent_conditional_name(self, items: list[ActivityItemCreate]):
        values = {"items": items}
        items[0].conditional_logic = ConditionalLogic(
            conditions=[
                EqualCondition(
                    item_name="non-existent name",
                    type=ConditionType.EQUAL,
                    payload=ValuePayload(value=1),
                )
            ]
        )
        with pytest.raises(IncorrectConditionItemError):
            validate_item_flow(values)

    def test_incorrect_conditional_index(self, items: list[ActivityItemCreate]):
        values = {"items": items}

        items[0].conditional_logic, items[1].conditional_logic = (
            items[1].conditional_logic,
            items[0].conditional_logic,
        )
        with pytest.raises(IncorrectConditionItemIndexError):
            validate_item_flow(values)

    def test_incorrect_conditional_item_type(self, items: list[ActivityItemCreate]):
        values = {"items": items}

        items[0].response_type = ResponseType.TEXT
        with pytest.raises(IncorrectConditionLogicItemTypeError):
            validate_item_flow(values)

    def test_incorrect_conditional_option(self, items: list[ActivityItemCreate]):
        values = {"items": items}

        conditions: list[Condition] = [
            EqualToOptionCondition(
                item_name=items[0].name,
                type=ConditionType.EQUAL_TO_OPTION,
                payload=OptionPayload(option_value="incorrect_option_value"),
            )
        ]
        if items[0].conditional_logic:
            items[0].conditional_logic.conditions = conditions
        with pytest.raises(IncorrectConditionOptionError):
            validate_item_flow(values)


class TestValidateScoreAndSections:
    def test_successful_validation(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
    ):
        values = {"items": items, "scores_and_reports": scores_and_reports}
        assert values == validate_score_and_sections(values)

    def test_without_report(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
    ):
        del scores_and_reports.reports
        values = {"items": items, "scores_and_reports": scores_and_reports}
        assert validate_score_and_sections(values) is None

    def test_items_score_not_in_item_names(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        score: Score,
    ):
        score.items_score = ["incorrect_item_name"]
        scores_and_reports.reports = [score]
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectScoreItemError):
            validate_score_and_sections(values)

    def test_incorrect_score_item_type(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        score: Score,
    ):
        score.items_score = [items[0].name]
        scores_and_reports.reports = [score]
        items[0].response_type = ResponseType.TEXT
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectScoreItemTypeError):
            validate_score_and_sections(values)

    def test_incorrect_score_item_config(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        score: Score,
    ):
        score.items_score = [items[0].name]
        scores_and_reports.reports = [score]
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectScoreItemConfigError):
            validate_score_and_sections(values)

    def test_items_score_items_print_not_in_item_names(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        score: Score,
    ):
        score.items_print = ["incorrect_item_name"]
        scores_and_reports.reports = [score]
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectScorePrintItemError):
            validate_score_and_sections(values)

    def test_incorrect_score_items_print_item_type(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        score: Score,
    ):
        score.items_print = [items[0].name]
        scores_and_reports.reports = [score]
        items[0].response_type = ResponseType.TIMERANGE
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectScorePrintItemTypeError):
            validate_score_and_sections(values)

    def test_items_score_conditional_logic_not_in_item_names(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        score: Score,
    ):
        score.conditional_logic = [
            ScoreConditionalLogic(
                name="Some name",
                id="Some name",
                items_print=["non-existent name"],
                match="any",
                conditions=[
                    EqualCondition(
                        item_name=score.id,
                        type=ConditionType.EQUAL,
                        payload=ValuePayload(value=1),
                    )
                ],
            ),
        ]
        scores_and_reports.reports = [score]
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectScorePrintItemError):
            validate_score_and_sections(values)

    def test_items_score_conditional_logic_print_item_type(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        score: Score,
    ):
        score.conditional_logic = [
            ScoreConditionalLogic(
                name="Some name",
                id="Some name",
                items_print=[items[0].name],
                match="any",
                conditions=[
                    EqualCondition(
                        item_name=score.id,
                        type=ConditionType.EQUAL,
                        payload=ValuePayload(value=1),
                    )
                ],
            ),
        ]
        scores_and_reports.reports = [score]
        items[0].response_type = ResponseType.TIMERANGE
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectScorePrintItemTypeError):
            validate_score_and_sections(values)

    def test_items_sections_not_in_item_names(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        section: Section,
    ):
        section.items_print = ["incorrect_item_name"]
        scores_and_reports.reports = [section]
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectSectionPrintItemError):
            validate_score_and_sections(values)

    def test_incorrect_sections_item_type(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        section: Section,
    ):
        section.items_print = [items[0].name]
        scores_and_reports.reports = [section]
        items[0].response_type = ResponseType.TIMERANGE
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectSectionPrintItemTypeError):
            validate_score_and_sections(values)

    def test_items_sections_conditional_logic_item(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
    ):
        items[1].response_type = ResponseType.TIMERANGE
        section = Section(
            type=ReportType.section,
            name="testsection",
            conditional_logic=SectionConditionalLogic(
                match="any",
                conditions=[
                    EqualCondition(
                        item_name="item_name",
                        type=ConditionType.EQUAL,
                        payload=ValuePayload(value=1),
                    )
                ],
            ),
        )
        scores_and_reports.reports = [section]
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectSectionConditionItemError):
            validate_score_and_sections(values)

    def test_duplicated_section_name_in_reports(
        self,
        items: list[ActivityItemCreate],
        scores_and_reports: ScoresAndReports,
        section: Section,
    ):
        copy = section.copy(deep=True)
        copy.items_print = [items[0].name]
        scores_and_reports.reports = cast(list, scores_and_reports.reports)
        scores_and_reports.reports.append(copy)
        items[0].response_type = ResponseType.TIMERANGE
        values = {"items": items, "scores_and_reports": scores_and_reports}
        with pytest.raises(IncorrectSectionPrintItemTypeError):
            validate_score_and_sections(values)


class TestValidateSubscales:
    def test_successful_validation(
        self,
        items: list[ActivityItemCreate],
        subscale_setting: SubscaleSetting,
    ):
        items0_config: SingleSelectionConfig = items[0].config  # type: ignore[assignment]
        items0_config.add_scores = True
        values = {"items": items, "subscale_setting": subscale_setting}
        assert values == validate_subscales(values)

    def test_incorrect_subscale_item(
        self,
        items: list[ActivityItemCreate],
        subscale_setting: SubscaleSetting,
        subscale: Subscale,
        subscale_item: SubscaleItem,
    ):
        items0_config: SingleSelectionConfig = items[0].config  # type: ignore[assignment]
        items0_config.add_scores = True
        subscale_item.name = "incorrect_item_name"
        subscale.items = [subscale_item]
        subscale_setting.subscales = [subscale]
        values = {"items": items, "subscale_setting": subscale_setting}
        with pytest.raises(IncorrectSubscaleItemError):
            validate_subscales(values)

    def test_subscale_item_type_error(
        self,
        items: list[ActivityItemCreate],
        subscale_setting: SubscaleSetting,
    ):
        items0_config: SingleSelectionConfig = items[0].config  # type: ignore[assignment]
        items0_config.add_scores = True
        items[0].response_type = ResponseType.TIMERANGE
        values = {"items": items, "subscale_setting": subscale_setting}
        with pytest.raises(SubscaleItemTypeError):
            validate_subscales(values)

    def test_subscale_item_score_error(
        self,
        items: list[ActivityItemCreate],
        subscale_setting: SubscaleSetting,
    ):
        values = {"items": items, "subscale_setting": subscale_setting}
        with pytest.raises(SubscaleItemScoreError):
            validate_subscales(values)

    def test_incorrect_subscale_inside_subscale(
        self,
        items: list[ActivityItemCreate],
        subscale_setting: SubscaleSetting,
        subscale: Subscale,
        subscale_item: SubscaleItem,
    ):
        items0_config: SingleSelectionConfig = items[0].config  # type: ignore[assignment]
        items0_config.add_scores = True
        subscale_item.type = SubscaleItemType.SUBSCALE
        subscale.items = [subscale_item]
        subscale_setting.subscales = [subscale]
        values = {"items": items, "subscale_setting": subscale_setting}
        with pytest.raises(IncorrectSubscaleInsideSubscaleError):
            validate_subscales(values)

    def test_subscale_inside_subscale_error(
        self,
        items: list[ActivityItemCreate],
        subscale_setting: SubscaleSetting,
        subscale: Subscale,
        subscale_item: SubscaleItem,
    ):
        items0_config: SingleSelectionConfig = items[0].config  # type: ignore[assignment]
        items0_config.add_scores = True
        subscale_item.name = "test subscale name"
        subscale_item.type = SubscaleItemType.SUBSCALE
        subscale.items = [subscale_item]
        subscale_setting.subscales = [subscale]
        values = {"items": items, "subscale_setting": subscale_setting}
        with pytest.raises(SubscaleInsideSubscaleError):
            validate_subscales(values)
