"""Test for the ProtocolEngine-based protocol API core."""
import inspect
from typing import Optional, Type, cast, Tuple

import pytest
from decoy import Decoy

from opentrons_shared_data.deck.dev_types import DeckDefinitionV3
from opentrons_shared_data.pipette.dev_types import PipetteNameType
from opentrons_shared_data.labware.dev_types import (
    LabwareDefinition as LabwareDefDict,
    LabwareUri,
)
from opentrons_shared_data.labware.labware_definition import LabwareDefinition

from opentrons.types import DeckSlotName, Mount, MountType, Point
from opentrons.hardware_control import SyncHardwareAPI, SynchronousAdapter
from opentrons.hardware_control.modules import AbstractModule
from opentrons.hardware_control.modules.types import (
    ModuleModel,
    TemperatureModuleModel,
    MagneticModuleModel,
    ThermocyclerModuleModel,
    HeaterShakerModuleModel,
)
from opentrons.protocol_engine import (
    ModuleModel as EngineModuleModel,
    DeckSlotLocation,
    ModuleLocation,
    ModuleDefinition,
    LabwareMovementStrategy,
    LoadedLabware,
    LoadedModule,
    commands,
    LabwareOffsetVector,
)
from opentrons.protocol_engine.clients import SyncClient as EngineClient
from opentrons.protocol_engine.types import Liquid as PE_Liquid, HexColor, FlowRates
from opentrons.protocol_engine.errors import LabwareNotLoadedOnModuleError
from opentrons.protocol_engine.state.labware import (
    LabwareLoadParams as EngineLabwareLoadParams,
)

from opentrons.protocol_api.core.labware import LabwareLoadParams
from opentrons.protocol_api.core.engine import (
    deck_conflict,
    ProtocolCore,
    InstrumentCore,
    LabwareCore,
    ModuleCore,
    load_labware_params,
)
from opentrons.protocol_api._liquid import Liquid
from opentrons.protocol_api.core.engine.exceptions import InvalidModuleLocationError
from opentrons.protocol_api.core.engine.module_core import (
    TemperatureModuleCore,
    MagneticModuleCore,
    ThermocyclerModuleCore,
    HeaterShakerModuleCore,
)
from opentrons.protocol_api import MAX_SUPPORTED_VERSION

from opentrons.protocols.api_support.types import APIVersion


