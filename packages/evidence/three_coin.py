"""Application input adapter for physical coin faces.

It performs no line, trigram or hexagram calculation. The UI mapping is
explicit and versioned before numeric values enter sanji-engine.
"""

COIN_FACE_MAPPING_ID = "COIN_FACES.HEADS_3_TAILS_2.V1"
COIN_FACE_MAPPING_VERSION = "1.0.0"
COIN_FACE_VALUES = {"heads": 3, "tails": 2}


def map_coin_faces(faces: list[str]) -> list[int]:
    if len(faces) != 3 or any(face not in COIN_FACE_VALUES for face in faces):
        raise ValueError("three_physical_coin_faces_required")
    return [COIN_FACE_VALUES[face] for face in faces]


def validate_six_tosses(tosses: list[dict]) -> list[dict]:
    if len(tosses) != 6 or [item.get("line_no") for item in tosses] != list(range(1, 7)):
        raise ValueError("six_lines_must_be_recorded_from_initial_to_top")
    return [
        {
            **item,
            "coin_values": map_coin_faces(item["coin_faces"]),
            "coin_face_mapping_id": COIN_FACE_MAPPING_ID,
            "coin_face_mapping_version": COIN_FACE_MAPPING_VERSION,
        }
        for item in tosses
    ]
