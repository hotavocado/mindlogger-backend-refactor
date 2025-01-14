from pydantic import Field, NonNegativeInt, root_validator, validator
from pydantic.color import Color

from apps.activities.errors import (
    InvalidDataMatrixByOptionError,
    InvalidDataMatrixError,
    InvalidScoreLengthError,
    MinValueError,
    MultiSelectNoneOptionError,
)
from apps.shared.domain import PublicModel, validate_color, validate_image, validate_uuid


class TextValues(PublicModel):
    pass


class MessageValues(PublicModel):
    pass


class TimeRangeValues(PublicModel):
    pass


class TimeValues(PublicModel):
    pass


class GeolocationValues(PublicModel):
    pass


class PhotoValues(PublicModel):
    pass


class VideoValues(PublicModel):
    pass


class DateValues(PublicModel):
    pass


class FlankerValues(PublicModel):
    pass


class StabilityTrackerValues(PublicModel):
    pass


class ABTrailsValues(PublicModel):
    pass


class _SingleSelectionValue(PublicModel):
    id: str | None = None
    text: str
    image: str | None = None
    score: int | None = None
    tooltip: str | None = None
    is_hidden: bool = Field(default=False)
    color: Color | None = None
    alert: str | None = None
    value: int | None = None

    @validator("image")
    def validate_image(cls, value):
        # validate image if not None
        if value is not None:
            return validate_image(value)
        return value

    @validator("color")
    def validate_color(cls, value):
        if value is not None:
            return validate_color(value)
        return value

    @validator("id")
    def validate_id(cls, value):
        return validate_uuid(value)


class SingleSelectionValues(PublicModel):
    palette_name: str | None
    options: list[_SingleSelectionValue]

    @validator("options")
    def validate_options(cls, value):
        return validate_options_value(value)


class _MultiSelectionValue(_SingleSelectionValue):
    is_none_above: bool = Field(default=False)


class MultiSelectionValues(PublicModel):
    palette_name: str | None
    options: list[_MultiSelectionValue]

    @validator("options")
    def validate_options(cls, value):
        return validate_options_value(value)

    @validator("options")
    def validate_none_option_flag(cls, value):
        return validate_none_option_flag(value)


class SliderValueAlert(PublicModel):
    value: int | None = Field(
        default=0,
        description="Either value or min_value and max_value must be provided. For SliderRows, only value is allowed.",  # noqa: E501
    )
    min_value: int | None
    max_value: int | None
    alert: str

    @root_validator()
    def validate_min_max_values(cls, values):
        if values.get("min_value") is not None and values.get("max_value") is not None:
            if values.get("min_value") >= values.get("max_value"):
                raise MinValueError()
        return values


class SliderValues(PublicModel):
    min_label: str | None = Field(..., max_length=100)
    max_label: str | None = Field(..., max_length=100)
    min_value: NonNegativeInt = Field(default=0, max_value=11)
    max_value: NonNegativeInt = Field(default=12, max_value=12)
    min_image: str | None = None
    max_image: str | None = None
    scores: list[int] | None = None
    alerts: list[SliderValueAlert] | None = None

    @validator("min_image", "max_image")
    def validate_image(cls, value):
        if value is not None:
            return validate_image(value)
        return value

    @root_validator
    def validate_min_max(cls, values):
        if values.get("min_value") >= values.get("max_value"):
            raise MinValueError()
        return values

    @root_validator
    def validate_scores(cls, values):
        # length of scores must be equal to max_value - min_value + 1
        scores = values.get("scores", [])
        if scores:
            if len(scores) != values.get("max_value") - values.get("min_value") + 1:
                raise InvalidScoreLengthError()
        return values


class NumberSelectionValues(PublicModel):
    min_value: NonNegativeInt = Field(default=0)
    max_value: NonNegativeInt = Field(default=100)

    @root_validator
    def validate_min_max(cls, values):
        if values.get("min_value") >= values.get("max_value"):
            raise MinValueError()
        return values


class DrawingValues(PublicModel):
    drawing_example: str | None
    drawing_background: str | None

    @validator("drawing_example", "drawing_background")
    def validate_image(cls, value):
        if value is not None:
            return validate_image(value)
        return value


class SliderRowsValue(SliderValues, PublicModel):
    id: str | None = None
    label: str = Field(..., max_length=100)

    @validator("id")
    def validate_id(cls, value):
        return validate_uuid(value)


class SliderRowsValues(PublicModel):
    rows: list[SliderRowsValue]


class _SingleSelectionOption(PublicModel):
    id: str | None = None
    text: str = Field(..., max_length=100)
    image: str | None = None
    tooltip: str | None = None

    @validator("image")
    def validate_image(cls, value):
        if value is not None:
            return validate_image(value)
        return value

    @validator("id")
    def validate_id(cls, value):
        return validate_uuid(value)


class _SingleSelectionRow(PublicModel):
    id: str | None = None
    row_name: str = Field(..., max_length=100)
    row_image: str | None = None
    tooltip: str | None = None

    @validator("row_image")
    def validate_image(cls, value):
        if value is not None:
            return validate_image(value)
        return value

    @validator("id")
    def validate_id(cls, value):
        return validate_uuid(value)


class _SingleSelectionDataOption(PublicModel):
    option_id: str
    score: int | None = None
    alert: str | None = None
    value: int | None = None


class _SingleSelectionDataRow(PublicModel):
    row_id: str
    options: list[_SingleSelectionDataOption]

    @validator("options")
    def validate_options(cls, value):
        return validate_options_value(value)


class SingleSelectionRowsValues(PublicModel):
    rows: list[_SingleSelectionRow]
    options: list[_SingleSelectionOption]
    data_matrix: list[_SingleSelectionDataRow] | None = None

    @validator("data_matrix")
    def validate_data_matrix(cls, value, values):
        if value is not None:
            if len(value) != len(values["rows"]):
                raise InvalidDataMatrixError()
            for row in value:
                if len(row.options) != len(values["options"]):
                    raise InvalidDataMatrixByOptionError()
        return value


class MultiSelectionRowsValues(SingleSelectionRowsValues, PublicModel):
    pass


class AudioValues(PublicModel):
    max_duration: NonNegativeInt = 300


class AudioPlayerValues(PublicModel):
    file: str | None = Field(default=None)


ResponseValueConfigOptions = [
    TextValues,
    SingleSelectionValues,
    MultiSelectionValues,
    SliderValues,
    NumberSelectionValues,
    TimeRangeValues,
    GeolocationValues,
    DrawingValues,
    PhotoValues,
    VideoValues,
    DateValues,
    SliderRowsValues,
    SingleSelectionRowsValues,
    MultiSelectionRowsValues,
    AudioValues,
    AudioPlayerValues,
    MessageValues,
    TimeValues,
    FlankerValues,
    StabilityTrackerValues,
    ABTrailsValues,
]


ResponseValueConfig = (
    SingleSelectionValues
    | MultiSelectionValues
    | SliderValues
    | NumberSelectionValues
    | DrawingValues
    | SliderRowsValues
    | SingleSelectionRowsValues
    | MultiSelectionRowsValues
    | AudioValues
    | AudioPlayerValues
    | TimeValues
)


def validate_options_value(options):
    # if value inside options is None, set it to max_value + 1
    for option in options:
        if option.value is None:
            option.value = (
                max(
                    [option.value if option.value is not None else -1 for option in options],
                    default=-1,
                )
                + 1
            )

    return options


def validate_none_option_flag(options):
    none_option_counter = 0

    for option in options:
        if option.is_none_above:
            none_option_counter += 1

    if none_option_counter > 1:
        raise MultiSelectNoneOptionError()

    return options
