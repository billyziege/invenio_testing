from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    ".",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                "test_record_search": "./js/test_record/search/index.js",
                "test_record_deposit_form": "./js/test_record/forms/index.js",
            },
            dependencies={},
            devDependencies={},
            aliases={
                "@js/test_record": "./js/test_record"
            },
        )
    },
)
