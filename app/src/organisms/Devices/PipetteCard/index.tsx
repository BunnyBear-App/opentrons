import * as React from 'react'
import { useTranslation } from 'react-i18next'
import {
  Box,
  Flex,
  DIRECTION_ROW,
  ALIGN_START,
  DIRECTION_COLUMN,
  SPACING,
  TYPOGRAPHY,
  COLORS,
  useOnClickOutside,
  InstrumentDiagram,
  BORDERS,
} from '@opentrons/components'
import {
  isOT3Pipette,
  NINETY_SIX_CHANNEL,
  SINGLE_MOUNT_PIPETTES,
} from '@opentrons/shared-data'
import { LEFT } from '../../../redux/pipettes'
import { OverflowBtn } from '../../../atoms/MenuList/OverflowBtn'
import { StyledText } from '../../../atoms/text'
import { useMenuHandleClickOutside } from '../../../atoms/MenuList/hooks'
import { ChangePipette } from '../../ChangePipette'
import { FLOWS } from '../../PipetteWizardFlows/constants'
import { PipetteWizardFlows } from '../../PipetteWizardFlows'
import { ChoosePipette } from '../../PipetteWizardFlows/ChoosePipette'
import { useIsOT3 } from '../hooks'
import { PipetteOverflowMenu } from './PipetteOverflowMenu'
import { PipetteSettingsSlideout } from './PipetteSettingsSlideout'
import { AboutPipetteSlideout } from './AboutPipetteSlideout'
import type {
  PipetteModelSpecs,
  PipetteMount,
  PipetteName,
} from '@opentrons/shared-data'
import type { AttachedPipette, Mount } from '../../../redux/pipettes/types'
import type {
  PipetteWizardFlow,
  SelectablePipettes,
} from '../../PipetteWizardFlows/types'
import { PipetteOffsetCalibration } from '../../../redux/calibration/api-types'

interface PipetteCardProps {
  pipetteInfo: PipetteModelSpecs | null
  pipetteId?: AttachedPipette['id'] | null
  pipetteOffsetCalibration: PipetteOffsetCalibration | null
  mount: Mount
  robotName: string
  is96ChannelAttached: boolean
}

