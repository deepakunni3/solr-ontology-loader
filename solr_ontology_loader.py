from ontobio.ontol_factory import OntologyFactory
import pysolr
import argparse
import networkx as nx


HAS_OBO_NAMESPACE = 'OIO:hasOBONamespace'
HAS_ALTERNATIVE_ID = 'OIO:hasAlternativeId'
CONSIDER = 'OIO:consider'

SUBCLASS_OF = 'subClassOf'
PART_OF = 'BFO:0000050'

parser = argparse.ArgumentParser(description="A simple loader that parses an ontology and loads terms (and its properties) as documents into a configured Solr core.")
parser.add_argument('--solr_url', type=str, required=True)
parser.add_argument('--ontology', type=str, required=True)
parser.add_argument('--terms', nargs='*')

cache = {}

def ancestors(ont, term, relations, reflexive=False):
    """
    Get all ancestors for a given term
    """
    global cache
    if reflexive:
        ancs = ancestors(ont, term, relations, reflexive=False)
        ancs.append(term)
        return ancs

    g = None
    if relations is None:
        g = ont.get_graph()
    else:
        key = '-'.join(relations)
        if key in cache:
            g = cache[key]
        else:
            g = ont.get_filtered_graph(relations)
            cache[key] = g

    if term in g:
        return list(nx.ancestors(g, term))
    else:
        return []

def get_closure(ont, term, relations, reflexive=False):
    """
    Get a closure for a given term
    """
    closure = ancestors(ont, term, relations=relations, reflexive=reflexive)
    return closure

def get_default_namespace(ont):
    namespace = None
    for t in ont.meta['basicPropertyValues']:
        if t['pred'] == 'http://www.geneontology.org/formats/oboInOwl#default-namespace':
            namespace = t['val']
            break
    return namespace

def load(docs):
    """
    Load docs into Solr
    """
    global solr
    solr.add(docs)

solr = None

if __name__ == "__main__":
    args = parser.parse_args()
    solr = pysolr.Solr(url=args.solr_url)

    ontology_factory = OntologyFactory()
    ontology = ontology_factory.create(args.ontology)
    default_namespace = get_default_namespace(ontology)
    terms = args.terms
    if terms is None:
        print("No terms provided. Creating Solr docs for all {} terms in {}".format(len(ontology.graph.nodes()), args.ontology))
        terms = ontology.graph.nodes()

    count = 0
    term_map = {}

    for term in terms:
        count += 1
        if term not in term_map:
            term_map[term] = {}
        # id
        term_map[term]['id'] = term
        # description
        term_map[term]['description'] = ontology.text_definition(term)
        # source
        source = ontology._get_basic_property_value(term, HAS_OBO_NAMESPACE)
        if source is None or source == 'none':
            # use default namespace
            source = default_namespace
        term_map[term]['source'] = source
        # is_obsolete
        term_map[term]['is_obsolete'] = ontology.is_obsolete(term)
        # comment
        term_map[term]['comment'] = ontology._get_meta_prop(term, 'comments')
        # synonym
        term_map[term]['synonym'] = ontology.synonyms(term)
        # alternate_id
        alt_id = ontology._get_meta_prop(term, HAS_ALTERNATIVE_ID)
        if alt_id is not None:
            term_map[term]['alternate_id'] = alt_id
        # replaced_by
        term_map[term]['replaced_by'] = ontology.replaced_by(term)
        # consider
        term_map[term]['consider'] = ontology._get_basic_property_value(term, CONSIDER)
        # subset
        term_map[term]['subset'] = ontology.subsets(term)
        # definition_xref
        definition = ontology.text_definition(term)
        if definition:
            term_map[term]['definition_xref'] = definition.xrefs
        # database_xref
        term_map[term]['database_xref'] = ontology.xrefs(term)
        # isa_closure
        term_map[term]['isa_closure'] = get_closure(ontology, term, [SUBCLASS_OF], True)
        # isa_closure_label
        term_map[term]['isa_closure_label'] = [ontology.label(x) for x in term_map[term]['isa_closure']]
        # isa_partof_closure
        term_map[term]['isa_partof_closure'] = get_closure(ontology, term, [SUBCLASS_OF, PART_OF], True)
        # isa_partof_closure_label
        term_map[term]['isa_partof_closure_label'] = [ontology.label(x) for x in term_map[term]['isa_closure']]

        if count % 1000 == 0:
            print("{} terms processed".format(count))

    docs = term_map.values()
    load(docs)

