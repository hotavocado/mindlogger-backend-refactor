# -*- coding: utf-8 -*-
"""
Constants should be defined here.
"""
import itertools
import os

from apps import girderformindlogger

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
LOG_ROOT = os.path.join(
    os.path.expanduser("~"), ".girderformindlogger", "logs"
)
MAX_LOG_SIZE = 1024 * 1024 * 10  # Size in bytes before logs are rotated.
LOG_BACKUP_COUNT = 5
ACCESS_FLAGS = {}

MAX_PULL_SIZE = 1024 * 1024 * 2
RESPONSE_ITEM_PAGINATION = 5000
APPLET_SCHEMA_VERSION = "1.0.1"

# Identifier for Girder's entry in the route table
GIRDER_ROUTE_ID = "core_girder"

# Threshold below which text search results will be sorted by their text score.
# Setting this too high causes mongodb to use too many resources for searches
# that yield lots of results.
TEXT_SCORE_SORT_MAX = 200
VERSION = {"release": girderformindlogger.__version__}

#: The local directory containing the static content.
STATIC_PREFIX = os.path.join(
    os.path.dirname(PACKAGE_DIR), "girderformindlogger"
)
STATIC_ROOT_DIR = os.path.join(STATIC_PREFIX, "web_client", "static")

DEFINED_INFORMANTS = {
    "parent": ["schema:children", "rel:parentOf"],
    "self": ["schema:sameAs"],
}

DEFINED_RELATIONS = {
    "schema:knows": {
        "rdf:type": ["owl:SymmetricProperty"],
        "rdfs:comment": [
            "The most generic bi-directional social/work relation."
        ],
    },
    "schema:sameAs": {
        "rdf:type": ["owl:SymmetricProperty"],
        "rdfs:comment": [
            "URL of a reference Web page that unambiguously indicates the "
            "item's identity. E.g. the URL of the item's Wikipedia page, "
            "Wikidata entry, or official website."
        ],
    },
    "rel:parentOf": {
        "owl:inverseOf": ["rel:childOf"],
        "owl:equivalentProperty": ["schema:parent"],
        "rdfs:subPropertyOf": ["schema:knows"],
        "rdfs:comment": [
            "A person who has given birth to or nurtured and raised this "
            "person."
        ],
    },
    "schema:parent": {
        "owl:inverseOf": ["schema:children"],
        "owl:equivalentProperty": ["rel:childOf"],
        "rdfs:subPropertyOf": ["schema:knows"],
        "rdfs:comment": ["A parent of this person."],
    },
    "bio:father": {
        "rdfs:subPropertyOf": ["schema:knows"],
        "rdfs:comment": [
            "The biological father of a person, also known as the genitor"
        ],
        "owl:inverseOf": ["rel:parentOf"],
    },
    "bio:mother": {
        "rdfs:subPropertyOf": ["schema:knows"],
        "rdfs:comment": [
            "The biological mother of a person, also known as the genetrix"
        ],
        "owl:inverseOf": ["rel:parentOf"],
    },
    "rel:childOf": {
        "owl:inverseOf": ["rel:parentOf"],
        "owl:equivalentProperty": ["schema:children"],
        "rdfs:comment": [
            "A person who was given birth to or nurtured and raised by this "
            "person."
        ],
    },
    "schema:children": {
        "owl:inverseOf": ["schema:parent"],
        "owl:equivalentProperty": ["rel:parentOf"],
        "rdfs:comment": ["A child of the person."],
    },
}

PREFERRED_NAMES = [
    "skos:prefLabel",
    "skos:altLabel",
    "name",
    "schema:name",
    "@id",
    "url",
]

HIERARCHY = ["applet", "protocol", "activity", "screen", "item"]

KEYS_TO_DELANGUAGETAG = list(
    itertools.chain.from_iterable(
        [
            ["http://schema.org/{}".format(k), "schema:{}".format(k), k]
            for k in ["contentUrl", "encodingFormat", "image", "url"]
        ]
    )
)

KEYS_TO_DEREFERENCE = [
    "schema:about",
    "http://schema.org/about",
    *KEYS_TO_DELANGUAGETAG,
]

KEYS_TO_EXPAND = [
    "responseOptions",
    "https://schema.repronim.org/valueconstraints",
    "reproterms:valueconstraints",
    "valueconstraints",
    "reprolib:valueconstraints",
    "reprolib:terms/valueconstraints",
]

PROFILE_FIELDS = ["_id", "firstName", "lastName", "schema:knows", "MRN"]


