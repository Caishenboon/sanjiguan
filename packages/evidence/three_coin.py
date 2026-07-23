"""Physical three-coin input validation; no hexagram interpretation."""


def line_value(faces: list[str]) -> int:
    if len(faces) != 3 or any(face not in {"heads", "tails"} for face in faces):
        raise ValueError("three_physical_coin_faces_required")
    return sum(3 if face == "heads" else 2 for face in faces)


def validate_six_tosses(tosses: list[dict]) -> list[dict]:
    if len(tosses) != 6 or [item.get("line_no") for item in tosses] != list(range(1, 7)):
        raise ValueError("six_lines_must_be_recorded_from_initial_to_top")
    return [{**item, "raw_value": line_value(item["coin_faces"])} for item in tosses]
