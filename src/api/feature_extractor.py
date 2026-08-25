#!/usr/bin/env python3
"""
Feature Extractor para el Chatbot GRD
Convierte texto conversacional en el vector de 808 features del modelo Random Forest
"""

import re
import json
import pickle
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GRDFeatureExtractor:
    """
    Extrae y convierte información médica desde texto natural
    al formato de features usado por Random Forest (808 features):
    - 500 ICD-10 (diagnósticos)
    - 300 ICD-9 (procedimientos)
    - 7 grupos etarios
    - 1 sexo (binario)
    """

    def __init__(self, model_path: str = None):
        self.model_path = model_path or self._find_model_path()
        self.top_icd10 = []
        self.top_icd9 = []
        self.label_encoder = None
        self._load_resources()
        self._compile_patterns()

    def _find_model_path(self) -> str:
        base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return base

    def _load_resources(self):
        try:
            top_icd10_path = os.path.join(self.model_path, 'dataset', 'processed', 'top_500_icd10.json')
            if os.path.exists(top_icd10_path):
                with open(top_icd10_path) as f:
                    self.top_icd10 = json.load(f)
            else:
                self.top_icd10 = self._default_icd10_codes()
            top_icd9_path = os.path.join(self.model_path, 'dataset', 'processed', 'top_300_icd9.json')
            if os.path.exists(top_icd9_path):
                with open(top_icd9_path) as f:
                    self.top_icd9 = json.load(f)
            else:
                self.top_icd9 = self._default_icd9_codes()
            le_path = os.path.join(self.model_path, 'dataset', 'processed', 'label_encoder.pkl')
            if os.path.exists(le_path):
                with open(le_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
            logger.info(f"Cargados {len(self.top_icd10)} ICD-10 y {len(self.top_icd9)} ICD-9")
        except Exception as e:
            logger.warning(f"Error cargando recursos: {e}. Usando defaults.")
            self.top_icd10 = self._default_icd10_codes()
            self.top_icd9 = self._default_icd9_codes()

    def _compile_patterns(self):
        self.re_icd10 = re.compile(r'\b([A-Z]\d{2}(?:\.\d{1,2})?)\b', re.IGNORECASE)
        self.re_icd9 = re.compile(r'\b(\d{2,3}(?:\.\d{1,2})?)\b')
        self.re_edad = re.compile(r'(\d{1,3})\s*años?', re.IGNORECASE)
        self.re_sexo_m = re.compile(r'\b(masculino|hombre|varón|M[\s,)]|paciente m)', re.IGNORECASE)
        self.re_sexo_f = re.compile(r'\b(femenino|mujer|F[\s,)]|paciente f|embaraz)', re.IGNORECASE)

    def extract_from_text(self, text: str) -> Dict:
        text_lower = text.lower()
        return {
            'edad': self._extract_edad(text),
            'sexo': self._extract_sexo(text_lower),
            'icd10_codes': self._extract_icd10(text),
            'icd9_codes': self._extract_icd9(text),
            'sintomas': self._extract_sintomas(text_lower),
            'condiciones': self._extract_condiciones(text_lower),
            'es_parto': self._detecta_parto(text_lower),
            'es_urgencia': self._detecta_urgencia(text_lower)
        }

    def create_features(self, icd10_codes: List[str] = None, icd9_codes: List[str] = None, edad_num: int = None, sexo: str = None) -> Dict:
        edad_cat = self._edad_a_grupo(edad_num) if edad_num is not None else None
        return {
            'edad': edad_cat,
            'sexo': sexo,
            'icd10_codes': icd10_codes or [],
            'icd9_codes': icd9_codes or [],
            'sintomas': [],
            'condiciones': [],
            'es_parto': False,
            'es_urgencia': False
        }

    def features_to_vector(self, features: Dict) -> List[int]:
        vector = [0] * 808
        for i, code in enumerate(self.top_icd10[:500]):
            if self._code_matches(code, features['icd10_codes']):
                vector[i] = 1
        for i, code in enumerate(self.top_icd9[:300]):
            if self._code_matches(code, features['icd9_codes']):
                vector[500 + i] = 1
        edad_idx = self._edad_to_index(features['edad'])
        if edad_idx is not None:
            vector[800 + edad_idx] = 1
        if features['sexo'] == 'F':
            vector[807] = 1
        return vector

    def _extract_edad(self, text: str) -> Optional[str]:
        match = self.re_edad.search(text)
        if match:
            return self._edad_a_grupo(int(match.group(1)))
        return None

    def _edad_a_grupo(self, edad: int) -> str:
        if edad < 5:
            return '0-4'
        elif edad < 18:
            return '5-17'
        elif edad < 30:
            return '18-29'
        elif edad < 45:
            return '30-44'
        elif edad < 65:
            return '45-64'
        elif edad < 80:
            return '65-79'
        return '80+'

    def _extract_sexo(self, text: str) -> Optional[str]:
        if self.re_sexo_f.search(text):
            return 'F'
        if self.re_sexo_m.search(text):
            return 'M'
        return None

    def _extract_icd10(self, text: str) -> List[str]:
        codes = []
        for match in self.re_icd10.finditer(text.upper()):
            code = match.group(1).upper()
            if re.match(r'^[A-Z]\d{2}', code):
                codes.append(code)
        return codes

    def _extract_icd9(self, text: str) -> List[str]:
        codes = []
        for match in self.re_icd9.finditer(text):
            code = match.group(1)
            if int(code.split('.')[0]) < 100:
                codes.append(code)
        return codes

    def _extract_sintomas(self, text: str) -> List[str]:
        sintomas_db = {
            'dolor': ['dolor', 'molestia', 'malestar'],
            'fiebre': ['fiebre', 'calentura', 'temperatura'],
            'nausea': ['nausea', 'vómito', 'vomito'],
            'cansancio': ['cansancio', 'fatiga', 'agotamiento'],
            'dificultad_respirar': ['falta aire', 'dificultad respirar', 'disnea'],
        }
        encontrados = []
        for sintoma, palabras in sintomas_db.items():
            if any(p in text for p in palabras):
                encontrados.append(sintoma)
        return encontrados

    def _extract_condiciones(self, text: str) -> List[str]:
        condiciones_map = {
            'diabetes': ['diabetes', 'dm2', 'dm 2'],
            'hipertension': ['hipertension', 'presion alta', 'htn'],
            'cardiopatia': ['corazon', 'cardiopatía', 'infarto', 'angina'],
            'cancer': ['cancer', 'cáncer', 'tumor', 'neoplasia'],
            'asma': ['asma', 'broncoespasmo'],
            'epoc': ['epoc', 'enfisema', 'bronquitis cronica'],
        }
        encontradas = []
        for cond, palabras in condiciones_map.items():
            if any(p in text for p in palabras):
                encontradas.append(cond)
        return encontradas

    def _detecta_parto(self, text: str) -> bool:
        return any(word in text for word in ['parto', 'embarazo', 'gestante', 'puerpera', 'cesarea'])

    def _detecta_urgencia(self, text: str) -> bool:
        return any(word in text for word in ['urgencia', 'emergencia', 'dolor agudo', 'sospecha'])

    def _code_matches(self, template_code: str, found_codes: List[str]) -> bool:
        for fc in found_codes:
            fc_upper = fc.upper().strip()
            if fc_upper == template_code.upper():
                return True
            if template_code.upper() in fc_upper:
                return True
            if fc_upper.split('.')[0] == template_code.upper().split('.')[0]:
                return True
        return False

    def _edad_to_index(self, edad_grupo: Optional[str]) -> Optional[int]:
        mapping = {'0-4': 0, '5-17': 1, '18-29': 2, '30-44': 3, '45-64': 4, '65-79': 5, '80+': 6}
        return mapping.get(edad_grupo)

    def _default_icd10_codes(self) -> List[str]:
        return ['Z51', 'O80', 'O09', 'J18', 'E11', 'I10', 'O33', 'O26', 'O82', 'Z37', 'O60', 'O75', 'O24', 'J44', 'I21'] + ['A' + str(i).zfill(2) for i in range(10, 50)]

    def _default_icd9_codes(self) -> List[str]:
        return ['75.69', '72.0', '73.5', '73.6', '74.0', '39.95', '88.5', '87.4', '88.3', '96.7'] + [str(i) for i in range(10, 50)]

    def to_json(self, features: Dict) -> str:
        return json.dumps(features, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    extractor = GRDFeatureExtractor()
    print(extractor.extract_from_text('Paciente mujer de 35 años con diabetes tipo 2, ICD-10 E11.9'))
