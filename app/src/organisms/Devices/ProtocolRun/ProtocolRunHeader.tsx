import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { Link, useHistory } from 'react-router-dom'

import {
  RUN_STATUS_IDLE,
  RUN_STATUS_RUNNING,
  RUN_STATUS_PAUSE_REQUESTED,
  RUN_STATUS_PAUSED,
  RUN_STATUS_STOP_REQUESTED,
  RUN_STATUS_STOPPED,
  RUN_STATUS_FAILED,
  RUN_STATUS_FINISHING,
  RUN_STATUS_SUCCEEDED,
  RUN_STATUS_BLOCKED_BY_OPEN_DOOR,
  RunStatus,
} from '@opentrons/api-client'
import {
  useRunQuery,
  useModulesQuery,
  usePipettesQuery,
} from '@opentrons/react-api-client'
import { HEATERSHAKER_MODULE_TYPE } from '@opentrons/shared-data'
import {
  Box,
  Flex,
  Icon,
  IconName,
  useHoverTooltip,
  useInterval,
  ALIGN_CENTER,
  DIRECTION_COLUMN,
  DISPLAY_FLEX,
  JUSTIFY_CENTER,
  JUSTIFY_SPACE_BETWEEN,
  SIZE_1,
  BORDERS,
  COLORS,
  SPACING,
  TYPOGRAPHY,
  useConditionalConfirm,
  JUSTIFY_FLEX_END,
} from '@opentrons/components'

import { getBuildrootUpdateDisplayInfo } from '../../../redux/buildroot'
import { ProtocolAnalysisErrorBanner } from './ProtocolAnalysisErrorBanner'
import { ProtocolAnalysisErrorModal } from './ProtocolAnalysisErrorModal'
import { Banner } from '../../../atoms/Banner'
import { PrimaryButton, SecondaryButton } from '../../../atoms/buttons'
import { useTrackEvent } from '../../../redux/analytics'
import { getIsHeaterShakerAttached } from '../../../redux/config'
import { StyledText } from '../../../atoms/text'
import { Tooltip } from '../../../atoms/Tooltip'
import {
  useCloseCurrentRun,
  useCurrentRunId,
} from '../../../organisms/ProtocolUpload/hooks'
import { ConfirmCancelModal } from '../../../organisms/RunDetails/ConfirmCancelModal'
import { HeaterShakerIsRunningModal } from '../HeaterShakerIsRunningModal'
import {
  useRunControls,
  useRunStatus,
  useRunTimestamps,
} from '../../../organisms/RunTimeControl/hooks'
import { formatInterval } from '../../../organisms/RunTimeControl/utils'
import { useIsHeaterShakerInProtocol } from '../../ModuleCard/hooks'
import { ConfirmAttachmentModal } from '../../ModuleCard/ConfirmAttachmentModal'
import {
  useProtocolDetailsForRun,
  useProtocolAnalysisErrors,
  useRunCalibrationStatus,
  useRunCreatedAtTimestamp,
  useUnmatchedModulesForProtocol,
  useIsRobotViewable,
  useTrackProtocolRunEvent,
  useRobotAnalyticsData,
} from '../hooks'
import { formatTimestamp } from '../utils'
import { EMPTY_TIMESTAMP } from '../constants'

import type { Run } from '@opentrons/api-client'
import type { State } from '../../../redux/types'
import type { HeaterShakerModule } from '../../../redux/modules/types'
import { RunProgressMeter } from '../../RunProgressMeter'

const EQUIPMENT_POLL_MS = 5000
const CANCELLABLE_STATUSES = [
  RUN_STATUS_RUNNING,
  RUN_STATUS_PAUSED,
  RUN_STATUS_PAUSE_REQUESTED,
  RUN_STATUS_BLOCKED_BY_OPEN_DOOR,
  RUN_STATUS_IDLE,
]

interface ProtocolRunHeaderProps {
  protocolRunHeaderRef: React.RefObject<HTMLDivElement> | null
  robotName: string
  runId: string
  makeHandleJumpToStep: (index: number) => () => void
}

