"""Test aspirate-in-place commands."""
import pytest
from decoy import Decoy

from opentrons.hardware_control import API as HardwareAPI

from opentrons.protocol_engine.execution import PipettingHandler
from opentrons.protocol_engine.commands.aspirate_in_place import (
    AspirateInPlaceParams,
    AspirateInPlaceResult,
    AspirateInPlaceImplementation,
)
from opentrons.protocol_engine.errors.exceptions import PipetteNotReadyToAspirateError

from opentrons.protocol_engine.state import (
    StateStore,
)


@pytest.fixture
def hardware_api(decoy: Decoy) -> HardwareAPI:
    """Get a mock in the shape of a HardwareAPI."""
    return decoy.mock(cls=HardwareAPI)


@pytest.fixture
def state_store(decoy: Decoy) -> StateStore:
    """Get a mock in the shape of a StateStore."""
    return decoy.mock(cls=StateStore)


@pytest.fixture
def pipetting(decoy: Decoy) -> PipettingHandler:
    """Get a mock in the shape of a PipettingHandler."""
    return decoy.mock(cls=PipettingHandler)


async def test_aspirate_in_place_implementation(
    decoy: Decoy,
    pipetting: PipettingHandler,
    state_store: StateStore,
    hardware_api: HardwareAPI,
) -> None:
    """It should aspirate in place."""
    subject = AspirateInPlaceImplementation(
        pipetting=pipetting,
        hardware_api=hardware_api,
        state_view=state_store,
    )

    data = AspirateInPlaceParams(
        pipetteId="pipette-id-abc",
        volume=123,
        flowRate=1.234,
    )

    decoy.when(
        pipetting.get_is_ready_to_aspirate(
            pipette_id="pipette-id-abc",
        )
    ).then_return(True)

    decoy.when(
        await pipetting.aspirate_in_place(
            pipette_id="pipette-id-abc", volume=123, flow_rate=1.234
        )
    ).then_return(123)

    result = await subject.execute(params=data)

    assert result == AspirateInPlaceResult(volume=123)


async def test_handle_aspirate_in_place_request_not_ready_to_aspirate(
    decoy: Decoy,
    pipetting: PipettingHandler,
    state_store: StateStore,
    hardware_api: HardwareAPI,
) -> None:
    """Should raise an exception for not ready to aspirate."""
    subject = AspirateInPlaceImplementation(
        pipetting=pipetting,
        hardware_api=hardware_api,
        state_view=state_store,
    )

    data = AspirateInPlaceParams(
        pipetteId="pipette-id-abc",
        volume=123,
        flowRate=1.234,
    )

    decoy.when(
        pipetting.get_is_ready_to_aspirate(
            pipette_id="pipette-id-abc",
        )
    ).then_return(False)

    with pytest.raises(
        PipetteNotReadyToAspirateError,
        match="Pipette cannot aspirate in place because of a previous blow out."
        " The first aspirate following a blow-out must be from a specific well"
        " so the plunger can be reset in a known safe position.",
    ):
        await subject.execute(params=data)