@pytest.fixture(autouse=True)
def patch_mock_load_labware_params(
    decoy: Decoy, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock out point_calculations.py functions."""
    for name, func in inspect.getmembers(load_labware_params, inspect.isfunction):
        monkeypatch.setattr(load_labware_params, name, decoy.mock(func=func))


@pytest.fixture(autouse=True)
def patch_mock_deck_conflict_check(
    decoy: Decoy, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Replace deck_conflict.check() with a mock."""
    mock = decoy.mock(func=deck_conflict.check)
    monkeypatch.setattr(deck_conflict, "check", mock)


@pytest.fixture
def mock_engine_client(decoy: Decoy) -> EngineClient:
    """Get a mock ProtocolEngine synchronous client."""
    return decoy.mock(cls=EngineClient)


@pytest.fixture
def api_version() -> APIVersion:
    """Get an API version to apply to the interface."""
    return MAX_SUPPORTED_VERSION


@pytest.fixture
def mock_sync_module_hardware(decoy: Decoy) -> SynchronousAdapter[AbstractModule]:
    """Get a mock synchronous module hardware."""
    return decoy.mock(name="SynchronousAdapter[AbstractModule]")  # type: ignore[no-any-return]


@pytest.fixture
def mock_sync_hardware_api(decoy: Decoy) -> SyncHardwareAPI:
    """Get a mock hardware API."""
    return decoy.mock(cls=SyncHardwareAPI)


@pytest.fixture
def subject(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    api_version: APIVersion,
    mock_sync_hardware_api: SyncHardwareAPI,
) -> ProtocolCore:
    """Get a ProtocolCore test subject with its dependencies mocked out."""
    decoy.when(mock_engine_client.state.labware.get_fixed_trash_id()).then_return(
        "fixed-trash-123"
    )
    decoy.when(
        mock_engine_client.state.labware.get_definition("fixed-trash-123")
    ).then_return(
        LabwareDefinition.construct(ordering=[["A1"]])  # type: ignore[call-arg]
    )

    return ProtocolCore(
        engine_client=mock_engine_client,
        api_version=api_version,
        sync_hardware=mock_sync_hardware_api,
    )


@pytest.mark.parametrize("api_version", [APIVersion(2, 3)])
def test_api_version(
    decoy: Decoy, subject: ProtocolCore, api_version: APIVersion
) -> None:
    """Should return the protocol version."""
    assert subject.api_version == api_version


def test_fixed_trash(subject: ProtocolCore) -> None:
    """It should have a single labware core for the fixed trash."""
    result = subject.fixed_trash

    assert isinstance(result, LabwareCore)
    assert result.labware_id == "fixed-trash-123"
    assert subject.get_labware_cores() == [result]

    # verify it's the same core every time
    assert subject.fixed_trash is result


def test_get_slot_item_empty(
    decoy: Decoy, mock_engine_client: EngineClient, subject: ProtocolCore
) -> None:
    """It should return None for an empty deck slot."""
    decoy.when(
        mock_engine_client.state.geometry.get_slot_item(
            slot_name=DeckSlotName.SLOT_1,
            allowed_labware_ids={"fixed-trash-123"},
            allowed_module_ids=set(),
        )
    ).then_return(None)

    assert subject.get_slot_item(DeckSlotName.SLOT_1) is None


def test_load_instrument(
    decoy: Decoy,
    mock_sync_hardware_api: SyncHardwareAPI,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
) -> None:
    """It should issue a LoadPipette command."""
    decoy.when(
        mock_engine_client.load_pipette(
            pipette_name=PipetteNameType.P300_SINGLE, mount=MountType.LEFT
        )
    ).then_return(commands.LoadPipetteResult(pipetteId="cool-pipette"))

    decoy.when(
        mock_engine_client.state.pipettes.get_flow_rates("cool-pipette")
    ).then_return(
        FlowRates(
            default_aspirate={"1.1": 22},
            default_dispense={"3.3": 44},
            default_blow_out={"5.5": 66},
        ),
    )

    result = subject.load_instrument(
        instrument_name=PipetteNameType.P300_SINGLE, mount=Mount.LEFT
    )

    assert isinstance(result, InstrumentCore)
    assert result.pipette_id == "cool-pipette"


def test_load_labware(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
) -> None:
    """It should issue a LoadLabware command."""
    decoy.when(
        mock_engine_client.state.labware.find_custom_labware_load_params()
    ).then_return([EngineLabwareLoadParams("hello", "world", 654)])

    decoy.when(
        load_labware_params.resolve(
            "some_labware",
            "a_namespace",
            456,
            [EngineLabwareLoadParams("hello", "world", 654)],
        )
    ).then_return(("some_namespace", 9001))

    decoy.when(
        mock_engine_client.load_labware(
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_5),
            load_name="some_labware",
            display_name="some_display_name",
            namespace="some_namespace",
            version=9001,
        )
    ).then_return(
        commands.LoadLabwareResult(
            labwareId="abc123",
            definition=LabwareDefinition.construct(),  # type: ignore[call-arg]
            offsetId=None,
        )
    )

    decoy.when(mock_engine_client.state.labware.get_definition("abc123")).then_return(
        LabwareDefinition.construct(ordering=[])  # type: ignore[call-arg]
    )

    result = subject.load_labware(
        load_name="some_labware",
        location=DeckSlotName.SLOT_5,
        label="some_display_name",  # maps to optional display name
        namespace="a_namespace",
        version=456,
    )

    assert isinstance(result, LabwareCore)
    assert result.labware_id == "abc123"
    assert subject.get_labware_cores() == [subject.fixed_trash, result]

    decoy.verify(
        deck_conflict.check(
            engine_state=mock_engine_client.state,
            existing_labware_ids=["fixed-trash-123"],
            existing_module_ids=[],
            new_labware_id="abc123",
        )
    )

    decoy.when(
        mock_engine_client.state.geometry.get_slot_item(
            slot_name=DeckSlotName.SLOT_5,
            allowed_labware_ids={"fixed-trash-123", "abc123"},
            allowed_module_ids=set(),
        )
    ).then_return(
        LoadedLabware.construct(id="abc123")  # type: ignore[call-arg]
    )

    assert subject.get_slot_item(DeckSlotName.SLOT_5) is result


