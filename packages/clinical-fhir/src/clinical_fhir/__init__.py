"""FHIR interoperability adapters for Clinical Intelligence Platform."""

from .adapter import FHIRAdapterError, prediction_request_from_bundle

__all__ = ["FHIRAdapterError", "prediction_request_from_bundle"]
