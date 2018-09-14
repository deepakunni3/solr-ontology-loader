# solr-ontology-loader

A simple loader that parses an ontology and loads terms (and its properties) as documents into a configured Solr core.


### Setting up environment
```
python3 -m venv working-environment
source working-environment/bin/activate
pip install -r requirements.txt
```

### Running the loader
```
python solr_ontology_loader.py --ontology <ONTOLOGY> --solr_url http://localhost:8983/solr/core
```

`<ONTOLOGY>` is an ontology OBO file (requires Owltools to be in your `PATH`).
