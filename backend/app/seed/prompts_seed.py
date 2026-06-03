"""Default DB-backed prompt templates."""

GENERATE_SPEC_TEMPLATE = (
    "Generate child specifications for this Need.\n"
    "Need: {parent_statement}\n"
    "Output exactly {count} concise child specifications.\n"
    "Use a numbered list. Do not include commentary, headings, or explanations."
)

GENERATE_SPEC_TO_CHILD_V2_TEMPLATE = (
    "Generate child specifications for this parent specification.\n"
    "Parent specification: {parent_statement}\n"
    "Output exactly {count} concise child specifications.\n"
    "Use a numbered list. Do not include commentary, headings, or explanations."
)

CLASSIFY_SPEC_TEMPLATE = (
    "Classify the complexity of this specification from 1 to 5.\n"
    "1 = trivial, 2 = simple, 3 = moderate, 4 = complex, 5 = very complex.\n"
    "Return only one integer from 1 to 5 with no commentary.\n"
    "Specification: {spec_statement}"
)

INSPECT_SPEC_TEMPLATE = (
    "Evaluate this requirement specification against the five criteria below.\n"
    "Output exactly one line per criterion in this format:\n"
    "- <Criterion>: PASS | FAIL — <short note>\n\n"
    "Criteria:\n"
    "- Clarity: PASS | FAIL — <short note>\n"
    "- Measurability: PASS | FAIL — <short note>\n"
    "- Testability: PASS | FAIL — <short note>\n"
    "- Atomicity: PASS | FAIL — <short note>\n"
    "- Ambiguity-free: PASS | FAIL — <short note>\n\n"
    "Specification:\n"
    "{spec_statement}"
)

DEFAULT_PROMPT_ROWS = (
    # v1 history preserves the pre-registry shared wording for auditability.
    {
        "task": "generate_need_to_spec",
        "name": "Generate Need to Spec",
        "description": "Generate child specifications from a Need.",
        "version": 1,
        "enabled": 1,
        "layer_id": None,
        "discipline_scope": None,
        "template": GENERATE_SPEC_TEMPLATE,
    },
    {
        "task": "generate_spec_to_child",
        "name": "Generate Spec to Child",
        "description": "Generate child specifications from a Spec.",
        "version": 1,
        "enabled": 1,
        "layer_id": None,
        "discipline_scope": None,
        "template": GENERATE_SPEC_TEMPLATE,
    },
    {
        "task": "classify_spec",
        "name": "Classify Spec",
        "description": "Classify a specification complexity from 1 to 5.",
        "version": 1,
        "enabled": 1,
        "layer_id": None,
        "discipline_scope": None,
        "template": CLASSIFY_SPEC_TEMPLATE,
    },
    {
        "task": "inspect_spec",
        "name": "Inspect Spec",
        "description": "Inspect a specification against quality criteria.",
        "version": 1,
        "enabled": 1,
        "layer_id": None,
        "discipline_scope": None,
        "template": INSPECT_SPEC_TEMPLATE,
    },
)