def MODELS():
    from apps.girderformindlogger.models.activity import Activity as ActivityModel
    from apps.girderformindlogger.models.applet import Applet as AppletModel
    from apps.girderformindlogger.models.cache import Cache as CacheModel
    from apps.girderformindlogger.models.collection import Collection as CollectionModel
    from apps.girderformindlogger.models.folder import Folder as FolderModel
    from apps.girderformindlogger.models.item import Item as ItemModel
    from apps.girderformindlogger.models.protocol import Protocol as ProtocolModel
    from apps.girderformindlogger.models.pushNotification import PushNotification as PushNotificationModel
    from apps.girderformindlogger.models.screen import Screen as ScreenModel
    from apps.girderformindlogger.models.user import User as UserModel

    return {
        "activity": ActivityModel,
        "activityFlow": FolderModel,
        "activitySet": ProtocolModel,
        "applet": AppletModel,
        "collection": CollectionModel,
        "field": ScreenModel,
        "folder": FolderModel,
        "item": ItemModel,
        "protocol": ProtocolModel,
        "screen": ScreenModel,
        "user": UserModel,
        "pushNotification": PushNotificationModel,
        "cache": CacheModel,
    }


NONES = {"None", None, "none", ""}

REPROLIB_CANONICAL = "://".join(
    ["https", "raw.githubusercontent.com/ReproNim/reproschema/master/"]
)

REPROLIB_PREFIXES = [
    *[
        "://".join([p, u])
        for p in ["http", "https"]
        for u in [
            "schema.repronim.org/",
            "purl.org/repro/s/dev/",
            "raw.githubusercontent.com/ReproNim/schema-standardization/master/",
            "raw.githubusercontent.com/ReproNim/reprolib/master/",
            "raw.githubusercontent.com/ReproNim/reproschema/master/",
        ]
    ],
    "reproschema:",
    "reproterms:",
]

REPROLIB_TYPES = {
    "activity": "reprolib:schemas/Activity",
    "protocol": "reprolib:schemas/Protocol",
    "screen": "reprolib:schemas/Field",
}

REPROLIB_TYPES_REVERSED = {
    v.split("/")[1]: k for k, v in REPROLIB_TYPES.items()
}


SPECIAL_SUBJECTS = {"ALL", "NONE"}

USER_ROLES = {
    "user": dict,
    "coordinator": list,
    "editor": list,
    "manager": list,
    "reviewer": dict,
}


def registerAccessFlag(key, name, description=None, admin=False):
    """
    Register a new access flag in the set of ACCESS_FLAGS available
    on data in the hierarchy. These are boolean switches that can be used
    to control access to specific functionality on specific resoruces.

    :param key: The unique identifier for this access flag.
    :type key: str
    :param name: Human readable name for this permission (displayed in UI).
    :type name: str
    :param description: Human readable longer description for the flag.
    :type description: str
    :param admin: Set this to True to only allow site admin users to set
        this flag. If True, the flag will only appear in the list for
        site admins. This can be useful for flags with security
        considerations.
    """
    ACCESS_FLAGS[key] = {
        "name": name,
        "description": description,
        "admin": admin,
    }


class ServerMode(object):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"


class TerminalColor(object):
    """
    Provides a set of values that can be used to color text in the terminal.
    """

    ERROR = "\033[1;91m"
    SUCCESS = "\033[32m"
    WARNING = "\033[1;33m"
    INFO = "\033[35m"
    ENDC = "\033[0m"

    @staticmethod
    def _color(tag, text):
        return "".join([tag, text, TerminalColor.ENDC])

    @staticmethod
    def error(text):
        return TerminalColor._color(TerminalColor.ERROR, text)

    @staticmethod
    def success(text):
        return TerminalColor._color(TerminalColor.SUCCESS, text)

    @staticmethod
    def warning(text):
        return TerminalColor._color(TerminalColor.WARNING, text)

    @staticmethod
    def info(text):
        return TerminalColor._color(TerminalColor.INFO, text)


class AssetstoreType(object):
    """
    All possible assetstore implementation types.
    """

    FILESYSTEM = 0
    GRIDFS = 1
    S3 = 2


class AccessType(object):
    """
    Represents the level of access granted to a user or group on an
    AccessControlledModel. Having a higher access level on a resource also
    confers all of the privileges of the lower levels.

    Semantically, READ access on a resource means that the user can see all
    the information pertaining to the resource, but cannot modify it.

    WRITE access usually means the user can modify aspects of the resource.

    ADMIN access confers total control; the user can delete the resource and
    also manage permissions for other users on it.
    """

    NONE = -1
    READ = 0
    WRITE = 1
    ADMIN = 2
    SITE_ADMIN = 100

    @classmethod
    def validate(cls, level):
        level = int(level)
        if level in (cls.NONE, cls.READ, cls.WRITE, cls.ADMIN, cls.SITE_ADMIN):
            return level
        else:
            raise ValueError("Invalid AccessType: %d." % level)


