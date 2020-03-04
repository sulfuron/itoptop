class DataModel(object):
    def __init__(self, filename):
        """
        Create Data Model
        :param filename:
        """
        import re
        from lxml import etree
        xml = open(filename, encoding='utf-8', errors='replace').read()
        xml = re.sub('xmlns(:xsi|)="[^"]+"', '', xml, count=1)
        xml = re.sub('xsi:', '', xml, count=0)
        xml = bytes(bytearray(xml, encoding='utf-8'))
        self.root = etree.XML(xml)

        schemas = [node for node in self.root.xpath("//class") if 'id' in node.attrib]
        self.schemas = [schema.attrib['id'] for schema in schemas]  # TODO: get only user visible schemas  

        self.lookupsExternalFields = {}
        self.lookupLinkedSets = {}

    def lookupExternalField(self, schema):
        """
        When an external field is sent for inclusion / insertion, iTop returns an error and does not refer to the
        related item automatically.

        Thus, it is necessary to search for the item id, include it in the object to be inserted / updated and remove the field
        external.

        Example:
        Inclusion of the object below in the Organization Class occurs an error.
            {'name': 'Name', 'parent_name': 'Parent Name'}
        However, the object below inserts correctly:
            {'name': 'Name', 'parent_id': <number>}

        How is done:

        :param schema:
        :return: dict index by field = (key, lookup_schema, lookup_field)
        """

        if schema in self.lookupsExternalFields:
            return self.lookupsExternalFields[schema]
        root = self.root

        schema_lookups = {}
        fields = list(set(root.xpath("//class[@id='%s']//field[@type='AttributeExternalField']/@id" % schema)))
        for field in fields:
            key = root.xpath("//class[@id='%s']//field[@id='%s']/extkey_attcode/text()" % (schema, field))[0]
            lookup_field = \
                root.xpath("//class[@id='%s']//field[@id='%s']/target_attcode/text()" % (schema, field))[0]
            if root.xpath("//class[@id='%s']//field[@id='%s']/@type" % (schema, key))[0] == 'AttributeHierarchicalKey':
                lookup_schema = schema
            else:
                target_class = root.xpath("//class[@id='%s']//field[@id='%s']/target_class/text()" % (schema, key))[0]
                lookup_schema = target_class
            schema_lookups[field] = (key, lookup_schema, lookup_field)

        parent = root.xpath("//class[@id='%s']/parent/text()" % schema)
        if len(parent) > 0:
            parent = parent[0]
            if parent != 'cmdbAbstractObject':  # TODO: improve this
                import copy
                lookups_inheritance = copy.deepcopy(self.lookupExternalField(parent))
                lookups_inheritance.update(schema_lookups)
                schema_lookups = lookups_inheritance

        self.lookupsExternalFields[schema] = schema_lookups
        return schema_lookups

    def lookupLinkedSet(self, schema):
        """
        When a field is of the linked set type (N-N relation) it is necessary to know which class is the middle.
        :param schema:
        :return: dict index by field = (linked_class, ext_key_to_me, ext_key_to_remote)
        """

        if schema in self.lookupLinkedSets:
            return self.lookupLinkedSets[schema]
        root = self.root

        schema_lookups = {}
        fields = list(set(root.xpath("//class[@id='%s']//field[@type='AttributeLinkedSetIndirect']/@id" % schema)))
        for field in fields:
            linked_class = root.xpath("//class[@id='%s']//field[@id='%s']/linked_class/text()" % (schema, field))[0]
            ext_key_to_me = root.xpath("//class[@id='%s']//field[@id='%s']/ext_key_to_me/text()" % (schema, field))[0]
            ext_key_to_remote = \
            root.xpath("//class[@id='%s']//field[@id='%s']/ext_key_to_remote/text()" % (schema, field))[0]
            schema_lookups[field] = (linked_class, ext_key_to_me, ext_key_to_remote)

        self.lookupLinkedSets[schema] = schema_lookups
        return schema_lookups
