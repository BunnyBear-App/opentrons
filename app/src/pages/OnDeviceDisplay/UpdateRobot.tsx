import * as React from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { Flex, SPACING } from '@opentrons/components'

import { getLocalRobot } from '../../redux/discovery'
import {
  getBuildrootUpdateAvailable,
  getBuildrootSession,
  startBuildrootUpdate,
} from '../../redux/buildroot'
import { UNREACHABLE } from '../../redux/discovery/constants'
import { CheckUpdates } from '../../organisms/UpdateRobotSoftware/CheckUpdates'
import { CompleteUpdateSoftware } from '../../organisms/UpdateRobotSoftware/CompleteUpdateSoftware'
import { ErrorUpdateSoftware } from '../../organisms/UpdateRobotSoftware/ErrorUpdateSoftware'
import { NoUpdateFound } from '../../organisms/UpdateRobotSoftware/NoUpdateFound'
import { UpdateSoftware } from '../../organisms/UpdateRobotSoftware/UpdateSoftware'

import type { Dispatch, State } from '../../redux/types'

const CHECK_UPDATES_DURATION = 10000 // Note: kj 1/10/2023 Currently set 10 sec later we may use a status from state

export function UpdateRobot(): JSX.Element {
  const [
    isShowCheckingUpdates,
    setIsShowCheckingUpdates,
  ] = React.useState<boolean>(true)
  const [isDownloading, setIsDownloading] = React.useState<boolean>(false)
  const localRobot = useSelector(getLocalRobot)
  const robotName = localRobot?.name != null ? localRobot.name : 'no name'
  const robotUpdateType = useSelector((state: State) => {
    return localRobot != null && localRobot.status !== UNREACHABLE
      ? getBuildrootUpdateAvailable(state, localRobot)
      : null
  })

  const session = useSelector(getBuildrootSession)
  const { step, stage, progress, error: sessionError } = session ?? {
    step: null,
    error: null,
  }
  const dispatch = useDispatch<Dispatch>()

  const softwareUpdateProcess = (): JSX.Element => {
    // Display Error screen
    if (sessionError != null) {
      return (
        <ErrorUpdateSoftware
          errorMessage={sessionError}
          robotName={robotName}
        />
      )
    }
    let updateType:
      | 'downloading'
      | 'validating'
      | 'sendingFile'
      | 'installing'
      | null = null
    if (step === 'finished') {
      return <CompleteUpdateSoftware robotName={robotName} />
    } else {
      if (isDownloading && (step === 'restart' || step === 'restarting')) {
        updateType = 'downloading'
      } else if (step === 'getToken' || step === 'uploadFile') {
        updateType = 'sendingFile'
      } else if (step === 'processFile' || step === 'commitUpdate') {
        if (stage === 'awaiting-file' || stage === 'validating') {
          updateType = 'validating'
        } else {
          updateType = 'installing'
        }
      }
      return (
        <UpdateSoftware
          updateType={updateType}
          processProgress={progress != null ? progress : 0}
        />
      )
    }
  }

  React.useEffect(() => {
    const checkUpdateTimer = setTimeout(() => {
      setIsShowCheckingUpdates(false)
    }, CHECK_UPDATES_DURATION)
    return () => {
      clearTimeout(checkUpdateTimer)
    }
  }, [])

  React.useEffect(() => {
    // check isDownloading to avoid dispatching again
    if (robotUpdateType === 'upgrade' && !isDownloading) {
      setIsDownloading(true)
      dispatch(startBuildrootUpdate(robotName))
    }
  }, [robotUpdateType, dispatch, robotName, isDownloading])

  return (
    <Flex
      padding={`${String(SPACING.spacing5)} ${String(
        SPACING.spacingXXL
      )} ${String(SPACING.spacingXXL)}`}
    >
      {isShowCheckingUpdates ? (
        <CheckUpdates />
      ) : robotUpdateType !== 'upgrade' ? (
        <NoUpdateFound />
      ) : (
        softwareUpdateProcess()
      )}
    </Flex>
  )
}
