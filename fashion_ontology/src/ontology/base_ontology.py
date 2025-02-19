# src/ontology/base_ontology.py

from typing import Dict, List, Optional, Set
import networkx as nx
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class FashionConcept:
    def __init__(self, name: str, category: str, attributes: Dict = None, parent: str = None):
        self.name = name
        self.category = category
        self.attributes = attributes or {}
        self.parent = parent
        self.children = set()
        self.created_at = datetime.now()
        self.modified_at = datetime.now()

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'category': self.category,
            'attributes': self.attributes,
            'parent': self.parent,
            'children': list(self.children),
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }

    def update(self, attributes: Dict) -> None:
        self.attributes.update(attributes)
        self.modified_at = datetime.now()

class FashionOntology:
    def __init__(self):
        self.concepts = {}
        self.graph = nx.DiGraph()
        self._initialize_base_structure()

    def _initialize_base_structure(self):
        """Initialize the base ontology structure"""
        # Product Categories
        self.add_concept("Fashion", "root")
        
        # Main Categories
        main_categories = ["Apparel", "Footwear", "Accessories", "Beauty"]
        for category in main_categories:
            self.add_concept(category, "main_category", parent="Fashion")

        # Apparel Sub-categories
        apparel_categories = [
            "Dresses", "Tops", "Bottoms", "Outerwear", "Suits", 
            "Activewear", "Intimates", "Swimwear"
        ]
        for category in apparel_categories:
            self.add_concept(category, "sub_category", parent="Apparel")

        # Attribute Categories
        self._add_attribute_categories()

    def _add_attribute_categories(self):
        """Add core attribute categories"""
        attribute_categories = {
            "Material": ["Cotton", "Silk", "Wool", "Polyester", "Leather", "Denim"],
            "Pattern": ["Solid", "Striped", "Floral", "Checked", "Geometric"],
            "Style": ["Casual", "Formal", "Athletic", "Bohemian", "Classic"],
            "Fit": ["Regular", "Slim", "Loose", "Tailored", "Oversized"],
            "Length": ["Mini", "Midi", "Maxi", "Cropped", "Full-length"],
            "Occasion": ["Casual", "Formal", "Party", "Workwear", "Sports"],
            "Feature": ["Pockets", "Buttons", "Zippers", "Collar", "Hood"],
            "Construction": ["Woven", "Knitted", "Quilted", "Seamless"]
        }

        for category, attributes in attribute_categories.items():
            self.add_concept(category, "attribute_category", parent="Fashion")
            for attr in attributes:
                self.add_concept(attr, "attribute", parent=category)

    def add_concept(self, name: str, category: str, attributes: Dict = None, 
                   parent: str = None) -> None:
        """Add a new concept to the ontology"""
        try:
            concept = FashionConcept(name, category, attributes, parent)
            self.concepts[name] = concept
            
            # Update graph
            self.graph.add_node(name, **concept.to_dict())
            if parent:
                self.graph.add_edge(parent, name)
                if parent in self.concepts:
                    self.concepts[parent].children.add(name)
                    
            logger.info(f"Added concept: {name} under parent: {parent}")
        except Exception as e:
            logger.error(f"Error adding concept {name}: {str(e)}")
            raise

    def get_children(self, concept_name: str) -> Set[str]:
        """Get all children of a concept"""
        return self.concepts[concept_name].children if concept_name in self.concepts else set()

    def get_ancestry(self, concept_name: str) -> List[str]:
        """Get the ancestry path of a concept"""
        path = []
        current = concept_name
        while current in self.concepts and self.concepts[current].parent:
            path.append(current)
            current = self.concepts[current].parent
        path.append("Fashion")  # Add root
        return list(reversed(path))

    def find_related_concepts(self, concept_name: str, max_distance: int = 2) -> List[str]:
        """Find related concepts within a certain distance"""
        if concept_name not in self.graph:
            return []
        related = []
        for node in self.graph.nodes():
            if node != concept_name:
                try:
                    distance = nx.shortest_path_length(self.graph, concept_name, node)
                    if distance <= max_distance:
                        related.append((node, distance))
                except nx.NetworkXNoPath:
                    continue
        return [node for node, _ in sorted(related, key=lambda x: x[1])]

    def export_to_json(self, filepath: str) -> None:
        """Export the ontology to JSON"""
        data = {
            "concepts": {name: concept.to_dict() 
                        for name, concept in self.concepts.items()},
            "relationships": list(self.graph.edges())
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def import_from_json(self, filepath: str) -> None:
        """Import ontology from JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Clear existing data
        self.concepts.clear()
        self.graph.clear()
        
        # Load concepts
        for name, concept_data in data["concepts"].items():
            self.add_concept(
                name=name,
                category=concept_data["category"],
                attributes=concept_data["attributes"],
                parent=concept_data["parent"]
            )

class OntologyManager:
    def __init__(self):
        self.ontology = FashionOntology()
        self.pending_concepts = set()

    def suggest_new_concept(self, name: str, category: str, 
                          attributes: Dict = None, parent: str = None) -> bool:
        """Suggest a new concept for the ontology"""
        if name in self.ontology.concepts:
            return False
        
        concept_data = {
            "name": name,
            "category": category,
            "attributes": attributes,
            "parent": parent
        }
        self.pending_concepts.add(json.dumps(concept_data))
        return True

    def review_pending_concepts(self) -> List[Dict]:
        """Get list of pending concepts for review"""
        return [json.loads(concept) for concept in self.pending_concepts]

    def approve_concept(self, name: str) -> bool:
        """Approve a pending concept"""
        for concept_json in self.pending_concepts:
            concept = json.loads(concept_json)
            if concept["name"] == name:
                self.ontology.add_concept(
                    name=concept["name"],
                    category=concept["category"],
                    attributes=concept["attributes"],
                    parent=concept["parent"]
                )
                self.pending_concepts.remove(concept_json)
                return True
        return False