@pytest.mark.parametrize(
    argnames=["use_gripper", "expected_strategy"],
    argvalues=[
        (True, LabwareMovementStrategy.USING_GRIPPER),
        (False, LabwareMovementStrategy.MANUAL_MOVE_WITH_PAUSE),
    ],
)
@pytest.mark.parametrize(
    argnames=[
        "use_pick_up_location_lpc_offset",
        "use_drop_location_lpc_offset",
        "pick_up_offset",
        "drop_offset",
    ],
    argvalues=[
        (False, False, None, None),
        (True, False, None, None),
        (False, True, None, (4, 5, 6)),
        (True, True, (4, 5, 6), (4, 5, 6)),
    ],
)
def test_move_labware(
    decoy: Decoy,
    subject: ProtocolCore,
    mock_engine_client: EngineClient,
    expected_strategy: LabwareMovementStrategy,
    use_gripper: bool,
    use_pick_up_location_lpc_offset: bool,
    use_drop_location_lpc_offset: bool,
    pick_up_offset: Optional[Tuple[float, float, float]],
    drop_offset: Optional[Tuple[float, float, float]],
) -> None:
    """It should issue a move labware command to the engine."""
    decoy.when(
        mock_engine_client.state.labware.get_definition("labware-id")
    ).then_return(
        LabwareDefinition.construct(ordering=[])  # type: ignore[call-arg]
    )
    labware = LabwareCore(labware_id="labware-id", engine_client=mock_engine_client)
    subject.move_labware(
        labware_core=labware,
        new_location=DeckSlotName.SLOT_5,
        use_gripper=use_gripper,
        use_pick_up_location_lpc_offset=use_pick_up_location_lpc_offset,
        use_drop_location_lpc_offset=use_drop_location_lpc_offset,
        pick_up_offset=pick_up_offset,
        drop_offset=drop_offset,
    )
    decoy.verify(
        mock_engine_client.move_labware(
            labware_id="labware-id",
            new_location=DeckSlotLocation(slotName=DeckSlotName.SLOT_5),
            strategy=expected_strategy,
            use_pick_up_location_lpc_offset=use_pick_up_location_lpc_offset,
            use_drop_location_lpc_offset=use_drop_location_lpc_offset,
            pick_up_offset=LabwareOffsetVector(x=4, y=5, z=6)
            if pick_up_offset
            else None,
            drop_offset=LabwareOffsetVector(x=4, y=5, z=6) if drop_offset else None,
        )
    )


