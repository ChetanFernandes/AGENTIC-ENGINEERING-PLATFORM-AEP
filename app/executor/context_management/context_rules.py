AGENT_CONTEXT_POLICY = {

    "repository": {
        "allowed": [
            "repository"
        ],
        "optional": [
            "architecture",
            "security",
            "code_review",
            "testing"
        ]
    },

    "architecture": {
        "allowed": [
            "repository"
        ],
        "optional": [
            "security",
            "code_review",
            "testing",
            "performance"
        ]
    },

    "security": {
        "allowed": [
            "repository"
        ],
        "optional": [
            "architecture",
            "code_review",
            "testing",
            "performance"
        ]
    },

    "performance": {
        "allowed": [
            "repository"
        ],
        "optional": [
            "architecture",
            "testing",
            "code_review"
        ]
    },

    "code_review": {
        "allowed": [
            "repository"
        ],
        "optional": [
            "security",
            "architecture",
            "testing",
            "performance"
        ]
    },

    "testing": {
        "allowed": [
            "repository"
        ],
        "optional": [
            "security",
            "code_review",
            "architecture",
            "code_engineering",
            "optimization",
            "refactoring"
        ]
    },

    "code_engineering": {
        "allowed": [
            "repository",
            "security",
            "code_review"
        ],
        "optional": [
            "testing",
            "architecture",
            "performance",
            "optimization"
        ]
    },

    "optimization": {
        "allowed": [
            "repository",
            "performance"
        ],
        "optional": [
            "architecture",
            "code_review",
            "testing",
            "security"
        ]
    },

    "refactoring": {
        "allowed": [
            "repository",
            "code_review"
        ],
        "optional": [
            "security",
            "architecture",
            "testing",
            "performance",
            "optimization"
        ]
    },

    "Jira": {
        "allowed": [
            "security",
            "code_review",
            "testing"
        ],
        "optional": [
            "architecture",
            "performance",
            "code_engineering",
            "optimization",
            "refactoring"
        ]
    }
}