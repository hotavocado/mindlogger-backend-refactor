from apps.shared.domain import PublicModel


class Node(PublicModel):
    order_index: int
    cx: float
    cy: float
    label: str


class BaseNodes(PublicModel):
    radius: float
    font_size: float
    nodes: list[Node]


class Tutorial(PublicModel):
    text: str
    node_label: str | None = None


class ABTrailsTutorial(PublicModel):
    tutorials: list[Tutorial]