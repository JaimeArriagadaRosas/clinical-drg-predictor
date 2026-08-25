"""FHIR interoperability adapters for Clinical Intelligence Platform."""

from .adapter import FHIRAdapterError, bundle_to_encounter, prediction_request_from_bundle

__all__ = ["FHIRAdapterError", "bundle_to_encounter", "prediction_request_from_bundle"]