@pytest.mark.parametrize("api_version", [APIVersion(2, 3)])
def test_load_labware_on_module(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    mock_sync_module_hardware: SynchronousAdapter[AbstractModule],
    subject: ProtocolCore,
    api_version: APIVersion,
) -> None:
    """It should issue a LoadLabware command."""
    decoy.when(
        mock_engine_client.state.labware.find_custom_labware_load_params()
    ).then_return([EngineLabwareLoadParams("hello", "world", 654)])

    decoy.when(
        load_labware_params.resolve(
            "some_labware",
            "a_namespace",
            456,
            [EngineLabwareLoadParams("hello", "world", 654)],
        )
    ).then_return(("some_namespace", 9001))

    decoy.when(
        mock_engine_client.load_labware(
            location=ModuleLocation(moduleId="module-id"),
            load_name="some_labware",
            display_name="some_display_name",
            namespace="some_namespace",
            version=9001,
        )
    ).then_return(
        commands.LoadLabwareResult(
            labwareId="abc123",
            definition=LabwareDefinition.construct(),  # type: ignore[call-arg]
            offsetId=None,
        )
    )

    decoy.when(mock_engine_client.state.labware.get_definition("abc123")).then_return(
        LabwareDefinition.construct(ordering=[])  # type: ignore[call-arg]
    )

    module_core = ModuleCore(
        module_id="module-id",
        engine_client=mock_engine_client,
        api_version=api_version,
        sync_module_hardware=mock_sync_module_hardware,
    )

    result = subject.load_labware(
        load_name="some_labware",
        location=module_core,
        label="some_display_name",  # maps to optional display name
        namespace="a_namespace",
        version=456,
    )

    assert isinstance(result, LabwareCore)
    assert result.labware_id == "abc123"

    decoy.verify(
        deck_conflict.check(
            engine_state=mock_engine_client.state,
            existing_labware_ids=["fixed-trash-123"],
            existing_module_ids=[],
            new_labware_id="abc123",
        )
    )

    decoy.when(
        mock_engine_client.state.labware.get_id_by_module("module-id")
    ).then_return("abc123")

    assert subject.get_labware_on_module(module_core) is result


def test_add_labware_definition(
    decoy: Decoy,
    minimal_labware_def: LabwareDefDict,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
) -> None:
    """It should add a labware definition to the engine."""
    decoy.when(
        mock_engine_client.add_labware_definition(
            definition=LabwareDefinition.parse_obj(minimal_labware_def)
        )
    ).then_return(LabwareUri("hello/world/123"))

    result = subject.add_labware_definition(minimal_labware_def)

    assert result == LabwareLoadParams("hello", "world", 123)


# TODO(mc, 2022-10-25): move to module core factory function
@pytest.mark.parametrize(
    ("requested_model", "engine_model", "expected_core_cls"),
    [
        (
            TemperatureModuleModel.TEMPERATURE_V1,
            EngineModuleModel.TEMPERATURE_MODULE_V1,
            TemperatureModuleCore,
        ),
        (
            TemperatureModuleModel.TEMPERATURE_V2,
            EngineModuleModel.TEMPERATURE_MODULE_V2,
            TemperatureModuleCore,
        ),
        (
            MagneticModuleModel.MAGNETIC_V1,
            EngineModuleModel.MAGNETIC_MODULE_V1,
            MagneticModuleCore,
        ),
        (
            MagneticModuleModel.MAGNETIC_V2,
            EngineModuleModel.MAGNETIC_MODULE_V2,
            MagneticModuleCore,
        ),
        (
            ThermocyclerModuleModel.THERMOCYCLER_V1,
            EngineModuleModel.THERMOCYCLER_MODULE_V1,
            ThermocyclerModuleCore,
        ),
        (
            ThermocyclerModuleModel.THERMOCYCLER_V2,
            EngineModuleModel.THERMOCYCLER_MODULE_V2,
            ThermocyclerModuleCore,
        ),
        (
            HeaterShakerModuleModel.HEATER_SHAKER_V1,
            EngineModuleModel.HEATER_SHAKER_MODULE_V1,
            HeaterShakerModuleCore,
        ),
    ],
)
def test_load_module(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    mock_sync_hardware_api: SyncHardwareAPI,
    requested_model: ModuleModel,
    engine_model: EngineModuleModel,
    expected_core_cls: Type[ModuleCore],
    subject: ProtocolCore,
) -> None:
    """It should issue a load module engine command."""
    definition = ModuleDefinition.construct()  # type: ignore[call-arg]

    mock_hw_mod_1 = decoy.mock(cls=AbstractModule)
    mock_hw_mod_2 = decoy.mock(cls=AbstractModule)

    decoy.when(mock_hw_mod_1.device_info).then_return({"serial": "abc123"})
    decoy.when(mock_hw_mod_2.device_info).then_return({"serial": "xyz789"})
    decoy.when(mock_sync_hardware_api.attached_modules).then_return(
        [mock_hw_mod_1, mock_hw_mod_2]
    )

    decoy.when(
        mock_engine_client.load_module(
            model=engine_model,
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_1),
        )
    ).then_return(
        commands.LoadModuleResult(
            moduleId="abc123",
            definition=definition,
            model=engine_model,
            serialNumber="xyz789",
        )
    )

    result = subject.load_module(
        model=requested_model,
        deck_slot=DeckSlotName.SLOT_1,
        configuration=None,
    )

    assert isinstance(result, expected_core_cls)
    assert result.module_id == "abc123"
    assert subject.get_module_cores() == [result]

    decoy.verify(
        deck_conflict.check(
            engine_state=mock_engine_client.state,
            existing_labware_ids=["fixed-trash-123"],
            existing_module_ids=[],
            new_module_id="abc123",
        )
    )

    decoy.when(
        mock_engine_client.state.geometry.get_slot_item(
            slot_name=DeckSlotName.SLOT_1,
            allowed_labware_ids={"fixed-trash-123"},
            allowed_module_ids={"abc123"},
        )
    ).then_return(
        LoadedModule.construct(id="abc123")  # type: ignore[call-arg]
    )
    decoy.when(mock_engine_client.state.labware.get_id_by_module("abc123")).then_raise(
        LabwareNotLoadedOnModuleError("oh no")
    )

    assert subject.get_slot_item(DeckSlotName.SLOT_1) is result
    assert subject.get_labware_on_module(result) is None


