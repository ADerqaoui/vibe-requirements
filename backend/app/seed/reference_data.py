"""Reference data for disciplines, layers, and V-model parent rules."""

DISCIPLINES = ("SW", "Electronic", "Mechanical")

LAYERS = (
    {"name": "Need", "kind": "cross_cutting", "discipline": None, "sort_order": 0},
    {"name": "System Requirement", "kind": "cross_cutting", "discipline": None, "sort_order": 10},
    {"name": "System Architecture", "kind": "cross_cutting", "discipline": None, "sort_order": 20},
    {"name": "SW Requirement", "kind": "discipline_locked", "discipline": "SW", "sort_order": 30},
    {"name": "SW Architecture", "kind": "discipline_locked", "discipline": "SW", "sort_order": 40},
    {"name": "SW Component/Unit", "kind": "discipline_locked", "discipline": "SW", "sort_order": 50},
    {
        "name": "Electronic Requirement",
        "kind": "discipline_locked",
        "discipline": "Electronic",
        "sort_order": 30,
    },
    {
        "name": "Electronic Architecture",
        "kind": "discipline_locked",
        "discipline": "Electronic",
        "sort_order": 40,
    },
    {
        "name": "Electronic Component",
        "kind": "discipline_locked",
        "discipline": "Electronic",
        "sort_order": 50,
    },
    {
        "name": "Mechanical Requirement",
        "kind": "discipline_locked",
        "discipline": "Mechanical",
        "sort_order": 30,
    },
    {
        "name": "Mechanical Architecture",
        "kind": "discipline_locked",
        "discipline": "Mechanical",
        "sort_order": 40,
    },
    {
        "name": "Mechanical Component",
        "kind": "discipline_locked",
        "discipline": "Mechanical",
        "sort_order": 50,
    },
)

LAYER_PARENTS = {
    "Need": (),
    "System Requirement": ("Need",),
    "System Architecture": ("System Requirement",),
    "SW Requirement": ("System Requirement", "System Architecture"),
    "SW Architecture": ("SW Requirement",),
    "SW Component/Unit": ("SW Architecture", "SW Requirement"),
    "Electronic Requirement": ("System Requirement", "System Architecture"),
    "Electronic Architecture": ("Electronic Requirement",),
    "Electronic Component": ("Electronic Architecture", "Electronic Requirement"),
    "Mechanical Requirement": ("System Requirement", "System Architecture"),
    "Mechanical Architecture": ("Mechanical Requirement",),
    "Mechanical Component": ("Mechanical Architecture", "Mechanical Requirement"),
}