function RunTimer({
  runStatus,
  startedAt,
  stoppedAt,
  completedAt,
}: {
  runStatus: string | null
  startedAt: string | null
  stoppedAt: string | null
  completedAt: string | null
}): JSX.Element {
  const [now, setNow] = React.useState(Date())
  useInterval(() => setNow(Date()), 500, true)

  const endTime =
    runStatus === RUN_STATUS_STOP_REQUESTED && stoppedAt != null
      ? stoppedAt
      : completedAt ?? now

  const runTime =
    startedAt != null ? formatInterval(startedAt, endTime) : EMPTY_TIMESTAMP

  return <StyledText css={TYPOGRAPHY.pRegular}>{runTime}</StyledText>
}

export function ProtocolRunHeader({
  protocolRunHeaderRef,
  robotName,
  runId,
  makeHandleJumpToStep,
}: ProtocolRunHeaderProps): JSX.Element | null {
  const { t } = useTranslation('run_details')
  const history = useHistory()
  const createdAtTimestamp = useRunCreatedAtTimestamp(runId)
  const {
    protocolData,
    displayName,
    protocolKey,
    isProtocolAnalyzing,
  } = useProtocolDetailsForRun(runId)
  const { trackProtocolRunEvent } = useTrackProtocolRunEvent(runId)
  const robotAnalyticsData = useRobotAnalyticsData(robotName)
  const isRobotViewable = useIsRobotViewable(robotName)
  const runStatus = useRunStatus(runId)
  const { analysisErrors } = useProtocolAnalysisErrors(runId)
  const isRunCurrent = Boolean(useRunQuery(runId)?.data?.data?.current)
  const { closeCurrentRun, isClosingCurrentRun } = useCloseCurrentRun()
  // NOTE: we are polling pipettes, though not using their value directly here
  usePipettesQuery({ refetchInterval: EQUIPMENT_POLL_MS })
  const { startedAt, stoppedAt, completedAt } = useRunTimestamps(runId)

  React.useEffect(() => {
    if (protocolData != null && !isRobotViewable) {
      history.push(`/devices`)
    }
  }, [protocolData, isRobotViewable, history])

  React.useEffect(() => {
    if (runStatus === RUN_STATUS_STOPPED && isRunCurrent && runId != null) {
      trackProtocolRunEvent({
        name: 'runFinish',
        properties: {
          ...robotAnalyticsData,
        },
      })
      closeCurrentRun()
    }
  }, [runStatus, isRunCurrent, runId, closeCurrentRun])

  const startedAtTimestamp =
    startedAt != null ? formatTimestamp(startedAt) : EMPTY_TIMESTAMP

  const completedAtTimestamp =
    completedAt != null ? formatTimestamp(completedAt) : EMPTY_TIMESTAMP

  // redirect to new run after successful reset
  const onResetSuccess = (createRunResponse: Run): void =>
    history.push(
      `/devices/${robotName}/protocol-runs/${createRunResponse.data.id}/run-preview`
    )

  const { pause } = useRunControls(runId, onResetSuccess)

  const [showAnalysisErrorModal, setShowAnalysisErrorModal] = React.useState(
    false
  )
  const handleErrorModalCloseClick: React.MouseEventHandler = e => {
    e.preventDefault()
    e.stopPropagation()
    setShowAnalysisErrorModal(false)
  }
  React.useEffect(() => {
    if (analysisErrors != null && analysisErrors?.length > 0) {
      setShowAnalysisErrorModal(true)
    }
  }, [analysisErrors])

  const [
    showConfirmCancelModal,
    setShowConfirmCancelModal,
  ] = React.useState<boolean>(false)

  const handleCancelClick = (): void => {
    if (runStatus === RUN_STATUS_RUNNING) pause()
    setShowConfirmCancelModal(true)
  }

  const handleClearClick = (): void => {
    trackProtocolRunEvent({
      name: 'runFinish',
      properties: robotAnalyticsData ?? undefined,
    })
    closeCurrentRun()
  }

  return (
    <Flex
      ref={protocolRunHeaderRef}
      backgroundColor={COLORS.white}
      border={BORDERS.lineBorder}
      borderRadius={BORDERS.radiusSoftCorners}
      flexDirection={DIRECTION_COLUMN}
      gridGap={SPACING.spacing4}
      marginBottom={SPACING.spacing4}
      padding={SPACING.spacing4}
    >
      {showAnalysisErrorModal &&
        analysisErrors != null &&
        analysisErrors?.length > 0 && (
          <ProtocolAnalysisErrorModal
            displayName={displayName}
            errors={analysisErrors}
            onClose={handleErrorModalCloseClick}
            robotName={robotName}
          />
        )}

      <Flex>
        {protocolKey != null ? (
          <Link to={`/protocols/${protocolKey}`}>
            <StyledText
              as="h2"
              fontWeight={TYPOGRAPHY.fontWeightSemiBold}
              color={COLORS.blueEnabled}
            >
              {displayName}
            </StyledText>
          </Link>
        ) : (
          <StyledText as="h2" fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
            {displayName}
          </StyledText>
        )}
      </Flex>
      {analysisErrors != null && analysisErrors?.length > 0 && (
        <ProtocolAnalysisErrorBanner errors={analysisErrors} />
      )}
      {runStatus === RUN_STATUS_BLOCKED_BY_OPEN_DOOR ? (
        <Banner type="warning">{t('close_door_to_resume')}</Banner>
      ) : null}
      {runStatus === RUN_STATUS_STOPPED ? (
        <Banner type="warning">{t('run_canceled')}</Banner>
      ) : null}
      {isRunCurrent ? (
        <TerminalRunBanner
          {...{ runStatus, handleClearClick, isClosingCurrentRun }}
        />
      ) : null}
      <Box display="grid" gridTemplateColumns="4fr 3fr 3fr 4fr">
        <LabeledValue label={t('run')} value={createdAtTimestamp} />
        <LabeledValue
          label={t('status')}
          value={<DisplayRunStatus runStatus={runStatus} />}
        />
        <LabeledValue
          label={t('run_time')}
          value={
            <RunTimer {...{ runStatus, startedAt, stoppedAt, completedAt }} />
          }
        />
        <Flex justifyContent={JUSTIFY_FLEX_END}>
          <ActionButton
            runId={runId}
            robotName={robotName}
            runStatus={runStatus}
            isProtocolAnalyzing={protocolData == null || !!isProtocolAnalyzing}
          />
        </Flex>
      </Box>
      {runStatus != null ? (
        <Box
          backgroundColor={COLORS.fundamentalsBackground}
          display="grid"
          gridTemplateColumns="4fr 6fr 4fr"
          padding={SPACING.spacing3}
        >
          <LabeledValue
            label={t('protocol_start')}
            value={startedAtTimestamp}
          />
          <LabeledValue
            label={t('protocol_end')}
            value={completedAtTimestamp}
          />
          <Flex justifyContent={JUSTIFY_FLEX_END}>
            {CANCELLABLE_STATUSES.includes(runStatus) && (
              <SecondaryButton
                isDangerous
                onClick={handleCancelClick}
                disabled={isClosingCurrentRun}
              >
                {t('cancel_run')}
              </SecondaryButton>
            )}
          </Flex>
        </Box>
      ) : null}
      <RunProgressMeter {...{ makeHandleJumpToStep, runId, robotName }} />
      {showConfirmCancelModal ? (
        <ConfirmCancelModal
          onClose={() => setShowConfirmCancelModal(false)}
          runId={runId}
        />
      ) : null}
    </Flex>
  )
}