@pytest.mark.parametrize(
    ("requested_model", "engine_model"),
    [
        (
            ThermocyclerModuleModel.THERMOCYCLER_V1,
            EngineModuleModel.THERMOCYCLER_MODULE_V1,
        ),
        (
            ThermocyclerModuleModel.THERMOCYCLER_V2,
            EngineModuleModel.THERMOCYCLER_MODULE_V2,
        ),
    ],
)
def test_load_module_thermocycler_with_no_location(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    mock_sync_hardware_api: SyncHardwareAPI,
    requested_model: ModuleModel,
    engine_model: EngineModuleModel,
    subject: ProtocolCore,
) -> None:
    """It should issue a load module engine command with location at 7."""
    definition = ModuleDefinition.construct()  # type: ignore[call-arg]

    mock_hw_mod = decoy.mock(cls=AbstractModule)
    decoy.when(mock_hw_mod.device_info).then_return({"serial": "xyz789"})
    decoy.when(mock_sync_hardware_api.attached_modules).then_return([mock_hw_mod])

    decoy.when(
        mock_engine_client.load_module(
            model=engine_model,
            location=DeckSlotLocation(slotName=DeckSlotName.SLOT_7),
        )
    ).then_return(
        commands.LoadModuleResult(
            moduleId="abc123",
            definition=definition,
            model=engine_model,
            serialNumber="xyz789",
        )
    )

    result = subject.load_module(
        model=requested_model,
        deck_slot=None,
        configuration=None,
    )

    decoy.verify(
        deck_conflict.check(
            engine_state=mock_engine_client.state,
            existing_labware_ids=["fixed-trash-123"],
            existing_module_ids=[],
            new_module_id="abc123",
        )
    )

    assert isinstance(result, ThermocyclerModuleCore)
    assert result.module_id == "abc123"


@pytest.mark.parametrize(
    "requested_model",
    [
        HeaterShakerModuleModel.HEATER_SHAKER_V1,
        MagneticModuleModel.MAGNETIC_V1,
        MagneticModuleModel.MAGNETIC_V2,
        TemperatureModuleModel.TEMPERATURE_V1,
        TemperatureModuleModel.TEMPERATURE_V2,
    ],
)
def test_load_module_no_location(
    requested_model: ModuleModel, subject: ProtocolCore
) -> None:
    """Should raise an InvalidModuleLocationError exception."""
    with pytest.raises(InvalidModuleLocationError):
        subject.load_module(model=requested_model, deck_slot=None, configuration=None)


