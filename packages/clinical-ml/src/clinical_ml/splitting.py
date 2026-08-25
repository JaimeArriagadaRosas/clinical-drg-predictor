from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass

from clinical_data.contracts import HospitalEncounter
from clinical_ml.features import FeatureDataset


@dataclass(frozen=True)
class DatasetSplit:
    train_idx: tuple[int, ...]
    validation_idx: tuple[int, ...]
    test_idx: tuple[int, ...]
    policy: str
    class_support: dict[str, dict[int, int]]


def _support(dataset: FeatureDataset, indices: tuple[int, ...]) -> dict[int, int]:
    return dict(sorted(Counter(int(dataset.y[index]) for index in indices).items()))


def split_by_patient(
    dataset: FeatureDataset,
    *,
    validation_fraction: float = 0.2,
    test_fraction: float = 0.2,
    random_state: int = 42,
) -> DatasetSplit:
    if validation_fraction < 0 or test_fraction < 0 or validation_fraction + test_fraction >= 1:
        raise ValueError("validation_fraction + test_fraction must be in [0, 1)")

    groups: dict[str, list[int]] = defaultdict(list)
    for index, patient_id in enumerate(dataset.patient_ids):
        groups[patient_id].append(index)
    patients = sorted(groups)
    if len(patients) < 3:
        raise ValueError("at least three patient groups are required for train/validation/test")

    random.Random(random_state).shuffle(patients)
    total = len(patients)
    test_count = max(1, round(total * test_fraction)) if test_fraction else 0
    validation_count = max(1, round(total * validation_fraction)) if validation_fraction else 0
    while test_count + validation_count >= total:
        if validation_count > 0:
            validation_count -= 1
        elif test_count > 0:
            test_count -= 1

    test_patients = set(patients[:test_count])
    validation_patients = set(patients[test_count : test_count + validation_count])
    train_patients = set(patients) - test_patients - validation_patients

    def indices_for(selected: set[str]) -> tuple[int, ...]:
        return tuple(sorted(index for patient in selected for index in groups[patient]))

    train = indices_for(train_patients)
    validation = indices_for(validation_patients)
    test = indices_for(test_patients)
    return DatasetSplit(
        train_idx=train,
        validation_idx=validation,
        test_idx=test,
        policy="patient-grouped",
        class_support={
            "train": _support(dataset, train),
            "validation": _support(dataset, validation),
            "test": _support(dataset, test),
        },
    )


def split_temporally(
    encounters: tuple[HospitalEncounter, ...] | list[HospitalEncounter],
    *,
    validation_fraction: float = 0.2,
    test_fraction: float = 0.2,
) -> DatasetSplit:
    items = tuple(encounters)
    if len(items) < 3:
        raise ValueError("at least three encounters are required for temporal splitting")
    if any(item.admission.admitted_at is None for item in items):
        raise ValueError("temporal split requires admitted_at for every encounter")

    ordered = sorted(range(len(items)), key=lambda index: items[index].admission.admitted_at)
    total = len(ordered)
    test_count = max(1, round(total * test_fraction)) if test_fraction else 0
    validation_count = max(1, round(total * validation_fraction)) if validation_fraction else 0
    while test_count + validation_count >= total:
        if validation_count > 0:
            validation_count -= 1
        elif test_count > 0:
            test_count -= 1
    train_end = total - validation_count - test_count
    validation_end = total - test_count

    return DatasetSplit(
        train_idx=tuple(ordered[:train_end]),
        validation_idx=tuple(ordered[train_end:validation_end]),
        test_idx=tuple(ordered[validation_end:]),
        policy="temporal",
        class_support={},
    )
