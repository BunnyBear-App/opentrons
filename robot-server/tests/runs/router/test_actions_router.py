"""Tests for the /runs router."""
import pytest
from datetime import datetime
from decoy import Decoy

from robot_server.errors import ApiError
from robot_server.service.json_api import RequestModel
from robot_server.runs.run_store import RunNotFoundError
from robot_server.runs.run_controller import RunController, RunActionNotAllowedError

from robot_server.runs.action_models import (
    RunAction,
    RunActionType,
    RunActionCreate,
)

from robot_server.runs.router.actions_router import create_run_action


@pytest.fixture
def mock_run_controller(decoy: Decoy) -> RunController:
    """Get a fake RunController dependency."""
    return decoy.mock(cls=RunController)


async def test_create_run_action(
    decoy: Decoy,
    mock_run_controller: RunController,
) -> None:
    """It should create a run action."""
    run_id = "some-run-id"
    action_id = "some-action-id"
    created_at = datetime(year=2021, month=1, day=1)
    action_type = RunActionType.PLAY
    request_body = RequestModel(data=RunActionCreate(actionType=action_type))
    expected_result = RunAction(
        id="some-action-id",
        createdAt=created_at,
        actionType=RunActionType.PLAY,
    )

    decoy.when(
        mock_run_controller.create_action(
            action_id=action_id,
            action_type=action_type,
            created_at=created_at,
        )
    ).then_return(expected_result)

    result = await create_run_action(
        runId=run_id,
        request_body=request_body,
        run_controller=mock_run_controller,
        action_id=action_id,
        created_at=created_at,
    )

    assert result.content.data == expected_result
    assert result.status_code == 201


@pytest.mark.parametrize(
    ("exception", "expected_error_id", "expected_status_code"),
    [
        (RunActionNotAllowedError("oh no"), "RunActionNotAllowed", 409),
        (RunNotFoundError("oh no"), "RunNotFound", 404),
    ],
)
async def test_create_play_action_not_allowed(
    decoy: Decoy,
    mock_run_controller: RunController,
    exception: Exception,
    expected_error_id: str,
    expected_status_code: int,
) -> None:
    """It should 409 if the runner is not able to handle the action."""
    run_id = "some-run-id"
    action_id = "some-action-id"
    created_at = datetime(year=2021, month=1, day=1)
    action_type = RunActionType.PLAY
    request_body = RequestModel(data=RunActionCreate(actionType=action_type))

    decoy.when(
        mock_run_controller.create_action(
            action_id=action_id,
            action_type=action_type,
            created_at=created_at,
        )
    ).then_raise(exception)

    with pytest.raises(ApiError) as exc_info:
        await create_run_action(
            runId=run_id,
            request_body=request_body,
            run_controller=mock_run_controller,
            action_id=action_id,
            created_at=created_at,
        )

    assert exc_info.value.status_code == expected_status_code
    assert exc_info.value.content["errors"][0]["id"] == expected_error_id
