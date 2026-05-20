from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import IExtensible, ISchemaExtender
from Products.Archetypes.Field import ReferenceField
from Products.Archetypes.Widget import AjaxSelectWidget
from zope.interface import implementer
from zope.component import adapter


class CoPhysiciansField(ExtensionField, ReferenceField):
    pass


@implementer(ISchemaExtender)
@adapter(IExtensible)
class CoPhysiciansExtender(object):
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
