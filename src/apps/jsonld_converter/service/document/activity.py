import asyncio
from copy import deepcopy
from typing import Type

from apps.jsonld_converter.domain import LdActivityCreate
from apps.jsonld_converter.errors import JsonLDNotSupportedError
from apps.jsonld_converter.service.document.field import (
    ReproFieldBase,
    ReproFieldText,
    ReproFieldRadio,
    ReproFieldSlider,
    ReproFieldSliderStacked,
    ReproFieldPhoto,
    ReproFieldVideo,
    ReproFieldAudio,
    ReproFieldDrawing,
    ReproFieldMessage,
    ReproFieldTimeRange,
    ReproFieldDate,
    ReproFieldGeolocation,
    ReproFieldAge,
    ReproFieldRadioStacked,
    ReproFieldAudioStimulus,
)
from apps.jsonld_converter.service.document.base import (
    LdDocumentBase,
    ContainsNestedMixin,
    CommonFieldsMixin,
    LdKeyword,
)
from apps.shared.domain import InternalModel


class ReproActivity(LdDocumentBase, ContainsNestedMixin, CommonFieldsMixin):
    ld_pref_label: str | None = None
    ld_alt_label: str | None = None
    ld_description: dict[str, str] | None = None
    ld_about: dict[str, str] | None = None
    ld_schema_version: str | None = None
    ld_version: str | None = None
    ld_image: str | None = None
    ld_splash: str | None = None
    ld_is_vis: str | bool | None = None
    ld_is_reviewer: bool | None = None
    ld_is_one_page: bool | None = None

    properties: dict
    nested_by_order: list[LdDocumentBase] | None = None

    extra: dict | None = None
    is_skippable: bool = False
    is_back_disabled: bool = False

    @classmethod
    def supports(cls, doc: dict) -> bool:
        ld_types = [
            'reproschema:Activity',
            *cls.attr_processor.resolve_key('reproschema:Activity')
        ]
        return cls.attr_processor.first(doc.get(LdKeyword.type)) in ld_types

    @classmethod
    def get_supported_types(cls) -> list[Type[LdDocumentBase]]:
        return [ReproFieldText, ReproFieldRadio, ReproFieldSlider, ReproFieldSliderStacked, ReproFieldPhoto,
                ReproFieldVideo, ReproFieldAudio, ReproFieldDrawing, ReproFieldMessage, ReproFieldTimeRange,
                ReproFieldDate, ReproFieldGeolocation, ReproFieldAge, ReproFieldRadioStacked, ReproFieldAudioStimulus]

    async def load(self, doc: dict, base_url: str | None = None):
        await super().load(doc, base_url)

        processed_doc: dict = deepcopy(self.doc_expanded)
        self.ld_version = self._get_ld_version(processed_doc)
        self.ld_schema_version = self._get_ld_schema_version(processed_doc)
        self.ld_pref_label = self._get_ld_pref_label(processed_doc)
        self.ld_alt_label = self._get_ld_alt_label(processed_doc)
        self.ld_description = self._get_ld_description(processed_doc, drop=True)
        self.ld_about = self._get_ld_about(processed_doc, drop=True)
        self.ld_is_vis = self.attr_processor.get_attr_value(processed_doc, 'reproschema:isVis')
        self.ld_is_reviewer = self.attr_processor.get_attr_value(processed_doc, 'reproschema:isReviewerActivity')
        self.ld_is_one_page = self.attr_processor.get_attr_value(processed_doc, 'reproschema:isOnePageAssessment')

        allow_list = self.attr_processor.get_attr_list(processed_doc, 'reproschema:allow')
        if allow_list:
            self.is_skippable = self._is_skippable(allow_list)
            self.is_back_disabled = self._is_back_disabled(allow_list)

        self.properties = self._get_ld_properties_formatted(processed_doc)
        self.nested_by_order = await self._get_nested_items(processed_doc)

        self._load_extra(processed_doc)

    async def _get_nested_items(self, doc: dict, drop=False):
        if items := self.attr_processor.get_attr_list(doc, 'reproschema:order', drop=drop):
            nested = await asyncio.gather(*[self._load_nested_doc(item) for item in items])
            return [node for node in nested if node]

    async def _load_nested_doc(self, doc: dict):
        try:
            node = await self.load_supported_document(doc, self.base_url)
            # override from properties
            if node.ld_id in self.properties:
                for prop, val in self.properties[node.ld_id].items():
                    if val is not None and hasattr(node, prop):
                        setattr(node, prop, val)
            return node
        except JsonLDNotSupportedError:
            return None  # TODO

    def _load_extra(self, doc: dict):
        if self.extra is None:
            self.extra = {}
        for k, v in doc.items():
            self.extra[k] = v

    def export(self) -> InternalModel:
        items = [nested.export() for nested in self.nested_by_order if isinstance(nested, ReproFieldBase)]
        return LdActivityCreate(
            name=self.ld_pref_label or self.ld_alt_label,
            description=self.ld_description or {},
            splash_screen=self.ld_splash or '',
            show_all_at_once=bool(self.ld_is_one_page),
            is_skippable=self.is_skippable,
            is_reviewable=bool(self.ld_is_reviewer),
            response_is_editable=bool(self.is_back_disabled),  # TODO why back disabled?
            is_hidden=self.ld_is_vis is False,
            image=self.ld_image or '',
            items=items,
            extra_fields=self.extra
        )