interface LabeledValueProps {
  label: string
  value: React.ReactNode
}

function LabeledValue(props: LabeledValueProps): JSX.Element {
  return (
    <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing2}>
      <StyledText as="h6">{props.label}</StyledText>
      {typeof props.value === 'string' ? (
        <StyledText as="p">{props.value}</StyledText>
      ) : (
        props.value
      )}
    </Flex>
  )
}

interface DisplayRunStatusProps {
  runStatus: RunStatus | null
}

function DisplayRunStatus(props: DisplayRunStatusProps): JSX.Element {
  const { t } = useTranslation('run_details')
  return (
    <Flex alignItems={ALIGN_CENTER}>
      {props.runStatus === RUN_STATUS_RUNNING ? (
        <Icon
          name="circle"
          color={COLORS.blueEnabled}
          size={SPACING.spacing2}
          marginRight={SPACING.spacing2}
          data-testid="running_circle"
        >
          <animate
            attributeName="fill"
            values={`${COLORS.blueEnabled}; transparent`}
            dur="1s"
            calcMode="discrete"
            repeatCount="indefinite"
          />
        </Icon>
      ) : null}
      <StyledText as="p">
        {props.runStatus != null ? t(`status_${String(props.runStatus)}`) : ''}
      </StyledText>
    </Flex>
  )
}

