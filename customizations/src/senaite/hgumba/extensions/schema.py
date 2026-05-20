from archetypes.schemaextender.extender import BaseSchemaExtender
from archetypes.schemaextender.field import ExtensionField
from Products.Archetypes.Field import ReferenceField
from Products.Archetypes.Widget import AjaxSelectWidget


class CoPhysiciansField(ExtensionField, ReferenceField):
    pass


class CoPhysiciansExtender(BaseSchemaExtender):
    fields = [
        CoPhysiciansField(
            "CoPhysicians",
            multiValued=True,
            allowed_types=("Doctor",),
            relationship="senaite_hgu_co_physician",
            widget=AjaxSelectWidget(
                label="Co-Profissionais Solicitantes",
                description="Medicos ou profissionais adicionais que solicitaram a analise",
                visible={"edit": "visible", "view": "invisible"},
            ),
        )
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields
