import logging
import pickle
from pathlib import Path

from .service import GRDPredictor

logger = logging.getLogger(__name__)


def load_legacy_predictor(project_root: Path | None = None) -> GRDPredictor:
    root = project_root or Path(__file__).resolve().parents[4]
    model_path = root / "models" / "best_model.pkl"
    encoder_path = root / "dataset" / "processed" / "label_encoder.pkl"

    try:
        from src.api.feature_extractor import GRDFeatureExtractor

        with model_path.open("rb") as model_file:
            model = pickle.load(model_file)
        with encoder_path.open("rb") as encoder_file:
            label_encoder = pickle.load(encoder_file)
        extractor = GRDFeatureExtractor(model_path=str(root))
        return GRDPredictor(model, label_encoder, extractor)
    except Exception as exc:
        logger.info("GRD assets unavailable: %s", exc)
        return GRDPredictor(None, None, None)
