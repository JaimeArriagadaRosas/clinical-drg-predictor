#!/usr/bin/env python3
"""Feature extraction compatibility layer for the historical GRD model.

The training pipeline persists its exact feature order in
``dataset/processed/metadata.pkl``. Inference uses that metadata whenever it is
available so prediction vectors cannot silently drift from the training schema.
"""

import json
import logging
import os
import pickle
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GRDFeatureExtractor:
    """Convert clinical inputs to the feature schema used during training."""

    def __init__(self, model_path: str = None):
        self.model_path = model_path or self._find_model_path()
        self.top_icd10 = []
        self.top_icd9 = []
        self.feature_names = []
        self.label_encoder = None
        self._load_resources()
        self._compile_patterns()

    def _find_model_path(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def _load_resources(self):
        try:
            processed_dir = os.path.join(self.model_path, "dataset", "processed")
            metadata_path = os.path.join(processed_dir, "metadata.pkl")

            if os.path.exists(metadata_path):
                with open(metadata_path, "rb") as metadata_file:
                    metadata = pickle.load(metadata_file)
                self.top_icd10 = list(metadata.get("diag_codes", []))
                self.top_icd9 = list(metadata.get("proc_codes", []))
                self.feature_names = list(metadata.get("feature_names", []))
            else:
                top_icd10_path = os.path.join(processed_dir, "top_500_icd10.json")
                if os.path.exists(top_icd10_path):
                    with open(top_icd10_path) as file:
                        self.top_icd10 = json.load(file)
                else:
                    self.top_icd10 = self._default_icd10_codes()

                top_icd9_path = os.path.join(processed_dir, "top_300_icd9.json")
                if os.path.exists(top_icd9_path):
                    with open(top_icd9_path) as file:
                        self.top_icd9 = json.load(file)
                else:
                    self.top_icd9 = self._default_icd9_codes()

            label_encoder_path = os.path.join(processed_dir, "label_encoder.pkl")
            if os.path.exists(label_encoder_path):
                with open(label_encoder_path, "rb") as encoder_file:
                    self.label_encoder = pickle.load(encoder_file)

            logger.info(
                "Loaded %s ICD-10, %s ICD-9 and %s ordered features",
                len(self.top_icd10),
                len(self.top_icd9),
                len(self.feature_names),
            )
        except Exception as exc:
            logger.warning("Error loading feature resources: %s. Using defaults.", exc)
            self.top_icd10 = self._default_icd10_codes()
            self.top_icd9 = self._default_icd9_codes()
            self.feature_names = []

    def _compile_patterns(self):
        self.re_icd10 = re.compile(r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b", re.IGNORECASE)
        self.re_icd9 = re.compile(r"\b(\d{2,3}(?:\.\d{1,2})?)\b")
        self.re_edad = re.compile(r"(\d{1,3})\s*años?", re.IGNORECASE)
        self.re_sexo_m = re.compile(
            r"\b(masculino|hombre|varón|M[\s,)]|paciente m)", re.IGNORECASE
        )
        self.re_sexo_f = re.compile(
            r"\b(femenino|mujer|F[\s,)]|paciente f|embaraz)", re.IGNORECASE
        )

    def extract_from_text(self, text: str) -> Dict:
        text_lower = text.lower()
        return {
            "edad": self._extract_edad(text),
            "sexo": self._extract_sexo(text_lower),
            "icd10_codes": self._extract_icd10(text),
            "icd9_codes": self._extract_icd9(text),
            "sintomas": self._extract_sintomas(text_lower),
            "condiciones": self._extract_condiciones(text_lower),
            "es_parto": self._detecta_parto(text_lower),
            "es_urgencia": self._detecta_urgencia(text_lower),
        }

    def create_features(
        self,
        icd10_codes: List[str] = None,
        icd9_codes: List[str] = None,
        edad_num: int = None,
        sexo: str = None,
    ) -> Dict:
        edad_cat = self._edad_a_grupo(edad_num) if edad_num is not None else None
        return {
            "edad": edad_cat,
            "sexo": sexo,
            "icd10_codes": icd10_codes or [],
            "icd9_codes": icd9_codes or [],
            "sintomas": [],
            "condiciones": [],
            "es_parto": False,
            "es_urgencia": False,
        }

    def features_to_vector(self, features: Dict) -> List[int]:
        if self.feature_names:
            return [self._value_for_feature(name, features) for name in self.feature_names]

        # Compatibility fallback for historical assets that predate metadata.pkl.
        # New training runs always persist metadata and therefore use the exact path above.
        vector = [0] * 808
        for i, code in enumerate(self.top_icd10[:500]):
            if self._code_matches(code, features["icd10_codes"]):
                vector[i] = 1
        for i, code in enumerate(self.top_icd9[:300]):
            if self._code_matches(code, features["icd9_codes"]):
                vector[500 + i] = 1
        edad_idx = self._edad_to_index(features["edad"])
        if edad_idx is not None:
            vector[800 + edad_idx] = 1
        if features["sexo"] == "M":
            vector[807] = 1
        return vector

    def _value_for_feature(self, feature_name: str, features: Dict) -> int:
        if feature_name.startswith("AGE_"):
            return int(feature_name == f"AGE_{features['edad']}")
        if feature_name == "SEX_MALE":
            return int(features["sexo"] == "M")
        if feature_name.startswith("DIAG_"):
            return int(self._code_matches(feature_name[5:], features["icd10_codes"]))
        if feature_name.startswith("PROC_"):
            return int(self._code_matches(feature_name[5:], features["icd9_codes"]))
        return 0

    def _extract_edad(self, text: str) -> Optional[str]:
        match = self.re_edad.search(text)
        if match:
            return self._edad_a_grupo(int(match.group(1)))
        return None

    def _edad_a_grupo(self, edad: int) -> str:
        # Mirrors pandas.cut in src/training/03_preprocessing.py:
        # bins=[0, 1, 5, 18, 40, 60, 80, 120], right=True, include_lowest=True.
        if edad <= 1:
            return "neonate"
        if edad <= 5:
            return "infant"
        if edad <= 18:
            return "child"
        if edad <= 40:
            return "young_adult"
        if edad <= 60:
            return "middle_adult"
        if edad <= 80:
            return "senior"
        return "elderly"

    def _extract_sexo(self, text: str) -> Optional[str]:
        if self.re_sexo_f.search(text):
            return "F"
        if self.re_sexo_m.search(text):
            return "M"
        return None

    def _extract_icd10(self, text: str) -> List[str]:
        codes = []
        for match in self.re_icd10.finditer(text.upper()):
            code = match.group(1).upper()
            if re.match(r"^[A-Z]\d{2}", code):
                codes.append(code)
        return codes

    def _extract_icd9(self, text: str) -> List[str]:
        codes = []
        for match in self.re_icd9.finditer(text):
            code = match.group(1)
            if int(code.split(".")[0]) < 100:
                codes.append(code)
        return codes

    def _extract_sintomas(self, text: str) -> List[str]:
        sintomas_db = {
            "dolor": ["dolor", "molestia", "malestar"],
            "fiebre": ["fiebre", "calentura", "temperatura"],
            "nausea": ["nausea", "vómito", "vomito"],
            "cansancio": ["cansancio", "fatiga", "agotamiento"],
            "dificultad_respirar": ["falta aire", "dificultad respirar", "disnea"],
        }
        encontrados = []
        for sintoma, palabras in sintomas_db.items():
            if any(palabra in text for palabra in palabras):
                encontrados.append(sintoma)
        return encontrados

    def _extract_condiciones(self, text: str) -> List[str]:
        condiciones_map = {
            "diabetes": ["diabetes", "dm2", "dm 2"],
            "hipertension": ["hipertension", "presion alta", "htn"],
            "cardiopatia": ["corazon", "cardiopatía", "infarto", "angina"],
            "cancer": ["cancer", "cáncer", "tumor", "neoplasia"],
            "asma": ["asma", "broncoespasmo"],
            "epoc": ["epoc", "enfisema", "bronquitis cronica"],
        }
        encontradas = []
        for condicion, palabras in condiciones_map.items():
            if any(palabra in text for palabra in palabras):
                encontradas.append(condicion)
        return encontradas

    def _detecta_parto(self, text: str) -> bool:
        return any(word in text for word in ["parto", "embarazo", "gestante", "puerpera", "cesarea"])

    def _detecta_urgencia(self, text: str) -> bool:
        return any(word in text for word in ["urgencia", "emergencia", "dolor agudo", "sospecha"])

    def _code_matches(self, template_code: str, found_codes: List[str]) -> bool:
        template_upper = template_code.upper().strip()
        for found_code in found_codes:
            found_upper = found_code.upper().strip()
            if found_upper == template_upper:
                return True
            if template_upper in found_upper:
                return True
            if found_upper.split(".")[0] == template_upper.split(".")[0]:
                return True
        return False

    def _edad_to_index(self, edad_grupo: Optional[str]) -> Optional[int]:
        mapping = {
            "neonate": 0,
            "infant": 1,
            "child": 2,
            "young_adult": 3,
            "middle_adult": 4,
            "senior": 5,
            "elderly": 6,
        }
        return mapping.get(edad_grupo)

    def _default_icd10_codes(self) -> List[str]:
        return [
            "Z51",
            "O80",
            "O09",
            "J18",
            "E11",
            "I10",
            "O33",
            "O26",
            "O82",
            "Z37",
            "O60",
            "O75",
            "O24",
            "J44",
            "I21",
        ] + ["A" + str(i).zfill(2) for i in range(10, 50)]

    def _default_icd9_codes(self) -> List[str]:
        return [
            "75.69",
            "72.0",
            "73.5",
            "73.6",
            "74.0",
            "39.95",
            "88.5",
            "87.4",
            "88.3",
            "96.7",
        ] + [str(i) for i in range(10, 50)]

    def to_json(self, features: Dict) -> str:
        return json.dumps(features, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    extractor = GRDFeatureExtractor()
    print(
        extractor.extract_from_text(
            "Paciente mujer de 35 años con diabetes tipo 2, ICD-10 E11.9"
        )
    )
