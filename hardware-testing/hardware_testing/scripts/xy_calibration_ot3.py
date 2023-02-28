"""XY Calibration OT3."""
import asyncio
import argparse
from random import random
from typing import List

from opentrons.calibration_storage.types import AttitudeMatrix
from opentrons.config.robot_configs import save_robot_settings
from opentrons.hardware_control.ot3api import OT3API
from opentrons.hardware_control.ot3_calibration import (
    find_deck_height,
    find_slot_center_linear,
)
from opentrons.hardware_control.robot_calibration import (
    build_temporary_identity_calibration,
)
from opentrons.util import linal

from hardware_testing.opentrons_api import helpers_ot3
from hardware_testing.opentrons_api.types import Point, OT3Mount


ALIGNMENT_TOLERANCE = {"x": 0.3, "y": 0.3, "z": 0.3}

EXPECTED_POINTS = {
    1: helpers_ot3.get_slot_calibration_square_position_ot3(1),
    3: helpers_ot3.get_slot_calibration_square_position_ot3(3),
    12: helpers_ot3.get_slot_calibration_square_position_ot3(12),
}
SLOT_12_TO_SLOT_3 = Point(y=-1 * (EXPECTED_POINTS[12].y - EXPECTED_POINTS[3].y))
SLOT_3_TO_SLOT_1 = Point(x=-1 * (EXPECTED_POINTS[3].x - EXPECTED_POINTS[1].x))


def _tuplefy_cal_point_dicts(points: List[Point]) -> linal.SolvePoints:
    return (
        (
            points[0].x,
            points[0].y,
            points[0].z,
        ),
        (
            points[1].x,
            points[1].y,
            points[1].z,
        ),
        (
            points[2].x,
            points[2].y,
            points[2].z,
        ),
    )


def _calculate_attitude(expected: List[Point], actual: List[Point]) -> AttitudeMatrix:
    assert len(expected) == len(actual)
    assert len(expected) == 3
    e = _tuplefy_cal_point_dicts(expected)
    a = _tuplefy_cal_point_dicts(actual)
    attitude = linal.solve_attitude(e, a)
    # NOTE: inverse b/c firmware coordinates are inverse of deck coordinates
    # FIXME: replace with eventual API implementation
    attitude_inverse = [[m * -1.0 for m in n] for n in attitude]
    return attitude_inverse


async def _find_slot(api: OT3API, mount: OT3Mount, expected: Point) -> Point:
    print(f"Expected: {expected}")
    if not api.is_simulator:
        z_height = await find_deck_height(api, mount, expected)
        actual = await find_slot_center_linear(
            api, mount, expected._replace(z=z_height)
        )
    else:
        actual = expected + Point(x=random(), y=random(), z=random())
    await api.remove_tip(mount)
    print(f"Actual: {actual}")
    return actual


def _check_gantry_alignment(actual_points: List[Point]) -> None:
    _points = {
        "x": [actual_points[1].x, actual_points[2].x],  # slot 3 and 12
        "y": [actual_points[0].y, actual_points[1].y],  # slots 1 and 3
        "z": [p.z for p in actual_points],  # all slots
    }
    _diffs = {
        ax: max(point_list) - min(point_list) for ax, point_list in _points.items()
    }
    _aligned = {ax: _diff < ALIGNMENT_TOLERANCE[ax] for ax, _diff in _diffs.items()}
    if False in list(_aligned.values()):
        raise RuntimeError(f"gantry not aligned: {_points}")
    return


async def _main(is_simulating: bool, mount: OT3Mount, erase: bool = False) -> None:
    api = await helpers_ot3.build_async_ot3_hardware_api(
        is_simulating=is_simulating,
        pipette_left="p50_single_v3.3",
        pipette_right="p1000_multi_v3.3",
    )
    if not api.is_simulator:
        input("attach probe, then press ENTER")
    await api.add_tip(mount, tip_length=helpers_ot3.CALIBRATION_PROBE_EVT.length)
    print(api.config.deck_transform)

    # run using default attitude matrix
    api.set_robot_calibration(build_temporary_identity_calibration())
    print(api.config.deck_transform)

    # erase old calibration by overwriting w/ default
    if erase and not api.is_simulator:
        save_robot_settings(api.config)

    # probe slots
    await api.home()
    actual_12 = await _find_slot(api, mount, EXPECTED_POINTS[12])
    actual_3 = await _find_slot(api, mount, actual_12 + SLOT_12_TO_SLOT_3)
    actual_1 = await _find_slot(api, mount, actual_3 + SLOT_3_TO_SLOT_1)

    # calculate new attitude matrix
    expected = [EXPECTED_POINTS[1], EXPECTED_POINTS[3], EXPECTED_POINTS[12]]
    actual = [actual_1, actual_3, actual_12]
    try:
        _check_gantry_alignment(actual)
    except RuntimeError as e:
        # FIXME: don't swallow error once robot alignment is reliable across units
        print(e)
        if not api.is_simulator:
            input("press ENTER if you wish to continue")
    attitude = _calculate_attitude(expected, actual)
    print(attitude)

    # reset OT3API calibration, using modified config
    api._config.deck_transform = attitude
    api.reset_robot_calibration()
    print(api.config.deck_transform)

    # save config to disk
    if not api.is_simulator:
        save_robot_settings(api.config)

    await api.home()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--erase", action="store_true")
    parser.add_argument(
        "--mount", "-m", choices=["left", "right", "gripper"], required=True
    )
    args = parser.parse_args()
    ot3_mounts = {
        "left": OT3Mount.LEFT,
        "right": OT3Mount.RIGHT,
        "gripper": OT3Mount.GRIPPER,
    }
    _mount = ot3_mounts[args.mount]
    asyncio.run(_main(args.simulate, _mount, args.erase))