@pytest.mark.parametrize("message", [None, "Hello, world!", ""])
def test_pause(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
    message: Optional[str],
) -> None:
    """It should issue a waitForResume command."""
    subject.pause(msg=message)
    decoy.verify(mock_engine_client.wait_for_resume(message=message))


@pytest.mark.parametrize("seconds", [0.0, -1.23, 1.23])
@pytest.mark.parametrize("message", [None, "Hello, world!", ""])
def test_delay(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
    seconds: float,
    message: Optional[str],
) -> None:
    """It should issue a waitForDuration command."""
    subject.delay(seconds=seconds, msg=message)
    decoy.verify(mock_engine_client.wait_for_duration(seconds=seconds, message=message))


def test_comment(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
) -> None:
    """It should issue a comment command."""
    subject.comment("Hello, world!")
    decoy.verify(mock_engine_client.comment("Hello, world!"))


def test_home(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
) -> None:
    """It should home all axes."""
    subject.home()
    decoy.verify(mock_engine_client.home(axes=None), times=1)


def test_is_simulating(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
) -> None:
    """It should return if simulating."""
    decoy.when(mock_engine_client.state.config.ignore_pause).then_return(True)
    assert subject.is_simulating()


def test_set_rail_lights(
    decoy: Decoy, mock_engine_client: EngineClient, subject: ProtocolCore
) -> None:
    """It should verify a call to sync client."""
    subject.set_rail_lights(on=True)
    decoy.verify(mock_engine_client.set_rail_lights(on=True))

    subject.set_rail_lights(on=False)
    decoy.verify(mock_engine_client.set_rail_lights(on=False))


def test_get_rail_lights(
    decoy: Decoy, mock_sync_hardware_api: SyncHardwareAPI, subject: ProtocolCore
) -> None:
    """It should get rails light state."""
    decoy.when(mock_sync_hardware_api.get_lights()).then_return({"rails": True})

    result = subject.get_rail_lights_on()
    assert result is True


def test_get_deck_definition(
    decoy: Decoy, mock_engine_client: EngineClient, subject: ProtocolCore
) -> None:
    """It should return the loaded deck definition from engine state."""
    deck_definition = cast(DeckDefinitionV3, {"schemaVersion": "3"})

    decoy.when(mock_engine_client.state.labware.get_deck_definition()).then_return(
        deck_definition
    )

    result = subject.get_deck_definition()

    assert result == deck_definition


def test_get_slot_center(
    decoy: Decoy, mock_engine_client: EngineClient, subject: ProtocolCore
) -> None:
    """It should return a slot center from engine state."""
    decoy.when(
        mock_engine_client.state.labware.get_slot_center_position(DeckSlotName.SLOT_2)
    ).then_return(Point(1, 2, 3))

    result = subject.get_slot_center(DeckSlotName.SLOT_2)

    assert result == Point(1, 2, 3)


def test_get_highest_z(
    decoy: Decoy, mock_engine_client: EngineClient, subject: ProtocolCore
) -> None:
    """It should return a slot center from engine state."""
    decoy.when(
        mock_engine_client.state.geometry.get_all_labware_highest_z()
    ).then_return(9001)

    result = subject.get_highest_z()

    assert result == 9001


def test_add_liquid(
    decoy: Decoy,
    mock_engine_client: EngineClient,
    subject: ProtocolCore,
) -> None:
    """It should return the created liquid."""
    liquid = PE_Liquid.construct(
        id="water-id",
        displayName="water",
        description="water desc",
        displayColor=HexColor(__root__="#fff"),
    )

    expected_result = Liquid(
        _id="water-id",
        name="water",
        description="water desc",
        display_color="#fff",
    )

    decoy.when(
        mock_engine_client.add_liquid(
            name="water", color="#fff", description="water desc"
        )
    ).then_return(liquid)

    result = subject.define_liquid(
        name="water", description="water desc", display_color="#fff"
    )

    assert result == expected_result
