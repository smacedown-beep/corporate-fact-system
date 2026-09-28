"""
Data Lineage Graph Tracker.
Enables full cryptographic backtracking from Composite / Derived metrics
all the way to the official raw file, hash, and source provider.
"""
from typing import Dict, Any, List, Optional
from src.db.repository import ProvenanceRepository


class LineageTracker:
    def __init__(self, repository: ProvenanceRepository):
        self.repository = repository

    def trace_provenance(self, entity_id: str) -> Dict[str, Any]:
        """
        Recursively traces parent hierarchy back to RAW observations and sources.
        """
        node = {
            "entity_id": entity_id,
            "parents": []
        }

        # Query direct parents from data_lineage
        parent_links = self.repository.get_lineage_parents(entity_id)

        for link in parent_links:
            parent_id = link["parent_id"]
            parent_type = link["parent_entity_type"]
            trans_rule = link.get("transformation_rule")

            parent_info = {
                "parent_id": parent_id,
                "parent_type": parent_type,
                "transformation_rule": trans_rule
            }

            if parent_type == "RAW":
                # Fetch raw details
                raw_rows = self.repository.engine.execute_query(
                    "SELECT * FROM raw_observation WHERE raw_id = ?", (parent_id,)
                )
                if raw_rows:
                    raw_dict = dict(raw_rows[0])
                    parent_info["metric_name"] = raw_dict.get("raw_metric_name")
                    parent_info["raw_value"] = raw_dict.get("raw_value_text")
                    parent_info["availability_date"] = raw_dict.get("availability_date")
                    parent_info["receipt"] = raw_dict.get("source_record_identifier")
            else:
                # Recurse further up the DAG
                parent_info["ancestors"] = self.trace_provenance(parent_id)

            node["parents"].append(parent_info)

        return node
