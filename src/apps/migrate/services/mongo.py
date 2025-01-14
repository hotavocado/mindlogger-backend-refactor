import datetime
import hashlib
import json
import os
import uuid
from functools import partial
from typing import List, Set, Tuple, Any, Literal

from bson.objectid import ObjectId

from Cryptodome.Cipher import AES
from pymongo import ASCENDING, MongoClient
from pymongo.database import Database
from sqlalchemy.types import String
from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType

from apps.applets.domain.base import Encryption
from apps.girderformindlogger.models.account_profile import AccountProfile
from apps.girderformindlogger.models.activity import Activity
from apps.girderformindlogger.models.applet import Applet
from apps.girderformindlogger.models.folder import Folder as FolderModel
from apps.girderformindlogger.models.profile import Profile
from apps.girderformindlogger.models.user import User
from apps.girderformindlogger.models.item import Item
from apps.girderformindlogger.utility import jsonld_expander
from apps.jsonld_converter.dependencies import (
    get_context_resolver,
    get_document_loader,
    get_jsonld_model_converter,
)
from apps.migrate.data_description.applet_user_access import AppletUserDAO
from apps.migrate.data_description.folder_dao import FolderAppletDAO, FolderDAO
from apps.migrate.data_description.library_dao import (
    LibraryDao,
    ThemeDao,
    AppletTheme,
)
from apps.migrate.data_description.public_link import PublicLinkDao
from apps.migrate.data_description.user_pins import UserPinsDAO
from apps.migrate.exception.exception import (
    EmptyAppletException,
    FormatldException,
)
from apps.migrate.services.applet_versions import (
    CONTEXT,
    content_to_jsonld,
    get_versions_from_content,
)
from apps.migrate.utilities import (
    convert_role,
    migration_log,
    mongoid_to_uuid,
    uuid_to_mongoid,
)
from apps.shared.domain.base import InternalModel, PublicModel
from apps.shared.encryption import get_key
from apps.workspaces.domain.constants import Role
from apps.shared.version import INITIAL_VERSION


enc = StringEncryptedType(key=get_key())


def decrypt(data):
    aes_key = bytes(str(os.getenv("MONGO__AES_KEY")).encode("utf-8"))
    max_count = 4

    try:
        cipher = AES.new(aes_key, AES.MODE_EAX, nonce=data[-32:-16])
        plaintext = cipher.decrypt(data[:-32])
        cipher.verify(data[-16:])
    except Exception:
        return None

    txt = plaintext.decode("utf-8")
    length = int(txt[-max_count:])

    return txt[:length]