const START_RUN_STATUSES: RunStatus[] = [
  RUN_STATUS_IDLE,
  RUN_STATUS_PAUSED,
  RUN_STATUS_PAUSE_REQUESTED,
  RUN_STATUS_BLOCKED_BY_OPEN_DOOR,
]
const RUN_AGAIN_STATUSES: RunStatus[] = [
  RUN_STATUS_STOPPED,
  RUN_STATUS_FINISHING,
  RUN_STATUS_FAILED,
  RUN_STATUS_SUCCEEDED,
]
const DISABLED_STATUSES: RunStatus[] = [
  RUN_STATUS_FINISHING,
  RUN_STATUS_PAUSE_REQUESTED,
  RUN_STATUS_STOP_REQUESTED,
  RUN_STATUS_BLOCKED_BY_OPEN_DOOR,
]
interface ActionButtonProps {
  runId: string
  robotName: string
  runStatus: RunStatus | null
  isProtocolAnalyzing: boolean
}
function ActionButton(props: ActionButtonProps): JSX.Element {
  const { runId, robotName, runStatus, isProtocolAnalyzing } = props
  const history = useHistory()
  const { t } = useTranslation('run_details')
  const attachedModules =
    useModulesQuery({ refetchInterval: EQUIPMENT_POLL_MS })?.data?.data ?? []
  const trackEvent = useTrackEvent()
  const { trackProtocolRunEvent } = useTrackProtocolRunEvent(runId)
  const [targetProps, tooltipProps] = useHoverTooltip()
  const {
    play,
    pause,
    reset,
    isPlayRunActionLoading,
    isPauseRunActionLoading,
    isResetRunLoading,
  } = useRunControls(runId, (createRunResponse: Run): void =>
    // redirect to new run after successful reset
    history.push(
      `/devices/${robotName}/protocol-runs/${createRunResponse.data.id}/run-preview`
    )
  )
  const { missingModuleIds } = useUnmatchedModulesForProtocol(robotName, runId)
  const { complete: isCalibrationComplete } = useRunCalibrationStatus(
    robotName,
    runId
  )
  const [showIsShakingModal, setShowIsShakingModal] = React.useState<boolean>(
    false
  )
  const isSetupComplete = isCalibrationComplete && missingModuleIds.length === 0
  const isRobotOnWrongVersionOfSoftware = ['upgrade', 'downgrade'].includes(
    useSelector((state: State) => {
      return getBuildrootUpdateDisplayInfo(state, robotName)
    })?.autoUpdateAction
  )
  const currentRunId = useCurrentRunId()
  const isCurrentRun = currentRunId === runId
  const isOtherRunCurrent = currentRunId != null && currentRunId !== runId
  const isRunControlButtonDisabled =
    (isCurrentRun && !isSetupComplete) ||
    isPlayRunActionLoading ||
    isPauseRunActionLoading ||
    isResetRunLoading ||
    isOtherRunCurrent ||
    isProtocolAnalyzing ||
    (runStatus != null && DISABLED_STATUSES.includes(runStatus)) ||
    isRobotOnWrongVersionOfSoftware
  const handleProceedToRunClick = (): void => {
    trackEvent({ name: 'proceedToRun', properties: {} })
    play()
  }
  const configBypassHeaterShakerAttachmentConfirmation = useSelector(
    getIsHeaterShakerAttached
  )
  const {
    confirm: confirmAttachment,
    showConfirmation: showConfirmationModal,
    cancel: cancelExit,
  } = useConditionalConfirm(
    handleProceedToRunClick,
    !configBypassHeaterShakerAttachmentConfirmation
  )
  const robotAnalyticsData = useRobotAnalyticsData(robotName)

  const isHeaterShakerInProtocol = useIsHeaterShakerInProtocol()
  const activeHeaterShaker = attachedModules.find(
    (module): module is HeaterShakerModule =>
      module.moduleType === HEATERSHAKER_MODULE_TYPE &&
      module?.data != null &&
      module.data.speedStatus !== 'idle'
  )
  const isHeaterShakerShaking = attachedModules
    .filter(
      (module): module is HeaterShakerModule =>
        module.moduleType === HEATERSHAKER_MODULE_TYPE
    )
    .some(module => module?.data != null && module.data.speedStatus !== 'idle')

  let buttonText: string = ''
  let handleButtonClick = (): void => {}
  let buttonIconName: IconName | null = null
  let disableReason = null

  if (currentRunId === runId && !isSetupComplete) {
    disableReason = t('setup_incomplete')
  } else if (isOtherRunCurrent) {
    disableReason = t('robot_is_busy')
  } else if (isRobotOnWrongVersionOfSoftware) {
    disableReason = t('shared:a_software_update_is_available')
  }

  if (isProtocolAnalyzing) {
    buttonIconName = 'ot-spinner'
    buttonText = t('analyzing_on_robot')
  } else if (runStatus === RUN_STATUS_RUNNING) {
    buttonIconName = 'pause'
    buttonText = t('pause_run')
    handleButtonClick = (): void => {
      pause()
      trackProtocolRunEvent({ name: 'runPause' })
    }
  } else if (runStatus === RUN_STATUS_STOP_REQUESTED) {
    buttonIconName = null
    buttonText = t('canceling_run')
  } else if (runStatus != null && START_RUN_STATUSES.includes(runStatus)) {
    buttonIconName = 'play'
    buttonText =
      runStatus === RUN_STATUS_IDLE ? t('start_run') : t('resume_run')
    handleButtonClick = () => {
      if (isHeaterShakerShaking && isHeaterShakerInProtocol) {
        setShowIsShakingModal(true)
      } else if (
        isHeaterShakerInProtocol &&
        !isHeaterShakerShaking &&
        (runStatus === RUN_STATUS_IDLE || runStatus === RUN_STATUS_STOPPED)
      ) {
        confirmAttachment()
      } else {
        play()
        trackProtocolRunEvent({
          name: runStatus === RUN_STATUS_IDLE ? 'runStart' : 'runResume',
          properties:
            runStatus === RUN_STATUS_IDLE && robotAnalyticsData != null
              ? robotAnalyticsData
              : {},
        })
      }
    }
  } else if (runStatus != null && RUN_AGAIN_STATUSES.includes(runStatus)) {
    buttonIconName = 'play'
    buttonText = t('run_again')
    handleButtonClick = () => {
      reset()
      trackEvent({
        name: 'proceedToRun',
        properties: { sourceLocation: 'RunRecordDetail' },
      })
      trackProtocolRunEvent({ name: 'runAgain' })
    }
  }

  return (
    <>
      <PrimaryButton
        justifyContent={JUSTIFY_CENTER}
        alignItems={ALIGN_CENTER}
        boxShadow="none"
        display={DISPLAY_FLEX}
        padding={`${SPACING.spacingSM} ${SPACING.spacing4}`}
        disabled={isRunControlButtonDisabled}
        onClick={handleButtonClick}
        id="ProtocolRunHeader_runControlButton"
        {...targetProps}
      >
        {buttonIconName != null ? (
          <Icon
            name={buttonIconName}
            size={SIZE_1}
            marginRight={SPACING.spacing3}
            spin={isProtocolAnalyzing}
          />
        ) : null}
        <StyledText css={TYPOGRAPHY.pSemiBold}>{buttonText}</StyledText>
      </PrimaryButton>
      {disableReason != null && (
        <Tooltip tooltipProps={tooltipProps}>{disableReason}</Tooltip>
      )}
      {showIsShakingModal &&
        activeHeaterShaker != null &&
        isHeaterShakerInProtocol &&
        runId != null && (
          <HeaterShakerIsRunningModal
            closeModal={() => setShowIsShakingModal(false)}
            module={activeHeaterShaker}
            startRun={play}
          />
        )}
      {showConfirmationModal && (
        <ConfirmAttachmentModal
          onCloseClick={cancelExit}
          isProceedToRunModal={true}
          onConfirmClick={handleProceedToRunClick}
        />
      )}
    </>
  )
}

interface TerminalRunProps {
  runStatus: RunStatus | null
  handleClearClick: () => void
  isClosingCurrentRun: boolean
}
function TerminalRunBanner(props: TerminalRunProps): JSX.Element | null {
  const { runStatus, handleClearClick, isClosingCurrentRun } = props
  const { t } = useTranslation('run_details')
  if (runStatus === RUN_STATUS_FAILED || runStatus === RUN_STATUS_SUCCEEDED) {
    return (
      <Banner
        type={runStatus === RUN_STATUS_FAILED ? 'error' : 'success'}
        onCloseClick={handleClearClick}
        isCloseActionLoading={isClosingCurrentRun}
      >
        <Flex justifyContent={JUSTIFY_SPACE_BETWEEN} width="100%">
          {runStatus === RUN_STATUS_FAILED
            ? t('run_failed')
            : t('run_completed')}
        </Flex>
      </Banner>
    )
  }
  return null
}
