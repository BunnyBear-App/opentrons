"""XY Calibration OT3."""
import asyncio
import argparse
from random import random
from typing import List
from typing_extensions import Final

from opentrons.calibration_storage.types import AttitudeMatrix
from opentrons.config.robot_configs import save_robot_settings
from opentrons.hardware_control.ot3api import OT3API
from opentrons.hardware_control.ot3_calibration import (
    find_deck_height,
    find_slot_center_binary,
)
from opentrons.hardware_control.robot_calibration import (
    build_temporary_identity_calibration,
)
from opentrons.util import linal

from hardware_testing.opentrons_api import helpers_ot3
from hardware_testing.opentrons_api.types import Point, OT3Mount


SLOTS_TO_PROBE: Final = [1, 3, 12]


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
    return linal.solve_attitude(e, a)


async def _find_slot(api: OT3API, mount: OT3Mount, expected: Point) -> Point:
    print(f"Expected: {expected}")
    await api.add_tip(mount, tip_length=helpers_ot3.CALIBRATION_PROBE_EVT.length)
    z_height = await find_deck_height(api, mount, expected)
    actual = await find_slot_center_binary(api, mount, expected._replace(z=z_height))
    if api.is_simulator:
        random_offset = Point(x=random(), y=random(), z=random())
        actual += random_offset
    await api.remove_tip(mount)
    print(f"Actual: {actual}")
    return actual


def _check_gantry_alignment(actual_points: List[Point]) -> None:
    # TODO: - assert all Z axes are within tolerance
    #       - assert first 2x Y axes are within tolerance
    #       - assert second 2x X axes are within tolerance
    return


async def _main(is_simulating: bool, mount: OT3Mount) -> None:
    api = await helpers_ot3.build_async_ot3_hardware_api(
        is_simulating=is_simulating,
        pipette_left="p50_single_v3.3",
        pipette_right="p1000_multi_v3.3",
    )
    await api.home()

    # run using default attitude matrix
    api.set_robot_calibration(build_temporary_identity_calibration())

    # probe slots, and calculate new attitude matrix
    expected_points = [
        helpers_ot3.get_slot_calibration_square_position_ot3(slot)
        for slot in SLOTS_TO_PROBE
    ]
    actual_points = [
        await _find_slot(api, mount, expected) for expected in expected_points
    ]
    _check_gantry_alignment(actual_points)
    attitude = _calculate_attitude(expected_points, actual_points)
    print(attitude)

    # reset OT3API calibration, using modified config
    api._config.deck_transform = attitude
    api.reset_robot_calibration()

    # save config to disk
    save_robot_settings(api.config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
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
    asyncio.run(_main(args.simulate, _mount))
