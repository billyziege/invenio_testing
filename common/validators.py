from invenio_records_resources.services.records.components import ServiceComponent
from marshmallow import ValidationError


class TitleRequiredOnPublish(ServiceComponent):
    """Rejects publication if the record's title is absent or blank.

    Used by PLT-018-b to verify that the pre-publish service-component
    hook mechanism can intercept and block a publication attempt.
    """

    def publish(self, identity, data=None, record=None, **kwargs):
        title = (record.get("metadata") or {}).get("title", "")
        if not (title and title.strip()):
            raise ValidationError(
                {"metadata": {"title": ["Title is required before publishing."]}}
            )
