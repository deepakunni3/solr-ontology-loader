from ontobio.ontol_factory import OntologyFactory
import pysolr
import argparse

parser = argparse.ArgumentParser(description="A simple loader that parses an ontology and loads terms (and its properties) as documents into a configured Solr core.")
parser.add_argument('--solr_url', type=str, required=True)
parser.add_argument('--ontology', type=str, required=True)
parser.add_argument('--terms', nargs='*')

def get_closure(ont, term, relations, reflexive=False):
    closure = ont.ancestors(term, relations=relations, reflexive=reflexive)
    return closure

def load(docs):
    global solr
    solr.add(docs)

solr = None

if __name__ == "__main__":
    args = parser.parse_args()
    solr = pysolr.Solr(url=args.solr_url)

    ontology_factory = OntologyFactory()
    ontology = ontology_factory.create(args.ontology)
    terms = args.terms
    if terms is None:
        print("No terms provided. Creating Solr docs for all {} terms in {}".format(len(ontology.graph.nodes()), args.ontology))
        terms = ontology.graph.nodes()

    term_map = {}
    for term in terms:
        print("Processing term {}".format(term))
        if term not in term_map:
            term_map[term] = {}
        # id
        term_map[term]['id'] = term
        # description
        term_map[term]['description'] = ontology.text_definition(term)
        # is_obsolete
        term_map[term]['is_obsolete'] = ontology.is_obsolete(term)
        # comment
        term_map[term]['comment'] = ontology._get_meta_prop(term, 'comments')
        # synonym
        term_map[term]['synonym'] = ontology.synonyms(term)
        # TODO: alternate_id
        # replaced_by
        term_map[term]['replaced_by'] = ontology.replaced_by(term)
        # consider
        term_map[term]['consider'] = ontology._get_basic_property_value(term, 'OIO:consider')
        # subset
        term_map[term]['subset'] = ontology.subsets(term)
        # definition_xref
        definition = ontology.text_definition(term)
        if definition:
            term_map[term]['definition_xref'] = definition.xrefs
        # database_xref
        term_map[term]['database_xref'] = ontology.xrefs(term)
        # isa_closure
        term_map[term]['isa_closure'] = get_closure(ontology, term, ['subClassOf'], False)
        # isa_closure_label
        term_map[term]['isa_closure_label'] = [ontology.label(x) for x in term_map[term]['isa_closure']]
        # isa_partof_closure
        term_map[term]['isa_partof_closure'] = get_closure(ontology, term, ['subClassOf', 'BFO:0000050'], False)
        # isa_partof_closure
        term_map[term]['isa_partof_closure_label'] = [ontology.label(x) for x in term_map[term]['isa_closure']]

    docs = term_map.values()
    load(docs)


