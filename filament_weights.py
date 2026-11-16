from typing import NamedTuple


MINIMUM_FULL_SPOOL_WEIGHT_G = 1000


class SpoolWeights(NamedTuple):
    used_weight_g: int
    total_weight_g: int
    remaining_weight_g: int


def calculate_spool_weights(entered_weight_g: object) -> SpoolWeights:
    if (
        isinstance(entered_weight_g, bool)
        or not isinstance(entered_weight_g, int)
        or entered_weight_g <= 0
    ):
        raise ValueError("Gram bilgisi pozitif bir tam sayı olmalı.")

    if entered_weight_g < MINIMUM_FULL_SPOOL_WEIGHT_G:
        total_weight_g = MINIMUM_FULL_SPOOL_WEIGHT_G
        remaining_weight_g = entered_weight_g
    else:
        total_weight_g = entered_weight_g
        remaining_weight_g = entered_weight_g

    return SpoolWeights(
        used_weight_g=total_weight_g - remaining_weight_g,
        total_weight_g=total_weight_g,
        remaining_weight_g=remaining_weight_g,
    )