def patch_broken_applet_versions(applet_id: str, applet_ld: dict) -> dict:
    broken_conditional_date_item = [
        "62a8d7d7b90b7f2ba9e1aa43",
    ]
    if applet_id in broken_conditional_date_item:
        for property in applet_ld["reprolib:terms/order"][0]["@list"][0][
            "reprolib:terms/addProperties"
        ]:
            if property["reprolib:terms/isAbout"][0]["@id"] == "EPDSMotherDOB":
                property["reprolib:terms/isVis"][0]["@value"] = True

    broken_item_flow_order = ["613f6eba6401599f0e495dc5"]
    if applet_id in broken_item_flow_order:
        for activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            for prop in activity["reprolib:terms/addProperties"]:
                prop["reprolib:terms/isVis"][0]["@value"] = True
        if applet_ld["schema:version"][0]["@value"] == "1.2.2":
            applet_ld["reprolib:terms/order"][0]["@list"][0][
                "reprolib:terms/order"
            ][0]["@list"].pop(26)
            applet_ld["reprolib:terms/order"][0]["@list"][0][
                "reprolib:terms/addProperties"
            ].pop(26)

    broken_applet_versions = [
        "6201cc26ace55b10691c0814",
        "6202734eace55b10691c0fc4",
        "623b757b5197b9338bdae930",
        "623cd7ee5197b9338bdaf218",
        "623e26175197b9338bdafbf0",
        "627be9f60a62aa47962269b7",
        "62f2ce4facd35a39e99b5e92",
        "634715115cb70043112196ba",
        "63ca78b7b71996780cdf1f16",
        "63dd2d4eb7199623ac5002e4",
        "6202738aace55b10691c101d",
        "620eb401b0b0a55f680dd5f5",
        "6210202db0b0a55f680de1a5",
        "63ebcec2601cdc0fee1f3d42",
        "63ec1498601cdc0fee1f47d2",
    ]
    if applet_id in broken_applet_versions:
        for activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            for property in activity["reprolib:terms/addProperties"]:
                property["reprolib:terms/isVis"] = [{"@value": True}]

    broken_v1_trails_activity_type = [
        "6276c0fd0a62aa105607838c",
    ]
    if applet_id in broken_v1_trails_activity_type:
        for _index, _activity in enumerate(
            applet_ld["reprolib:terms/order"][0]["@list"]
        ):
            if _activity["@type"][0] == "reprolib:schemas/ABTrails":
                _activity["@type"][0] = "reprolib:schemas/Activity"
                _activity["reprolib:terms/activityType"] = [
                    {
                        "@type": "http://www.w3.org/2001/XMLSchema#string",
                        "@value": "TRAILS_MOBILE",
                    }
                ]

    broken_applet_abtrails = [
        "62768ff20a62aa1056078093",
        "62d06045acd35a1054f106f6",
        "64946e208819c1120b4f9271",
        "61f3423962485608c74c1f45",
    ]
    if (
        applet_id == "62768ff20a62aa1056078093"
        and applet_ld["schema:version"][0]["@value"] == "1.0.4"
    ):
        applet_ld["reprolib:terms/order"][0]["@list"].pop(4)

    no_ids_flanker_map = {
        "<<<<<": "left-con",
        "<<><<": "right-inc",
        ">><>>": "left-inc",
        ">>>>>": "right-con",
        "--<--": "left-neut",
        "-->--": "right-neut",
    }
    if applet_id in broken_applet_abtrails:
        for _activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            if _activity["@id"] in ["Flanker_360", "flanker_schema"]:
                for _item in _activity["reprolib:terms/order"][0]["@list"]:
                    if "reprolib:terms/inputs" in _item:
                        for _intput in _item["reprolib:terms/inputs"]:
                            if "schema:itemListElement" in _intput:
                                for _el in _intput["schema:itemListElement"]:
                                    if (
                                        "@id" not in _el
                                        and "schema:image" in _el
                                    ):
                                        _el["@id"] = no_ids_flanker_map[
                                            _el["schema:image"]
                                        ]
                        _item["reprolib:terms/inputs"].append(
                            {
                                "@type": ["http://schema.org/Text"],
                                "http://schema.org/name": [
                                    {"@language": "en", "@value": "blockType"}
                                ],
                                "http://schema.org/value": [
                                    {"@language": "en", "@value": "practice"}
                                ],
                            }
                        )
                        _item["reprolib:terms/inputs"].append(
                            {
                                "@type": ["http://schema.org/ItemList"],
                                "schema:itemListElement": [
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 1",
                                            }
                                        ],
                                        "schema:value": [{"@value": 0}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 2",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 3",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 4",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 5",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                ],
                                "schema:name": [
                                    {"@language": "en", "@value": "blocks"}
                                ],
                                "schema:numberOfItems": [{"@value": 5}],
                            }
                        )
                        _item["reprolib:terms/inputs"].append(
                            {
                                "schema:itemListElement": [
                                    {
                                        "schema:image": "",
                                        "schema:name": [
                                            {"@language": "en", "@value": "<"}
                                        ],
                                        "schema:value": [{"@value": 0}],
                                    },
                                    {
                                        "schema:image": "",
                                        "schema:name": [
                                            {"@language": "en", "@value": ">"}
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                ],
                                "schema:name": [
                                    {"@language": "en", "@value": "buttons"}
                                ],
                            }
                        )

    applet_ld = patch_prize_activity(applet_id, applet_ld)
    if applet_id not in broken_applet_versions:
        patch_broken_visability_for_applet(applet_ld)

    broken_item_flow = [
        "6522a4753c36ce0d4d6cda4d",
    ]
    if applet_id in broken_item_flow:
        applet_ld["reprolib:terms/order"][0]["@list"][0][
            "reprolib:terms/addProperties"
        ][5]["reprolib:terms/isVis"][0] = {"@value": True}

    return applet_ld


def patch_broken_applets(
    applet_id: str, applet_ld: dict, applet_mongo: dict
) -> tuple[dict, dict]:
    broken_report_condition_item = [
        "6358265b5cb700431121f033",
        "6358267b5cb700431121f143",
        "63696d4a52ea02101467671d",
        "63696e7c52ea021014676784",
    ]
    if applet_id in broken_report_condition_item:
        for report in applet_ld["reprolib:terms/order"][0]["@list"][0][
            "reprolib:terms/reports"
        ][0]["@list"]:
            if report["@id"] == "sumScore_suicidalorselfinjury":
                report["reprolib:terms/conditionals"][0]["@list"][1][
                    "reprolib:terms/printItems"
                ][0]["@list"] = []
                report["reprolib:terms/conditionals"][0]["@list"][0][
                    "reprolib:terms/printItems"
                ][0]["@list"] = []

    broken_conditional_date_item = [
        "62a8d7d7b90b7f2ba9e1aa43",
        "62a8d7e5b90b7f2ba9e1aab3",
    ]
    if applet_id in broken_conditional_date_item:
        for property in applet_ld["reprolib:terms/order"][0]["@list"][0][
            "reprolib:terms/addProperties"
        ]:
            if property["reprolib:terms/isAbout"][0]["@id"] == "EPDSMotherDOB":
                property["reprolib:terms/isVis"][0]["@value"] = False

    broken_item_flow = [
        "6522a4753c36ce0d4d6cda4d",
    ]
    if applet_id in broken_item_flow:
        applet_ld["reprolib:terms/order"][0]["@list"][0][
            "reprolib:terms/addProperties"
        ][5]["reprolib:terms/isVis"][0] = {"@value": False}

    broken_activity_order = [
        "63d3d579b71996780cdf409a",
        "63f36719601cdc5212d58eae",
    ]
    if applet_id in broken_activity_order:
        duplicate_activity = None
        for _index, activity in enumerate(
            applet_ld["reprolib:terms/order"][0]["@list"]
        ):
            if (
                activity["_id"] == "activity/63d3d4eeb71996780cdf3e97"
                or activity["_id"] == "activity/63f36646601cdc5212d58cbe"
            ):
                duplicate_activity = _index

        if duplicate_activity:
            applet_ld["reprolib:terms/order"][0]["@list"].pop(
                duplicate_activity
            )

    broken_applets = [
        # broken conditional logic [object object]  in main applet
        "6202738aace55b10691c101d",
        "620eb401b0b0a55f680dd5f5",
        "6210202db0b0a55f680de1a5",
    ]
    if applet_id in broken_applets:
        for activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            for property in activity["reprolib:terms/addProperties"]:
                if type(
                    property["reprolib:terms/isVis"][0]["@value"]
                ) == str and (
                    "[object object]"
                    in property["reprolib:terms/isVis"][0]["@value"]
                ):
                    property["reprolib:terms/isVis"] = [{"@value": True}]

    # "623ce52a5197b9338bdaf4b6",  # needs to be renamed in cache,version as well
    broken_applet_name = [
        "623ce52a5197b9338bdaf4b6",
        "64934a618819c1120b4f8e34",
    ]
    if applet_id in broken_applet_name:
        applet_ld["displayName"] = str(applet_ld["displayName"]) + str("(1)")
        applet_ld["http://www.w3.org/2004/02/skos/core#prefLabel"] = applet_ld[
            "displayName"
        ]
    broken_applet_version = "623ce52a5197b9338bdaf4b6"
    if applet_id == broken_applet_version:
        applet_mongo["meta"]["applet"]["version"] = str("2.6.40")

    broken_conditional_logic = [
        "63ebcec2601cdc0fee1f3d42",
        "63ec1498601cdc0fee1f47d2",
    ]
    if applet_id in broken_conditional_logic:
        for activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            for property in activity["reprolib:terms/addProperties"]:
                if (
                    property["reprolib:terms/isAbout"][0]["@id"]
                    == "IUQ_Wd_Social_Device"
                ):
                    property["reprolib:terms/isVis"] = [{"@value": False}]

    repo_replacements = [
        (
            "mtg137/Stability_tracker_applet_touch",
            "ChildMindInstitute/stability_touch_applet_schema",
        ),
        (
            "mtg137/Stability_tracker_applet",
            "ChildMindInstitute/stability_tilt_applet_schema",
        ),
        (
            "ChildMindInstitute/A-B-Trails",
            "ChildMindInstitute/mindlogger-trails-task",
        ),
    ]
    for what, repl in repo_replacements:
        if "schema:image" in applet_ld and what in applet_ld["schema:image"]:
            contents = json.dumps(applet_ld)
            contents = contents.replace(what, repl)
            applet_ld = json.loads(contents)

    # fix duplicated names for stability activity items in prefLabel
    duplications = [
        (
            "stability_schema",
            [
                "Stability Tracker",
                "Stability tracker instructions",
            ],
        ),
        (
            "flanker_schema",
            [
                "Visual Stimulus Response",
                "Visual Stimulus Response instructions",
            ],
        ),
        (
            "Flanker_360",
            [
                "Visual Stimulus Response",
                "Visual Stimulus Response instructions",
            ],
        ),
    ]
    key = "http://www.w3.org/2004/02/skos/core#prefLabel"
    for stability_activity in applet_ld["reprolib:terms/order"][0]["@list"]:
        for activity_name, item_label in duplications:
            if stability_activity["@id"] == activity_name:
                for stability_item in stability_activity[
                    "reprolib:terms/order"
                ][0]["@list"]:
                    if (
                        key in stability_item
                        and stability_item[key][0]["@value"] in item_label
                    ):
                        stability_item[key][0]["@value"] = (
                            stability_item[key][0]["@value"]
                            + "_"
                            + stability_item["@id"]
                        )

    broken_conditional_logic_naming = [
        "64e7af5e22d81858d681de92",
        "633ecc1ab7ee9765ba54452d",
        "64ec703122d81858d681eb27",
    ]
    if applet_id in broken_conditional_logic_naming:
        for _activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            for _report in _activity["reprolib:terms/reports"][0]["@list"]:
                _report = fix_spacing_in_report(_report)
                if "reprolib:terms/conditionals" in _report:
                    for _conditional in _report["reprolib:terms/conditionals"][
                        0
                    ]["@list"]:
                        _conditional = fix_spacing_in_report(_conditional)

    broken_conditional_non_existing_slider2_item = ["64dce2d622d81858d6819f13"]
    if applet_id in broken_conditional_non_existing_slider2_item:
        for _activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            for _report in _activity["reprolib:terms/reports"][0]["@list"]:
                key = "reprolib:terms/printItems"
                if key in _report:
                    _report[key][0]["@list"] = [
                        print_item
                        for print_item in _report[key][0]["@list"]
                        if print_item["@value"] != "Slider2"
                    ]

    broken_conditional_non_existing_items = ["633ecc1ab7ee9765ba54452d"]
    if applet_id in broken_conditional_non_existing_items:
        for _activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            if (
                _activity["@id"]
                == "NIH Toolbox: Perceived Stress (SR 18+1) (1)"
            ):
                for _report in _activity["reprolib:terms/reports"][0]["@list"]:
                    key = "reprolib:terms/printItems"
                    if key in _report:
                        _report[key][0]["@list"] = [
                            print_item
                            for print_item in _report[key][0]["@list"]
                            if print_item["@value"]
                            not in [
                                "nihps_sr18_q05",
                                "nihps_sr18_q06",
                                "nihps_sr18_q07",
                                "nihps_sr18_q08",
                            ]
                        ]
                    if _report["@id"] in [
                        "averageScore_score_2",
                        "percentScore_score_3",
                    ]:
                        _report.pop("reprolib:terms/jsExpression")

    duplicated_activity_names = ["640b239b601cdc5212d63e75"]
    if applet_id in duplicated_activity_names:
        current_names = []
        current_names_indexes = []
        for _index, _activity in enumerate(
            applet_ld["reprolib:terms/order"][0]["@list"]
        ):
            if _activity["@id"] in current_names:
                current_names_indexes.append(_index)
            current_names.append(_activity["@id"])
        if current_names_indexes:
            current_names_indexes.sort(reverse=True)
            for _index in current_names_indexes:
                applet_ld["reprolib:terms/order"][0]["@list"].pop(_index)

    broken_v1_trails_activity_type = [
        "6276c0fd0a62aa105607838c",
    ]
    if applet_id in broken_v1_trails_activity_type:
        for _index, _activity in enumerate(
            applet_ld["reprolib:terms/order"][0]["@list"]
        ):
            if _activity["@type"][0] == "reprolib:schemas/ABTrails":
                _activity["@type"][0] = "reprolib:schemas/Activity"
                _activity["reprolib:terms/activityType"] = [
                    {
                        "@type": "http://www.w3.org/2001/XMLSchema#string",
                        "@value": "TRAILS_MOBILE",
                    }
                ]

    no_ids_flanker_map = {
        "<<<<<": "left-con",
        "<<><<": "right-inc",
        ">><>>": "left-inc",
        ">>>>>": "right-con",
        "--<--": "left-neut",
        "-->--": "right-neut",
    }
    no_ids_flanker_buttons = [
        "62768ff20a62aa1056078093",
        "64946e208819c1120b4f9271",
        "61f3423962485608c74c1f45",
    ]
    if applet_id in no_ids_flanker_buttons:
        for _activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            if _activity["@id"] in ["Flanker_360", "flanker_schema"]:
                for _item in _activity["reprolib:terms/order"][0]["@list"]:
                    if "reprolib:terms/inputs" in _item:
                        for _intput in _item["reprolib:terms/inputs"]:
                            if "schema:itemListElement" in _intput:
                                for _el in _intput["schema:itemListElement"]:
                                    if (
                                        "@id" not in _el
                                        and "schema:image" in _el
                                    ):
                                        _el["@id"] = no_ids_flanker_map[
                                            _el["schema:image"]
                                        ]
                        _item["reprolib:terms/inputs"].append(
                            {
                                "@type": ["http://schema.org/Text"],
                                "http://schema.org/name": [
                                    {"@language": "en", "@value": "blockType"}
                                ],
                                "http://schema.org/value": [
                                    {"@language": "en", "@value": "practice"}
                                ],
                            }
                        )
                        _item["reprolib:terms/inputs"].append(
                            {
                                "@type": ["http://schema.org/ItemList"],
                                "schema:itemListElement": [
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 1",
                                            }
                                        ],
                                        "schema:value": [{"@value": 0}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 2",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 3",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 4",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                    {
                                        "reprolib:terms/order": [
                                            {
                                                "@list": [
                                                    {"@id": "left-con"},
                                                    {"@id": "right-con"},
                                                    {"@id": "left-inc"},
                                                    {"@id": "right-inc"},
                                                    {"@id": "left-neut"},
                                                    {"@id": "right-neut"},
                                                ]
                                            }
                                        ],
                                        "schema:name": [
                                            {
                                                "@language": "en",
                                                "@value": "Block 5",
                                            }
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                ],
                                "schema:name": [
                                    {"@language": "en", "@value": "blocks"}
                                ],
                                "schema:numberOfItems": [{"@value": 5}],
                            }
                        )
                        _item["reprolib:terms/inputs"].append(
                            {
                                "schema:itemListElement": [
                                    {
                                        "schema:image": "",
                                        "schema:name": [
                                            {"@language": "en", "@value": "<"}
                                        ],
                                        "schema:value": [{"@value": 0}],
                                    },
                                    {
                                        "schema:image": "",
                                        "schema:name": [
                                            {"@language": "en", "@value": ">"}
                                        ],
                                        "schema:value": [{"@value": 1}],
                                    },
                                ],
                                "schema:name": [
                                    {"@language": "en", "@value": "buttons"}
                                ],
                            }
                        )

    applet_ld = patch_prize_activity(applet_id, applet_ld)

    patch_broken_visability_for_applet(applet_ld)
    return applet_ld, applet_mongo


def patch_prize_activity(applet_id: str, applet_ld: dict) -> dict:
    # Prize activity
    if applet_id == "613f7a206401599f0e495e0a":
        for _activity in applet_ld["reprolib:terms/order"][0]["@list"]:
            if _activity["@id"] == "PrizeActivity":
                for _item in _activity["reprolib:terms/order"][0]["@list"]:
                    if _item["@id"] == "PrizeSelection":
                        _item["reprolib:terms/inputType"][0][
                            "@value"
                        ] = "radio"

    return applet_ld


def fix_spacing_in_report(_report: dict) -> dict:
    if "@id" in _report:
        _report["@id"] = _report["@id"].replace(" ", "_")
    if "reprolib:terms/isVis" in _report:
        _report["reprolib:terms/isVis"][0]["@value"] = (
            _report["reprolib:terms/isVis"][0]["@value"]
            .replace(
                "averageScore_average_less than",
                "averageScore_average_less_than",
            )
            .replace(
                "averageScore_average_greater than",
                "averageScore_average_greater_than",
            )
            .replace(
                "averageScore_average_equal to",
                "averageScore_average_equal_to",
            )
            .replace(
                "averageScore_average_is not equal to",
                "averageScore_average_is_not_equal_to",
            )
            .replace(
                "averageScore_average_outside of",
                "averageScore_average_outside_of",
            )
        )

    return _report


def patch_broken_visability_for_applet(applet: dict) -> None:
    def get_isvis(entity: dict) -> Any | Literal[False]:
        term = entity.get("reprolib:terms/isVis", [])
        # Return False if there is no isVis term, to make patch process more
        # consistent (False and missing value for old UI have the same logic)
        return term[0]["@value"] if term else False

    def set_isvis(entity: dict, value: bool) -> None:
        entity["reprolib:terms/isVis"] = [{"@value": value}]

    acitivity_id_isvis_map = {}
    for activity in applet["reprolib:terms/order"][0]["@list"]:
        incorrect_vis = get_isvis(activity)
        item_id_isvis_map = {}
        # For each activity which has isVis bool type invert isVis
        # and add new value to the map for futher updating addProperties
        if isinstance(incorrect_vis, bool):
            set_isvis(activity, not incorrect_vis)
            acitivity_id_isvis_map[activity["@id"]] = get_isvis(activity)

        # For each item which has isVis bool type invert isVis
        # and add new value to the map for futher updating addProperties of
        # activity
        for item in activity["reprolib:terms/order"][0]["@list"]:
            incorrect_vis = get_isvis(item)
            if isinstance(incorrect_vis, bool):
                set_isvis(item, not incorrect_vis)
                item_id_isvis_map[item["@id"]] = get_isvis(item)
        # update addProperties of applet if they exist
        # set correct value from map
        for add_prop in activity.get("reprolib:terms/addProperties", []):
            item_id = add_prop["reprolib:terms/isAbout"][0]["@id"]
            if item_id in item_id_isvis_map:
                if isinstance(
                    add_prop["reprolib:terms/isVis"][0]["@value"], bool
                ):
                    set_isvis(add_prop, item_id_isvis_map[item_id])

    # update addProperties of applet if they exist, set correct value from map
    for add_prop in applet.get("reprolib:terms/addProperties", []):
        activity_id = add_prop["reprolib:terms/isAbout"][0]["@id"]
        if activity_id in acitivity_id_isvis_map:
            if isinstance(add_prop["reprolib:terms/isVis"][0]["@value"], bool):
                set_isvis(add_prop, acitivity_id_isvis_map[activity_id])


def patch_library_version(applet_id: str, version: str) -> str:
    if applet_id == "61f42e5c62485608c74c2a7e":
        version = "4.2.42"
    elif applet_id == "623b81c45197b9338bdaea22":
        version = "2.11.39"

    return version


class Mongo:
    def __init__(self) -> None:
        # Setup MongoDB connection
        # uri = f"mongodb://{os.getenv('MONGO__USER')}:{os.getenv('MONGO__PASSWORD')}@{os.getenv('MONGO__HOST')}/{os.getenv('MONGO__DB')}"  # noqa: E501
        uri = f"mongodb://{os.getenv('MONGO__HOST')}"  # noqa: E501  {os.getenv('MONGO__USER')}:{os.getenv('MONGO__PASSWORD')}@
        self.client = MongoClient(uri, 27017)  # uri
        self.db = self.client[os.getenv("MONGO__DB", "mindlogger")]

    @staticmethod
    async def get_converter_result(schema) -> InternalModel | PublicModel:
        document_loader = get_document_loader()
        context_resolver = get_context_resolver(document_loader)
        converter = get_jsonld_model_converter(
            document_loader, context_resolver
        )

        return await converter.convert(schema)

    def close_connection(self):
        self.client.close()

    def get_users(self) -> list[dict]:
        collection = self.db["user"]
        users = collection.find(
            {},
            {
                "_id": 1,
                "email": 1,
                "firstName": 1,
                "lastName": 1,
                "salt": 1,
                "created": 1,
                "email_encrypted": 1,
            },
        )

        count = 0
        total_documents = 0
        encrypted_count = 0
        results = []
        email_hashes = []

        for user in users:
            first_name = decrypt(user.get("firstName"))
            if not first_name:
                first_name = "-"
            elif len(first_name) >= 50:
                first_name = first_name[:49]
            first_name = enc.process_bind_param(first_name, String)

            last_name = decrypt(user.get("lastName"))
            if not last_name:
                last_name = "-"
            elif len(last_name) >= 50:
                last_name = last_name[:49]
            last_name = enc.process_bind_param(last_name, String)

            if user.get("email"):
                if not user.get("email_encrypted"):
                    email_hash = hashlib.sha224(
                        user.get("email").encode("utf-8")
                    ).hexdigest()
                    if "@" in user.get("email"):
                        email_aes_encrypted = enc.process_bind_param(
                            user.get("email"), String
                        )
                        encrypted_count += 1
                    else:
                        email_aes_encrypted = None
                elif (
                    user.get("email_encrypted")
                    and len(user.get("email")) == 56
                ):
                    email_hash = user.get("email")
                    email_aes_encrypted = None
                else:
                    total_documents += 1
                    continue

                if email_hash not in email_hashes:
                    email_hashes.append(email_hash)
                    results.append(
                        {
                            "id_": user.get("_id"),
                            "email": email_hash,
                            "hashed_password": user.get("salt"),
                            "first_name": first_name,
                            "last_name": last_name,
                            "created_at": user.get("created"),
                            "email_aes_encrypted": email_aes_encrypted,
                        }
                    )
                    count += 1
            total_documents += 1
        migration_log.info(
            f"Total Users Documents - {total_documents}, "
            f"Successfully prepared for migration - {count}, "
            f"Users with email_aes_encrypted - {encrypted_count}"
        )

        return results

    def get_users_workspaces(self, users_ids: list[ObjectId]) -> list[dict]:
        collection = self.db["accountProfile"]
        users_workspaces = collection.find(
            {
                "$expr": {"$eq": ["$accountId", "$_id"]},
                "userId": {"$in": users_ids},
            }
        )

        count = 0
        results = []

        for user_workspace in users_workspaces:
            workspace_name = user_workspace.get("accountName")
            if len(workspace_name) >= 100:
                workspace_name = workspace_name[:99]
            workspace_name = enc.process_bind_param(workspace_name, String)
            results.append(
                {
                    "id_": user_workspace.get("_id"),
                    "user_id": user_workspace.get("userId"),
                    "workspace_name": workspace_name,
                }
            )
            count += 1
        migration_log.info(
            f"Successfully prepared workspaces for migration - {count}"
        )

        return results

    def patch_cloned_activities_order(
        self, applet_format: dict, applet: dict
    ) -> dict:
        """
        This patches a bug in the legacy system where after an applet is duplicated the activities order still
        refers to the original records.
        If it's the case, it will remove those and replace with the cloned applet activities IDs.
        """

        # patch activity of applet with id=65155ba49932fa109e82de99
        if applet["_id"] == ObjectId("65155ba49932fa109e82de99"):
            _broken_activity_index = None
            for _index, _activity in enumerate(
                applet_format["applet"]["reprolib:terms/order"][0]["@list"]
            ):
                if _activity["@id"] == "617a62dba463200ebc8506fc":
                    _broken_activity_index = _index
                    break
            if _broken_activity_index is not None:
                applet_format["applet"]["reprolib:terms/order"][0]["@list"][
                    _broken_activity_index
                ] = {"@id": "65155aa49932fa109e82dbde"}

        original_id = applet["duplicateOf"]
        original = Applet().findOne(query={"_id": original_id})
        if original:
            original_format = jsonld_expander.formatLdObject(
                original, "applet", refreshCache=False, reimportFromUrl=False
            )
        else:
            original_format = None

        if (
            original_format
            and "applet" in original_format
            and "reprolib:terms/order" in original_format["applet"]
        ):
            act_blacklist = []
            for _orig_act in original_format["applet"]["reprolib:terms/order"][
                0
            ]["@list"]:
                if ObjectId.is_valid(_orig_act["@id"]):
                    act_blacklist.append(_orig_act["@id"])
            for _key, _activity in original_format["activities"].items():
                act_blacklist.append(str(_activity))

            # exclude duplicates of activities
            all_activities = []
            for _orig_act in applet_format["applet"]["reprolib:terms/order"][
                0
            ]["@list"]:
                try:
                    all_activities.append(ObjectId(_orig_act["@id"]))
                except Exception:
                    continue
            for _key, _activity in applet_format["activities"].items():
                try:
                    all_activities.append(ObjectId(_activity))
                except Exception:
                    continue
            all_activities = list(
                FolderModel().find(query={"_id": {"$in": all_activities}})
            )
            for _activity in all_activities:
                if "duplicateOf" in _activity:
                    act_blacklist.append(str(_activity["duplicateOf"]))
                if (
                    applet["created"] - _activity["created"]
                ).total_seconds() > 600:
                    act_blacklist.append(str(_activity["_id"]))

            order = applet_format["applet"]["reprolib:terms/order"][0]["@list"]
            order = [
                _act for _act in order if _act["@id"] not in act_blacklist
            ]
            # TODO: exclude from applet_format['activities'] ids from blacklist
            if len(order) == 0:
                order = [
                    {"@id": str(_act)} for _act in applet_format["activities"]
                ]
            applet_format["applet"]["reprolib:terms/order"][0]["@list"] = order

            # add missing acitivity ids in activity list
            # when applet is a duplicate
            for activity in order:
                if ObjectId.is_valid(activity["@id"]):
                    applet_format["activities"][activity["@id"]] = ObjectId(
                        activity["@id"]
                    )

        return applet_format

    def get_applet_repro_schema(self, applet: dict) -> dict:
        applet_format = jsonld_expander.formatLdObject(
            applet, "applet", refreshCache=False, reimportFromUrl=False
        )

        if applet_format is None or applet_format == {}:
            raise FormatldException(
                message="formatLdObject returned empty object"
            )

        if "duplicateOf" in applet:
            applet_format = self.patch_cloned_activities_order(
                applet_format, applet
            )

        if applet_format["activities"] == {}:
            raise FormatldException(
                message="formatLdObject returned empty activities"
            )

        for key, activity in applet_format["activities"].items():
            applet_format["activities"][key] = jsonld_expander.formatLdObject(
                Activity().findOne({"_id": ObjectId(activity)}),
                "activity",
                refreshCache=False,
                reimportFromUrl=False,
            )

        activities_by_id = applet_format["activities"].copy()
        for _key, _activity in activities_by_id.copy().items():
            activity_id = _activity["activity"]["@id"]
            if activity_id not in activities_by_id:
                activities_by_id[activity_id] = _activity.copy()
            activity_name = _activity["activity"][
                "http://www.w3.org/2004/02/skos/core#prefLabel"
            ][0]["@value"]
            if activity_name not in activities_by_id:
                activities_by_id[activity_name] = _activity.copy()

        # setup activity items
        for key, value in activities_by_id.items():
            if "items" not in value:
                migration_log.debug("Warning: activity  %s  has no items", key)
                continue

            activity_items_by_id = value["items"].copy()
            for _key, _item in activity_items_by_id.copy().items():
                if "url" in _item:
                    activity_items_by_id[_item["url"]] = _item.copy()

            activity_object = value["activity"]
            activity_items_objects = []
            for item in activity_object["reprolib:terms/order"][0]["@list"]:
                item_key = item["@id"]
                if item_key in activity_items_by_id:
                    activity_items_objects.append(
                        activity_items_by_id[item_key]
                    )
                else:
                    activity_items_objects.append(item)
                    migration_log.debug(
                        (
                            f"item {item_key} ",
                            "presents in order but absent in activity items. "
                            f"activityId: {activity_object['_id']}",
                        ),
                    )

            activities_by_id[key]["activity"]["reprolib:terms/order"][0][
                "@list"
            ] = activity_items_objects
            activities_by_id[key].pop("items")

        applet = applet_format["applet"]
        activity_objects = []
        # setup activities
        for activity in applet["reprolib:terms/order"][0]["@list"]:
            activity_id = self.find_additional_id(
                list(activities_by_id.keys()), activity["@id"]
            )
            if activity_id:
                activity_objects.append(
                    activities_by_id[activity_id]["activity"]
                )
            else:
                migration_log.debug(
                    "Warning: activity %s presents in order but absent in applet activities.",
                    activity_id,
                )

        applet["reprolib:terms/order"][0]["@list"] = activity_objects

        activity_ids_inside_applet = []
        for activity in activity_objects:
            activity_ids_inside_applet.append(activity["@id"])

        if applet.get("reprolib:terms/activityFlowOrder"):
            activity_flows = applet_format["activityFlows"].copy()
            for _key, _flow in activity_flows.copy().items():
                flow_id = _flow["@id"]
                if flow_id not in activity_flows:
                    activity_flows[flow_id] = _flow.copy()

            activity_flows_fixed = {}
            # setup activity flow items
            for key, activity_flow in activity_flows.items():
                activity_flow_order = []
                for item in activity_flow["reprolib:terms/order"][0]["@list"]:
                    if item["@id"] in activity_ids_inside_applet:
                        activity_flow_order.append(item)
                    else:
                        migration_log.debug(
                            (
                                f"item {item['@id']} "
                                "presents in flow order but absent in applet "
                                "activities. activityFlowId: {key}",
                            ),
                        )
                activity_flow["reprolib:terms/order"][0][
                    "@list"
                ] = activity_flow_order
                activity_flows_fixed[key] = activity_flow

            activity_flow_objects = []

            # setup activity flows
            for flow in applet["reprolib:terms/activityFlowOrder"][0]["@list"]:
                if activity_flows_fixed.get(flow["@id"]):
                    activity_flow_objects.append(
                        activity_flows_fixed[flow["@id"]]
                    )

            applet["reprolib:terms/activityFlowOrder"][0][
                "@list"
            ] = activity_flow_objects
        # add context

        applet["@context"] = CONTEXT["@context"]
        applet["@type"] = CONTEXT["@type"]

        return applet

    def find_additional_id(
        self, activities_ids: list[str], activity_id: str
    ) -> str | None:
        if activity_id in activities_ids:
            return activity_id

        lookup = {
            "ab_trails_v1/ab_trails_v1_schema": "A/B Trails v1.0",
            "ab_trails_v2/ab_trails_v2_schema": "A/B Trails v2.0",
            "Flanker/Flanker_schema": "flanker_schema",
            "Stability/Stability_schema": "stability_schema",
        }
        for _a_id in activities_ids:
            for key, value in lookup.items():
                if key in activity_id and value == _a_id:
                    return _a_id

        # e.g take Flanker_schema from
        # https://raw.github.com/CMI/flanker/master/activities/Flanker/Flanker_schema
        activity_id_from_relative_url = activity_id.split("/").pop()
        for _a_id in activities_ids:
            if (
                activity_id_from_relative_url == _a_id
                or activity_id_from_relative_url.lower() == _a_id.lower()
            ):
                return _a_id

        return None

    async def get_applet(self, applet_id: str) -> dict:
        applet = Applet().findOne({"_id": ObjectId(applet_id)})
        if (
            not applet
            or "applet" not in applet["meta"]
            or applet["meta"]["applet"] == {}
        ):
            raise EmptyAppletException()
        # fetch version
        applet = self.fetch_applet_version(applet)
        ld_request_schema = self.get_applet_repro_schema(applet)
        ld_request_schema, applet = patch_broken_applets(
            applet_id, ld_request_schema, applet
        )
        ld_request_schema = self.preprocess_performance_task(ld_request_schema)
        converted = await self.get_converter_result(ld_request_schema)

        converted.extra_fields["created"] = applet["created"]
        converted.extra_fields["updated"] = applet["updated"]
        converted.extra_fields["creator"] = str(applet.get("creatorId", None))
        converted.extra_fields["version"] = applet["meta"]["applet"].get(
            "version", INITIAL_VERSION
        )
        if "encryption" in applet["meta"]:
            converted.encryption = Encryption(
                public_key=json.dumps(
                    applet["meta"]["encryption"]["appletPublicKey"]
                ),
                prime=json.dumps(applet["meta"]["encryption"]["appletPrime"]),
                base=json.dumps(applet["meta"]["encryption"]["base"]),
                account_id=str(applet["accountId"]),
            )
        converted = self._extract_ids(converted, applet_id)

        return converted

    async def get_applet_versions(self, applet_id: str) -> [dict, str]:
        applet = FolderModel().findOne(query={"_id": ObjectId(applet_id)})
        owner = AccountProfile().findOne(
            query={"applets.owner": {"$in": [ObjectId(applet_id)]}}
        )

        owner_id = owner["userId"] if owner else str(applet["creatorId"])

        protocolId = applet["meta"]["protocol"].get("_id").split("/").pop()
        result = get_versions_from_content(protocolId)
        converted_applet_versions = dict()
        if result is not None and result != {}:
            last_version = list(result.keys())[-1]

            old_activities_by_id = {}
            for version, content in result.items():
                migration_log.debug(version)
                if version == last_version:
                    converted_applet_versions[
                        version
                    ] = {}  # skipping last version for optimization
                else:
                    (
                        ld_request_schema,
                        old_activities_by_id,
                    ) = content_to_jsonld(
                        content["applet"], old_activities_by_id
                    )
                    ld_request_schema = patch_broken_applet_versions(
                        applet_id, ld_request_schema
                    )
                    converted = await self.get_converter_result(
                        ld_request_schema
                    )
                    converted.extra_fields["created"] = content["updated"]
                    converted.extra_fields["updated"] = content["updated"]
                    converted.extra_fields["version"] = version
                    converted = self._extract_ids(converted, applet_id)

                    converted_applet_versions[version] = converted

        return converted_applet_versions, owner_id

    def _extract_ids(self, converted: dict, applet_id: str = None) -> dict:
        converted.extra_fields["id"] = mongoid_to_uuid(
            applet_id
            if applet_id is not None
            else converted.extra_fields["extra"]["_:id"][0]["@value"]
        )
        for activity in converted.activities:
            activity.extra_fields["id"] = mongoid_to_uuid(
                activity.extra_fields["extra"]["_:id"][0]["@value"]
            )
            for item in activity.items:
                item.extra_fields["id"] = mongoid_to_uuid(
                    item.extra_fields["extra"]["_:id"][0]["@value"]
                )
        for flow in converted.activity_flows:
            flow.extra_fields["id"] = mongoid_to_uuid(
                flow.extra_fields["extra"]["_:id"][0]["@value"]
            )
        return converted

    mongo_arbitrary_db_cache = {}

    def get_main_or_arbitrary_db(self, applet_id: ObjectId) -> Database:
        return self.db  # don't migrate arb servers

        def resolve_arbitrary_client(profile: dict):
            if "db" in profile:
                return MongoClient(profile["db"])

        profile = self.db["accountProfile"].find_one(
            {"applets.owner": applet_id}
        )
        if not profile:
            migration_log.debug(
                "Unable to find the account for applet %s", str(applet_id)
            )
            return self.db

        profile_id = str(profile["_id"])
        if profile_id in self.mongo_arbitrary_db_cache:
            client = self.mongo_arbitrary_db_cache[profile_id]
        elif _client := resolve_arbitrary_client(profile):
            self.mongo_arbitrary_db_cache[profile_id] = _client
            client = _client
        else:
            return self.db

        return client.get_database()

    def get_answer_migration_queries(self, **kwargs):
        db = self.get_main_or_arbitrary_db(kwargs["applet_id"])
        query = {
            "meta.responses": {
                "$exists": True,
                # Some items have response, but response is empty dict, dont't migrate
                "$ne": {},
            },
            "meta.activity.@id": kwargs["activity_id"],
            "meta.applet.@id": kwargs["applet_id"],
            "meta.applet.version": kwargs["version"],
        }
        if kwargs.get("assessments_only"):
            query["meta.reviewing"] = {"$exists": True}
        item_collection = db["item"]
        try:
            creators_ids = item_collection.find(query).distinct("creatorId")
        except Exception as e:
            migration_log.debug("Error: mongo is unreachable %s", str(e))
            return []
        result = []
        for creator_id in creators_ids:
            result.append({**query, "creatorId": creator_id})

        return result

    def get_answers_with_files(
        self,
        *,
        answer_migration_queries,
    ):
        for query in answer_migration_queries:
            db = (
                self.get_main_or_arbitrary_db(query["meta.applet.@id"])
                if "meta.applet.@id" in query
                else self.db
            )
            item_collection = db["item"]
            items = item_collection.find(query, sort=[("created", ASCENDING)])
            del query["meta.responses"]
            answer_with_files = dict()
            for item in items:
                item = item_collection.find_one({"_id": item["_id"]})
                if not answer_with_files and "dataSource" in item["meta"]:
                    answer_with_files["answer"] = item
                    answer_with_files["query"] = query
                elif answer_with_files and "dataSource" not in item["meta"]:
                    answer_with_files.setdefault("files", []).append(
                        item["meta"]["responses"]
                    )
                elif answer_with_files and "dataSource" in item["meta"]:
                    yield answer_with_files
                    answer_with_files = dict(answer=item, query=query)
            yield answer_with_files

    def get_applet_info(self, applet_id: str) -> dict:
        info = {}
        applet = Applet().findOne({"_id": ObjectId(applet_id)})
        account = AccountProfile().findOne({"_id": applet["accountId"]})
        owner = User().findOne({"_id": applet["creatorId"]})
        info["applet_id"] = applet_id
        info["applet_name"] = applet["meta"]["applet"].get(
            "displayName", "Untitled"
        )
        info["account_name"] = account["accountName"]
        info["owner_email"] = owner["email"]
        info["updated"] = applet["updated"]

        return info

    def docs_by_ids(
        self, collection: str, doc_ids: List[ObjectId]
    ) -> List[dict]:
        return self.db[collection].find({"_id": {"$in": doc_ids}})

    def get_user_nickname(self, user_profile: dict) -> str:
        nick_name = decrypt(user_profile.get("nickName"))
        if not nick_name:
            # f_name = decrypt(user_profile.get("firstName"))
            # l_name = decrypt(user_profile.get("lastName"))
            # nick_name = f"{f_name} {l_name}" if f_name and l_name else f""
            nick_name = ""
        return nick_name

    def reviewer_meta(
        self, applet_id: ObjectId, account_profile: dict
    ) -> List[uuid.UUID]:
        reviewer_profile = self.db["appletProfile"].find_one(
            {"userId": account_profile["userId"], "appletId": applet_id}
        )
        respondent_profiles = self.db["appletProfile"].find(
            {
                "appletId": applet_id,
                "reviewers": reviewer_profile["_id"],
                "roles": "user",
            }
        )
        user_ids = []
        for profile in respondent_profiles:
            user_id = profile.get("userId")
            if user_id:
                user_ids.append(mongoid_to_uuid(user_id))
        return user_ids

    def respondents_by_applet_profile(
        self, account_profile: dict
    ) -> List[uuid.UUID]:
        respondent_profiles = self.db["appletProfile"].find(
            {
                "appletId": account_profile["appletId"],
                "reviewers": account_profile["_id"],
                "roles": "user",
            }
        )
        user_ids = []
        for profile in respondent_profiles:
            user_id = profile.get("userId")
            if user_id:
                user_ids.append(mongoid_to_uuid(user_id))
        return user_ids

    def respondent_metadata_applet_profile(self, applet_profile: dict):
        return {
            "nick": self.get_user_nickname(applet_profile),
            "secret": applet_profile.get("MRN", ""),
        }

    def respondent_metadata(self, user: dict, applet_id: ObjectId):
        doc_cur = (
            self.db["appletProfile"]
            .find({"userId": user["_id"], "appletId": applet_id})
            .limit(1)
        )
        doc = next(doc_cur, None)
        if not doc:
            return {}
        return {
            "nick": self.get_user_nickname(doc),
            "secret": doc.get("MRN", ""),
        }

    def inviter_id(self, user_id, applet_id):
        doc_invite = self.db["invitation"].find(
            {"userId": user_id, "appletId": applet_id}
        )
        doc_invite = next(doc_invite, {})
        invitor = doc_invite.get("invitedBy", {})
        invitor_profile_id = invitor.get("_id")
        ap_doc = self.db["appletProfile"].find_one({"_id": invitor_profile_id})
        return mongoid_to_uuid(ap_doc["userId"]) if ap_doc else None

    def is_pinned(self, user_id):
        res = self.db["appletProfile"].find_one(
            {"userId": user_id, "pinnedBy": {"$exists": 1, "$ne": []}}
        )
        return bool(res)

    def get_owner_by_applet(self, applet_id: str) -> uuid.UUID | None:
        owner = AccountProfile().findOne(
            query={"applets.owner": {"$in": [ObjectId(applet_id)]}}
        )
        return mongoid_to_uuid(owner["userId"]) if owner else None

    def get_anons(self, anon_id: uuid.UUID) -> List[AppletUserDAO]:
        applet_profiles = self.db["appletProfile"].find(
            {"MRN": "Guest Account Submission"}
        )
        res = []
        for applet_profile in applet_profiles:
            owner_id = self.get_owner_by_applet(applet_profile["appletId"])
            if owner_id is None:
                continue
            res.append(
                AppletUserDAO(
                    applet_id=mongoid_to_uuid(applet_profile["appletId"]),
                    user_id=anon_id,
                    owner_id=owner_id,
                    inviter_id=owner_id,
                    role=Role.RESPONDENT,
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow(),
                    meta={
                        # nickname is encrypted version of 'Mindlogger ChildMindInstitute'
                        "nickname": "hFywashKw+KlcDPazIy5QHz4AdkTOYkD28Q8+dpeDDA=",
                        "secretUserId": "Guest Account Submission",
                        "legacyProfileId": str(applet_profile["_id"]),
                    },
                    is_pinned=False,
                    is_deleted=False,
                )
            )
        return res

    @staticmethod
    def get_user_roles(applet_profile: dict) -> list[str]:
        roles = applet_profile["roles"]
        if "owner" in roles:
            return ["owner", "user"]
        elif "manager" in roles:
            return ["manager", "user"] if "user" in roles else ["manager"]
        return roles

    def has_manager_role(self, roles: list[str]):
        manager_roles = set(Role.managers())
        exist = bool(set(roles).intersection(manager_roles))
        return exist

    def get_roles_mapping_from_applet_profile(
        self, migrated_applet_ids: List[ObjectId]
    ):
        applet_collection = self.db["folder"]
        not_found_users = []
        not_found_applets = []
        access_result = []
        applet_profiles = self.db["appletProfile"].find(
            {
                "appletId": {"$in": migrated_applet_ids},
                "roles": {"$exists": True, "$not": {"$size": 0}},
            }
        )
        owner_count = 0
        manager_count = 0
        reviewer_count = 0
        editor_count = 0
        coordinator_count = 0
        respondent_count = 0

        for applet_profile in applet_profiles:
            if applet_profile["userId"] in not_found_users:
                continue
            if applet_profile["appletId"] in not_found_applets:
                continue

            user = User().findOne({"_id": applet_profile["userId"]})
            if not user:
                not_found_users.append(applet_profile["userId"])
                continue

            applet = applet_collection.find_one(
                {"_id": applet_profile["appletId"]}
            )
            if not applet:
                not_found_applets.append(applet_profile["appletId"])
                continue

            roles = self.get_user_roles(applet_profile)
            has_manager_role = self.has_manager_role(roles)
            for role_name in set(roles):
                meta = {}
                if role_name == Role.REVIEWER:
                    meta["respondents"] = self.respondents_by_applet_profile(
                        applet_profile
                    )
                    reviewer_count += 1
                elif role_name == Role.EDITOR:
                    editor_count += 1
                elif role_name == Role.COORDINATOR:
                    coordinator_count += 1
                elif role_name == Role.OWNER:
                    owner_count += 1
                elif role_name == Role.MANAGER:
                    manager_count += 1
                elif role_name == "user":
                    respondent_count += 1
                    data = self.respondent_metadata_applet_profile(
                        applet_profile
                    )
                    if data:
                        if has_manager_role:
                            if data["nick"] == "":
                                f_name = user["firstName"]
                                l_name = user["lastName"]
                                f_name = f_name if f_name else "-"
                                l_name = l_name if l_name else "-"
                                meta["nickname"] = f"{f_name} {l_name}"
                            else:
                                meta["nickname"] = data["nick"]

                            meta["secretUserId"] = (
                                f"{str(uuid.uuid4())}"
                                if data["secret"] == ""
                                else data["secret"]
                            )
                        else:
                            meta["nickname"] = data["nick"]
                            meta["secretUserId"] = data["secret"]
                        if "nickname" in meta:
                            nickname = meta.pop("nickname")
                            if nickname != "":
                                meta["nickname"] = enc.process_bind_param(
                                    nickname, String
                                )

                owner_id = self.get_owner_by_applet(applet_profile["appletId"])
                if not owner_id:
                    owner_id = mongoid_to_uuid(applet.get("creatorId"))
                meta["legacyProfileId"] = applet_profile["_id"]
                inviter_id = self.inviter_id(
                    applet_profile["userId"], applet_profile["appletId"]
                )
                if not inviter_id:
                    inviter_id = owner_id
                access = AppletUserDAO(
                    applet_id=mongoid_to_uuid(applet_profile["appletId"]),
                    user_id=mongoid_to_uuid(applet_profile["userId"]),
                    owner_id=owner_id,
                    inviter_id=inviter_id,
                    role=convert_role(role_name),
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow(),
                    meta=meta,
                    is_pinned=self.is_pinned(applet_profile["userId"]),
                    is_deleted=False,
                )
                access_result.append(access)
        prepared = len(access_result)
        migration_log.info(f"[ROLES] found: {prepared}")
        migration_log.info(
            f"""[ROLES]
                Owner:          {owner_count}
                Manager:        {manager_count}
                Editor:         {editor_count}
                Coordinator:    {coordinator_count}
                Reviewer:       {reviewer_count}
                Respondent:     {respondent_count}
        """
        )
        return access_result

    def get_user_applet_role_mapping(
        self, migrated_applet_ids: List[ObjectId]
    ) -> List[AppletUserDAO]:
        account_profile_collection = self.db["accountProfile"]
        applet_collection = self.db["folder"]
        not_found_users = []
        not_found_applets = []
        access_result = []
        account_profile_docs = account_profile_collection.find()
        for doc in account_profile_docs:
            if doc["userId"] in not_found_users:
                continue

            user = User().findOne({"_id": doc["userId"]})
            if not user:
                continue
            role_applets_mapping = doc.get("applets")
            managerial_applets = []
            for role, applets in role_applets_mapping.items():
                if role != "user":
                    managerial_applets.extend(applets)

            for role_name, applet_ids in role_applets_mapping.items():
                for applet_id in applet_ids:
                    # Check maybe we already check this id in past
                    if applet_id in not_found_applets:
                        continue

                    if applet_id not in migrated_applet_ids:
                        # Applet doesn't exist in postgresql, just skip it
                        # ant put id to cache
                        continue
                    applet = applet_collection.find_one({"_id": applet_id})
                    if not applet:
                        continue
                    meta = {}
                    if role_name == Role.REVIEWER:
                        meta["respondents"] = self.reviewer_meta(
                            applet_id, doc
                        )
                    elif role_name == "user":
                        data = self.respondent_metadata(user, applet_id)
                        if data:
                            if applet_id in managerial_applets:
                                if data["nick"] == "":
                                    f_name = user["firstName"]
                                    l_name = user["lastName"]
                                    meta["nickname"] = (
                                        f"{f_name} {l_name}"
                                        if f_name and l_name
                                        else f"- -"
                                    )
                                else:
                                    meta["nickname"] = data["nick"]

                                meta["secretUserId"] = (
                                    f"{str(uuid.uuid4())}"
                                    if data["secret"] == ""
                                    else data["secret"]
                                )
                            else:
                                meta["nickname"] = data["nick"]
                                meta["secretUserId"] = data["secret"]

                    owner_id = self.get_owner_by_applet(applet_id)
                    if not owner_id:
                        owner_id = mongoid_to_uuid(applet.get("creatorId"))

                    applet_profile = self.db["appletProfile"].find_one(
                        {
                            "userId": doc["userId"],
                            "appletId": applet_id,
                        }
                    )
                    if applet_profile:
                        meta["legacyProfileId"] = applet_profile["_id"]
                    inviter_id = self.inviter_id(doc["userId"], applet_id)
                    if not inviter_id:
                        inviter_id = owner_id
                    access = AppletUserDAO(
                        applet_id=mongoid_to_uuid(applet_id),
                        user_id=mongoid_to_uuid(doc["userId"]),
                        owner_id=owner_id,
                        inviter_id=inviter_id,
                        role=convert_role(role_name),
                        created_at=datetime.datetime.utcnow(),
                        updated_at=datetime.datetime.utcnow(),
                        meta=meta,
                        is_pinned=self.is_pinned(doc["userId"]),
                        is_deleted=False,
                    )
                    access_result.append(access)
        migration_log.info(
            f"[Role] Prepared for migrations {len(access_result)} items"
        )
        return list(set(access_result))

    def get_pinned_users(self, applets_ids: list[ObjectId] | None):
        query = {
            "pinnedBy": {"$exists": 1},
            "userId": {"$exists": 1, "$ne": None},
        }
        if applets_ids:
            query["appletId"] = {"$in": applets_ids}
        return self.db["appletProfile"].find(query)

    def get_applet_profiles_by_ids(self, ids):
        return self.db["appletProfile"].find({"_id": {"$in": ids}})

    def get_pinned_role(self, applet_profile):
        system_roles = Role.as_list().copy()
        system_roles.remove(Role.RESPONDENT)
        system_roles = set(system_roles)
        applet_roles = set(applet_profile.get("roles", []))
        if system_roles.intersection(applet_roles):
            return Role.MANAGER
        else:
            return Role.RESPONDENT

    def get_owner_by_applet_profile(self, applet_profile):
        profiles = self.db["accountProfile"].find(
            {"userId": applet_profile["userId"]}
        )
        it = filter(lambda p: p["_id"] == p["accountId"], profiles)
        profile = next(it, None)
        return profile["userId"] if profiles else None

    def get_user_pin_mapping(self, applets_ids: list[ObjectId] | None):
        pin_profiles = self.get_pinned_users(applets_ids)
        pin_dao_list = set()
        for profile in pin_profiles:
            if not profile["pinnedBy"]:
                continue
            pinned_by = self.get_applet_profiles_by_ids(profile["pinnedBy"])
            for manager_profile in pinned_by:
                role = self.get_pinned_role(manager_profile)
                owner_id = self.get_owner_by_applet_profile(manager_profile)
                dao = UserPinsDAO(
                    user_id=mongoid_to_uuid(profile["userId"]),
                    pinned_user_id=mongoid_to_uuid(manager_profile["userId"]),
                    owner_id=mongoid_to_uuid(owner_id),
                    role=convert_role(role),
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow(),
                )
                pin_dao_list.add(dao)
        return pin_dao_list

    def get_folders(self, account_id):
        return list(
            FolderModel().find(
                query={"accountId": account_id, "baseParentType": "user"}
            )
        )

    def get_applets_in_folder(self, folder_id):
        return list(
            FolderModel().find(
                query={
                    "baseParentType": "folder",
                    "baseParentId": folder_id,
                    "meta.applet": {"$exists": True},
                }
            )
        )

    def get_root_applets(self, account_id):
        return list(
            FolderModel().find(
                query={
                    "accountId": account_id,
                    "baseParentType": "collection",
                    "baseParentId": ObjectId("5ea689a286d25a5dbb14e82c"),
                    "meta.applet": {"$exists": True},
                }
            )
        )

    def get_folders_and_applets(self, account_id):
        folders = self.get_folders(account_id)
        for folder in folders:
            folder["applets"] = self.get_applets_in_folder(folder["_id"])
        result = {
            "applets": self.get_root_applets(account_id),
            "folders": folders,
        }
        return result

    def get_folder_pin(
        self, folder: dict, applet_id: ObjectId
    ) -> datetime.datetime | None:
        def _filter_applet(document):
            _id = document["_id"]
            if isinstance(_id, str):
                _id = ObjectId(_id)
            return _id == applet_id

        meta = folder.get("meta", {})
        applets_order = meta.get("applets", {})
        order_it = filter(_filter_applet, applets_order)
        order = next(order_it, None)
        if not order or not order.get("_pin_order"):
            return None
        now = datetime.datetime.utcnow()
        return now + datetime.timedelta(seconds=order["_pin_order"])

    def get_folder_mapping(
        self, workspaces: list[tuple[uuid.UUID, uuid.UUID]]
    ) -> Tuple[Set[FolderDAO], Set[FolderAppletDAO]]:
        folders_list = []
        applets_list = []
        count = 0
        all_count = len(workspaces)
        for workspace in workspaces:
            workspace_id = workspace[0]
            workspace_user_id = workspace[1]
            account_id = uuid_to_mongoid(workspace_id)
            if account_id is None:
                continue
            res = self.get_folders_and_applets(account_id)
            folder_count = 0
            all_folder_count = len(res["folders"])
            for folder in res["folders"]:
                creator_id = mongoid_to_uuid(folder["creatorId"])
                folders_list.append(
                    FolderDAO(
                        id=mongoid_to_uuid(folder["_id"]),
                        created_at=folder["created"],
                        updated_at=folder["updated"],
                        name=folder["name"],
                        creator_id=creator_id,
                        workspace_id=workspace_user_id,
                        migrated_date=datetime.datetime.utcnow(),
                        migrated_update=datetime.datetime.utcnow(),
                        is_deleted=False,
                    )
                )
                folder_count += 1
                migration_log.debug(
                    f"[FOLDERS] "
                    f"\t fetch folder: {folder_count}/{all_folder_count}"
                )
                for applet in folder["applets"]:
                    pinned_at = self.get_folder_pin(folder, applet["_id"])
                    applets_list.append(
                        FolderAppletDAO(
                            id=uuid.uuid4(),
                            folder_id=mongoid_to_uuid(folder["_id"]),
                            applet_id=mongoid_to_uuid(applet["_id"]),
                            created_at=applet["created"],
                            updated_at=applet["updated"],
                            pinned_at=pinned_at,
                            migrated_date=datetime.datetime.utcnow(),
                            migrated_update=datetime.datetime.utcnow(),
                            is_deleted=False,
                        )
                    )
            count += 1
            migration_log.debug(
                f"[FOLDERS] Fetch workspace folders {count}/{all_count}"
            )
        return set(folders_list), set(applets_list)

    def get_themes(self) -> list[ThemeDao]:
        themes = []
        theme_docs = self.db["folder"].find(
            {"parentId": ObjectId("61323c0ff7102f0a6e9b3588")}
        )
        for theme_doc in theme_docs:
            if theme_doc:
                meta = theme_doc.get("meta", {})
                themes.append(
                    ThemeDao(
                        id=mongoid_to_uuid(theme_doc["_id"]),
                        creator_id=mongoid_to_uuid(theme_doc["creatorId"]),
                        name=theme_doc["name"],
                        logo=meta.get("logo"),
                        small_logo=meta.get("smallLogo"),
                        background_image=meta.get("backgroundImage"),
                        primary_color=meta.get("primaryColor"),
                        secondary_color=meta.get("secondaryColor"),
                        tertiary_color=meta.get("tertiaryColor"),
                        public=theme_doc["public"],
                        allow_rename=True,
                        created_at=theme_doc["created"],
                        updated_at=theme_doc["updated"],
                        is_default=False,
                    )
                )
        return themes

    def get_library(self, applet_ids: list[ObjectId] | None) -> LibraryDao:
        lib_set = set()
        query = {}
        if applet_ids:
            query["appletId"] = {"$in": applet_ids}
        library = self.db["appletLibrary"].find(query)
        for lib_doc in library:
            applet_id = mongoid_to_uuid(lib_doc["appletId"])
            version = lib_doc.get("version")
            version = patch_library_version(str(lib_doc["appletId"]), version)
            if version:
                version_id = f"{applet_id}_{version}"
            else:
                version_id = None
            now = datetime.datetime.utcnow()
            created_at = lib_doc.get("createdAt", now)
            updated_at = lib_doc.get("updated_at", now)
            lib = LibraryDao(
                id=mongoid_to_uuid(lib_doc["_id"]),
                applet_id=applet_id,
                applet_id_version=version_id,
                keywords=lib_doc["keywords"] + [lib_doc["name"]],
                search_keywords=lib_doc["keywords"] + [lib_doc["name"]],
                created_at=created_at,
                updated_at=updated_at,
                migrated_date=now,
                migrated_updated=now,
                is_deleted=False,
                name=lib_doc["name"],
                display_name=lib_doc["displayName"],
            )
            lib_set.add(lib)
        return lib_set

    def get_applets_by_workspace(self, workspace_id: str) -> list[str]:
        items = Profile().find(query={"accountId": ObjectId(workspace_id)})
        ids = set()
        for item in items:
            ids.add(str(item["appletId"]))
        return list(ids)

    def get_public_link_mappings(
        self, applet_ids: List[ObjectId]
    ) -> List[PublicLinkDao]:
        applets = self.db["folder"].find(
            {
                "_id": {"$in": applet_ids},
                "publicLink": {"$exists": -1},
            }
        )
        result = []
        for document in applets:
            link: dict | None = document.get("publicLink")
            if link:
                link_id = link.get("id")
                login = link.get("requireLogin")
                created_by_ap = link.get("createdBy")
                applet_profile = self.db["appletProfile"].find_one(
                    {"_id": created_by_ap["_id"]}
                )
                if not applet_profile:
                    continue
                user_id = applet_profile["userId"]
                if not isinstance(user_id, ObjectId):
                    user_id = ObjectId(user_id)
                if link_id is not None and login is not None:
                    result.append(
                        PublicLinkDao(
                            applet_bson=document["_id"],
                            link=link_id,
                            require_login=login,
                            created_by_bson=user_id,
                        )
                    )
        return result

    def get_applet_theme_mapping(self) -> list[AppletTheme]:
        applet_cursor = self.db["folder"].find(
            {
                "$and": [
                    {"meta.applet.themeId": {"$exists": True}},
                    {"meta.applet.themeId": {"$ne": "None"}},
                    {"meta.applet.themeId": {"$ne": None}},
                ]
            }
        )
        result = []
        for applet_doc in applet_cursor:
            applet_id = mongoid_to_uuid(applet_doc["_id"])
            theme_id = mongoid_to_uuid(applet_doc["meta"]["applet"]["themeId"])
            theme_bson_id = ObjectId(applet_doc["meta"]["applet"]["themeId"])
            theme = self.db["folder"].find_one({"_id": theme_bson_id})
            theme_name = (
                theme["name"] if theme["name"] != "mindlogger" else "Default"
            )
            if theme:
                mapper = AppletTheme(
                    applet_id=applet_id,
                    theme_id=theme_id,
                    theme_name=theme_name,
                )
                result.append(mapper)
        return result

    def get_repro_order(self, schema: dict):
        act_list = schema.get("reprolib:terms/order", [])
        result = []
        for act in act_list:
            _list_attr = act.get("@list", [])
            result += _list_attr
        return result

    @staticmethod
    def is_has_item_types(
        _types: list[str], activity_items: list[dict]
    ) -> bool:
        for item in activity_items:
            _inputs = item.get("reprolib:terms/inputType", [])
            for _input in _inputs:
                if _input.get("@value") in _types:
                    return True
        return False

    def get_activity_names(self, activity_schemas: list[dict]) -> list[str]:
        names = []
        for activity in activity_schemas:
            name_attr = activity.get(
                "http://www.w3.org/2004/02/skos/core#prefLabel"
            )
            name_attr = next(iter(name_attr), {})
            name = name_attr.get("@value")
            if name:
                names.append(name)
        return names

    def _is_cst(self, activity_items: list[dict], cst_type: str):
        def _filter_user_input_type(item: dict):
            _type = next(iter(item.get("@type", [])), None)
            if not _type or _type != "http://schema.org/Text":
                return False
            name = next(iter(item.get("schema:name", [])), {})
            value = next(iter(item.get("schema:value", [])), {})
            if (
                name.get("@value") == "userInputType"
                and value.get("@value") == cst_type
            ):
                return True

        for item in activity_items:
            _inputs = item.get("reprolib:terms/inputs", [])
            for _input in _inputs:
                flt_result = next(
                    filter(_filter_user_input_type, _inputs), None
                )
                if flt_result:
                    return self.is_has_item_types(
                        ["stabilityTracker"], activity_items
                    )
        return False

    def is_cst(self, activity_items: list[dict]) -> bool:
        return self._is_cst(activity_items, "touch")

    def is_cst_gyro(self, activity_items: list[dict]) -> bool:
        return self._is_cst(activity_items, "gyroscope")

    def is_ab_trails(
        self,
        applet_schema: dict,
        activity_items: list[dict],
        activity_names: list[str],
    ) -> bool:
        # Check activity names
        # Try to find 'Trails_iPad', 'Trails_Mobile' strings as activity name
        ab_trails_act_names = ["Trails_iPad", "Trails_Mobile"]
        m = list(map(lambda name: name in ab_trails_act_names, activity_names))
        if not any(m):
            return False
        # Check applet name
        # Try to find 'A/B Trails' as expected applet name
        ab_trails_name = "A/B Trails"
        applet_name = applet_schema.get(
            "http://www.w3.org/2004/02/skos/core#prefLabel"
        )
        applet_name = next(iter(applet_name), {})
        if applet_name.get("@value") != ab_trails_name:
            return False
        # Check activity item types
        # Try to find items with type 'trail'
        return self.is_has_item_types(["trail"], activity_items)

    def is_flanker(self, activity_items: list[dict]) -> bool:
        return self.is_has_item_types(
            ["visual-stimulus-response"], activity_items
        )

    def preprocess_performance_task(self, applet_schema) -> dict:
        # Add activity type by activity items for activities without type
        activities = self.get_repro_order(applet_schema)
        activity_names = self.get_activity_names(activities)
        for activity in activities:
            activity_type = activity.get("reprolib:terms/activityType")
            if activity_type is not None:
                # If activity have activityType it is normal case
                continue
            items = self.get_repro_order(activity)
            if self.is_ab_trails(applet_schema, items, activity_names):
                name_attr = activity.get(
                    "http://www.w3.org/2004/02/skos/core#prefLabel"
                )
                activity_name = next(iter(name_attr), {})
                if activity_name.get("@value") == "Trails_Mobile":
                    name = "TRAILS_MOBILE"
                else:
                    name = "TRAILS_IPAD"
                activity["reprolib:terms/activityType"] = [
                    {
                        "@type": "http://www.w3.org/2001/XMLSchema#string",
                        "@value": name,
                    }
                ]
                continue
            elif self.is_cst_gyro(items):
                activity["reprolib:terms/activityType"] = [
                    {
                        "@type": "http://www.w3.org/2001/XMLSchema#string",
                        "@value": "CST_GYRO",
                    }
                ]
            elif self.is_cst(items):
                activity["reprolib:terms/activityType"] = [
                    {
                        "@type": "http://www.w3.org/2001/XMLSchema#string",
                        "@value": "CST_TOUCH",
                    }
                ]
                continue
            elif self.is_flanker(items):
                activity["reprolib:terms/activityType"] = [
                    {
                        "@type": "http://www.w3.org/2001/XMLSchema#string",
                        "@value": "FLANKER",
                    }
                ]
                continue
        return applet_schema

    def fetch_applet_version(self, applet: dict):
        if not applet["meta"]["applet"].get("version", None):
            protocol = self.db["folder"].find_one(
                {
                    "_id": ObjectId(
                        str(applet["meta"]["protocol"]["_id"]).split("/")[1]
                    )
                }
            )
            applet["meta"]["applet"]["version"] = protocol["meta"]["protocol"][
                "schema:version"
            ][0]["@value"]
        return applet