export const PipetteCard = (props: PipetteCardProps): JSX.Element => {
  const { t } = useTranslation(['device_details', 'protocol_setup'])
  const {
    pipetteInfo,
    pipetteOffsetCalibration,
    mount,
    robotName,
    pipetteId,
    is96ChannelAttached,
  } = props
  const {
    menuOverlay,
    handleOverflowClick,
    showOverflowMenu,
    setShowOverflowMenu,
  } = useMenuHandleClickOutside()
  const isOt3 = useIsOT3(robotName)
  const pipetteName = pipetteInfo?.name
  const isOT3PipetteAttached = isOT3Pipette(pipetteName as PipetteName)
  const pipetteDisplayName = pipetteInfo?.displayName
  const pipetteOverflowWrapperRef = useOnClickOutside<HTMLDivElement>({
    onClickOutside: () => setShowOverflowMenu(false),
  })
  const [showChangePipette, setChangePipette] = React.useState(false)
  const [showSlideout, setShowSlideout] = React.useState(false)
  const [
    pipetteWizardFlow,
    setPipetteWizardFlow,
  ] = React.useState<PipetteWizardFlow | null>(null)
  const [showAttachPipette, setShowAttachPipette] = React.useState(false)
  const [showAboutSlideout, setShowAboutSlideout] = React.useState(false)

  const [
    selectedPipette,
    setSelectedPipette,
  ] = React.useState<SelectablePipettes>(SINGLE_MOUNT_PIPETTES)

  const handleChangePipette = (): void => {
    if (isOT3PipetteAttached && isOt3) {
      setPipetteWizardFlow(FLOWS.DETACH)
    } else if (!isOT3PipetteAttached && isOt3) {
      setShowAttachPipette(true)
    } else {
      setChangePipette(true)
    }
  }
  const handleCalibrate = (): void => {
    if (isOT3PipetteAttached) setPipetteWizardFlow(FLOWS.CALIBRATE)
  }
  const handleAboutSlideout = (): void => {
    setShowAboutSlideout(true)
  }
  const handleSettingsSlideout = (): void => {
    setShowSlideout(true)
  }

  const handleAttachPipette = (): void => {
    setShowAttachPipette(false)
    setPipetteWizardFlow(FLOWS.ATTACH)
  }
  return (
    <Flex
      backgroundColor={COLORS.fundamentalsBackground}
      borderRadius={BORDERS.radiusSoftCorners}
      width="100%"
      data-testid={`PipetteCard_${String(pipetteDisplayName)}`}
    >
      {showAttachPipette ? (
        <ChoosePipette
          proceed={handleAttachPipette}
          setSelectedPipette={setSelectedPipette}
          selectedPipette={selectedPipette}
          exit={() => setShowAttachPipette(false)}
        />
      ) : null}
      {pipetteWizardFlow != null ? (
        <PipetteWizardFlows
          flowType={pipetteWizardFlow}
          mount={
            //  hardcoding in LEFT mount for whenever a 96 channel is selected
            selectedPipette === NINETY_SIX_CHANNEL
              ? LEFT
              : (mount as PipetteMount)
          }
          closeFlow={() => setPipetteWizardFlow(null)}
          robotName={robotName}
          selectedPipette={
            pipetteName === 'p1000_96' ? NINETY_SIX_CHANNEL : selectedPipette
          }
        />
      ) : null}
      {showChangePipette && (
        <ChangePipette
          robotName={robotName}
          mount={mount}
          closeModal={() => setChangePipette(false)}
        />
      )}
      {showSlideout && pipetteInfo != null && pipetteId != null && (
        <PipetteSettingsSlideout
          robotName={robotName}
          pipetteName={pipetteInfo.displayName}
          onCloseClick={() => setShowSlideout(false)}
          isExpanded={true}
          pipetteId={pipetteId}
        />
      )}
      {showAboutSlideout && pipetteInfo != null && pipetteId != null && (
        <AboutPipetteSlideout
          pipetteId={pipetteId}
          pipetteName={pipetteInfo.displayName}
          onCloseClick={() => setShowAboutSlideout(false)}
          isExpanded={true}
        />
      )}
      <Box
        padding={`${String(SPACING.spacing4)} ${String(SPACING.spacing3)}`}
        width="100%"
      >
        <Flex flexDirection={DIRECTION_ROW} paddingRight={SPACING.spacing3}>
          <Flex alignItems={ALIGN_START}>
            {pipetteInfo === null ? null : (
              <InstrumentDiagram
                pipetteSpecs={pipetteInfo}
                mount={mount}
                transform="scale(0.3)"
                size="3.125rem"
                transformOrigin="20% -10%"
              />
            )}
          </Flex>
          <Flex
            flexDirection={DIRECTION_COLUMN}
            flex="100%"
            paddingLeft={SPACING.spacing3}
          >
            <StyledText
              textTransform={TYPOGRAPHY.textTransformUppercase}
              color={COLORS.darkGreyEnabled}
              fontWeight={TYPOGRAPHY.fontWeightSemiBold}
              fontSize={TYPOGRAPHY.fontSizeH6}
              paddingBottom={SPACING.spacing2}
              data-testid={`PipetteCard_mount_${String(pipetteDisplayName)}`}
            >
              {is96ChannelAttached
                ? t('both_mounts')
                : t('mount', {
                    side: mount === LEFT ? t('left') : t('right'),
                  })}
            </StyledText>
            <Flex
              paddingBottom={SPACING.spacing2}
              data-testid={`PipetteCard_display_name_${String(
                pipetteDisplayName
              )}`}
            >
              <StyledText fontSize={TYPOGRAPHY.fontSizeP}>
                {pipetteDisplayName ?? t('empty')}
              </StyledText>
            </Flex>
          </Flex>
        </Flex>
      </Box>
      <Box
        alignSelf={ALIGN_START}
        padding={SPACING.spacing2}
        data-testid={`PipetteCard_overflow_btn_${String(pipetteDisplayName)}`}
      >
        <OverflowBtn aria-label="overflow" onClick={handleOverflowClick} />
      </Box>
      {showOverflowMenu && (
        <>
          <Box
            ref={pipetteOverflowWrapperRef}
            data-testid={`PipetteCard_overflow_menu_${String(
              pipetteDisplayName
            )}`}
            onClick={() => setShowOverflowMenu(false)}
          >
            <PipetteOverflowMenu
              pipetteSpecs={pipetteInfo}
              mount={mount}
              handleChangePipette={handleChangePipette}
              handleSettingsSlideout={handleSettingsSlideout}
              handleAboutSlideout={handleAboutSlideout}
              handleCalibrate={handleCalibrate}
              isPipetteCalibrated={pipetteOffsetCalibration != null}
            />
          </Box>
          {menuOverlay}
        </>
      )}
    </Flex>
  )
}