class SortDir(object):
    ASCENDING = 1
    DESCENDING = -1


class TokenScope(object):
    """
    Constants for core token scope strings. Token scopes must not contain
    spaces, since many services accept scope lists as a space-separated list
    of strings.
    """

    ONE_TIME_AUTH = "core.one_time"
    ANONYMOUS_SESSION = "core.anonymous_session"
    USER_AUTH = "core.user_auth"
    TEMPORARY_USER_AUTH = "core.user_auth.temporary"
    EMAIL_VERIFICATION = "core.email_verification"
    PLUGINS_READ = "core.plugins.read"
    SETTINGS_READ = "core.setting.read"
    ASSETSTORES_READ = "core.assetstore.read"
    PARTIAL_UPLOAD_READ = "core.partial_upload.read"
    PARTIAL_UPLOAD_CLEAN = "core.partial_upload.clean"
    DATA_READ = "core.data.read"
    DATA_WRITE = "core.data.write"
    DATA_OWN = "core.data.own"
    USER_INFO_READ = "core.user_info.read"

    _customScopes = []
    _adminCustomScopes = []
    _scopeIds = set()
    _adminScopeIds = set()

    @classmethod
    def describeScope(cls, scopeId, name, description, admin=False):
        """
        Register a description of a scope.

        :param scopeId: The unique identifier string for the scope.
        :type scopeId: str
        :param name: A short human readable name for the scope.
        :type name: str
        :param description: A more complete description of the scope.
        :type description: str
        :param admin: If this scope only applies to admin users, set to True.
        :type admin: bool
        """
        info = {"id": scopeId, "name": name, "description": description}
        if admin:
            cls._adminCustomScopes.append(info)
            cls._adminScopeIds.add(scopeId)
        else:
            cls._customScopes.append(info)
            cls._scopeIds.add(scopeId)

    @classmethod
    def listScopes(cls):
        return {
            "custom": cls._customScopes,
            "adminCustom": cls._adminCustomScopes,
        }

    @classmethod
    def scopeIds(cls, admin=False):
        if admin:
            return cls._scopeIds | cls._adminScopeIds
        else:
            return cls._scopeIds


TokenScope.describeScope(
    TokenScope.USER_INFO_READ,
    "Read your user information",
    "Allows clients to look up your user information, including private fields "
    "such as email address.",
)
TokenScope.describeScope(
    TokenScope.DATA_READ,
    "Read data",
    "Allows clients to read all data that you have access to.",
)
TokenScope.describeScope(
    TokenScope.DATA_WRITE,
    "Write data",
    "Allows clients to edit data in the hierarchy and create new data anywhere "
    "you have write access.",
)
TokenScope.describeScope(
    TokenScope.DATA_OWN,
    "Data ownership",
    "Allows administrative control "
    "on data you own, including setting access control and deletion.",
)

TokenScope.describeScope(
    TokenScope.PLUGINS_READ,
    "See installed plugins",
    "Allows clients " "to see the list of plugins installed on the server.",
    admin=True,
)
TokenScope.describeScope(
    TokenScope.SETTINGS_READ,
    "See system setting values",
    "Allows clients to " "view the value of any system setting.",
    admin=True,
)
TokenScope.describeScope(
    TokenScope.ASSETSTORES_READ,
    "View assetstores",
    "Allows clients to see " "all assetstore information.",
    admin=True,
)
TokenScope.describeScope(
    TokenScope.PARTIAL_UPLOAD_READ,
    "View unfinished uploads.",
    "Allows clients to see all partial uploads.",
    admin=True,
)
TokenScope.describeScope(
    TokenScope.PARTIAL_UPLOAD_CLEAN,
    "Remove unfinished uploads.",
    "Allows clients to remove unfinished uploads.",
    admin=True,
)


class CoreEventHandler(object):
    """
    This enum represents handler identifier strings for core event handlers.
    If you wish to unbind a core event handler, use one of these as the
    ``handlerName`` argument. Unbinding core event handlers can be used to
    disable certain default functionalities.
    """

    # For removing deleted user/group references from AccessControlledModel
    ACCESS_CONTROL_CLEANUP = "core.cleanupDeletedEntity"

    # For updating an item's size to include a new file.
    FILE_PROPAGATE_SIZE = "core.propagateSizeToItem"

    # For adding a group's creator into its ACL at creation time.
    GROUP_CREATOR_ACCESS = "core.grantCreatorAccess"

    # For creating the default Public and Private folders at user creation time.
    USER_DEFAULT_FOLDERS = "core.addDefaultFolders"

    # For adding a user into its own ACL.
    USER_SELF_ACCESS = "core.grantSelfAccess"

    # For updating the cached webroot HTML when settings change.
    WEBROOT_SETTING_CHANGE = "core.updateWebrootSettings"
