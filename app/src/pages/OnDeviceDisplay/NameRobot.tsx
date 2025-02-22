import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { useSelector, useDispatch } from 'react-redux'
import { useFormik } from 'formik'
import { css } from 'styled-components'

import {
  Flex,
  DIRECTION_COLUMN,
  DIRECTION_ROW,
  ALIGN_CENTER,
  SPACING,
  POSITION_FIXED,
  JUSTIFY_CENTER,
  POSITION_RELATIVE,
  POSITION_ABSOLUTE,
  COLORS,
  TYPOGRAPHY,
  Icon,
} from '@opentrons/components'
import { useUpdateRobotNameMutation } from '@opentrons/react-api-client'

import {
  removeRobot,
  getConnectableRobots,
  getReachableRobots,
  getUnreachableRobots,
  getLocalRobot,
} from '../../redux/discovery'
import { useTrackEvent } from '../../redux/analytics'
import { StyledText } from '../../atoms/text'
import { InputField } from '../../atoms/InputField'
import { CustomKeyboard } from '../../atoms/SoftwareKeyboard'
import { TertiaryButton } from '../../atoms/buttons'
import { StepMeter } from '../../atoms/StepMeter'
import { ConfirmRobotName } from '../../organisms/NameRobot/ConfirmRobotName'

import type { UpdatedRobotName } from '@opentrons/api-client'
import type { State, Dispatch } from '../../redux/types'

// Note: kj 12/15/2022 the current input field is optimized for the desktop
// Need to update the InputField for the ODD app
// That will be done in another PR
const INPUT_FIELD_ODD_STYLE = css`
  padding-top: ${SPACING.spacingXXL};
  padding-bottom: ${SPACING.spacingXXL};
  font-size: 2.5rem;
  line-height: 3.25rem;
  text-align: center;
`

interface FormikErrors {
  newRobotName?: string
}

export function NameRobot(): JSX.Element {
  const { t } = useTranslation(['device_settings', 'shared'])
  const trackEvent = useTrackEvent()
  const localRobot = useSelector(getLocalRobot)
  const previousName = localRobot?.name != null ? localRobot.name : null
  const [name, setName] = React.useState<string>('')
  const [newName, setNewName] = React.useState<string>('')
  const [
    isShowConfirmRobotName,
    setIsShowConfirmRobotName,
  ] = React.useState<boolean>(false)
  const keyboardRef = React.useRef(null)
  const dispatch = useDispatch<Dispatch>()

  // check for robot name
  const connectableRobots = useSelector((state: State) =>
    getConnectableRobots(state)
  )
  const reachableRobots = useSelector((state: State) =>
    getReachableRobots(state)
  )
  const unreachableRobots = useSelector((state: State) =>
    getUnreachableRobots(state)
  )

  const formik = useFormik({
    initialValues: {
      newRobotName: '',
    },
    onSubmit: (values, { resetForm }) => {
      const newName = values.newRobotName.concat(name)
      const sameNameRobotInUnavailable = unreachableRobots.find(
        robot => robot.name === newName
      )
      if (sameNameRobotInUnavailable != null) {
        dispatch(removeRobot(sameNameRobotInUnavailable.name))
      }
      updateRobotName(newName)
      resetForm({ values: { newRobotName: '' } })
    },
    validate: values => {
      const errors: FormikErrors = {}
      const newName = values.newRobotName.concat(name)
      // In ODD users cannot input letters and numbers from software keyboard
      // so the app only checks the length of input string
      if (newName.length < 1) {
        errors.newRobotName = t('name_rule_error_too_short')
      }
      if (
        [...connectableRobots, ...reachableRobots].some(
          robot => newName === robot.name
        )
      ) {
        errors.newRobotName = t('name_rule_error_exist')
      }
      return errors
    },
  })

  const { updateRobotName, isLoading: isNaming } = useUpdateRobotNameMutation({
    onSuccess: (data: UpdatedRobotName) => {
      if (data.name != null) {
        setNewName(data.name)
        setIsShowConfirmRobotName(true)
        if (previousName != null) {
          dispatch(removeRobot(previousName))
        }
      }
    },
    onError: (error: Error) => {
      console.error('error', error.message)
    },
  })

  const handleConfirm = (): void => {
    // check robot name in the same network
    trackEvent({
      name: 'renameRobot',
      properties: {
        previousRobotName: previousName,
        newRobotName: formik.values.newRobotName,
        appType: 'OnDeviceDisplay',
      },
    })
    formik.handleSubmit()
  }

  return (
    <>
      {isShowConfirmRobotName ? (
        <ConfirmRobotName robotName={newName} />
      ) : (
        <>
          <StepMeter totalSteps={5} currentStep={4} OnDevice />
          <Flex flexDirection={DIRECTION_COLUMN} margin={SPACING.spacingXXL}>
            <Flex
              flexDirection={DIRECTION_ROW}
              alignItems={ALIGN_CENTER}
              justifyContent={JUSTIFY_CENTER}
              position={POSITION_RELATIVE}
              marginBottom="3.041875rem"
            >
              <Flex>
                <StyledText
                  fontSize="2rem"
                  fontWeight="700"
                  lineHeight="2.72375rem"
                >
                  {t('name_your_robot')}
                </StyledText>
              </Flex>

              <Flex position={POSITION_ABSOLUTE} right="0">
                <TertiaryButton
                  width="11.8125rem"
                  height="3.75rem"
                  fontSize="1.5rem"
                  fontWeight="500"
                  lineHeight="2.0425rem"
                  onClick={handleConfirm}
                >
                  {Boolean(isNaming) ? (
                    <Icon
                      name="ot-spinner"
                      size="1.25rem"
                      spin
                      marginRight={SPACING.spacing3}
                    />
                  ) : null}
                  {t('shared:confirm')}
                </TertiaryButton>
              </Flex>
            </Flex>

            <Flex
              width="100%"
              flexDirection={DIRECTION_COLUMN}
              alignItems={ALIGN_CENTER}
            >
              <StyledText
                color={COLORS.black}
                fontSize="1.375rem"
                lineHeight="1.875rem"
                fontWeight={TYPOGRAPHY.fontWeightRegular}
                marginBottom="0.75rem"
              >
                {t('name_your_robot_description')}
              </StyledText>
              <Flex
                flexDirection={DIRECTION_ROW}
                alignItems={ALIGN_CENTER}
                marginBottom="0.625rem"
                justifyContent={JUSTIFY_CENTER}
                width="100%"
              >
                <InputField
                  data-testid="name-robot_input"
                  id="newRobotName"
                  name="newRobotName"
                  type="text"
                  onChange={formik.handleChange}
                  value={name}
                  error={formik.errors.newRobotName && ''}
                  css={INPUT_FIELD_ODD_STYLE}
                />
              </Flex>
              <StyledText
                color={COLORS.darkGreyEnabled}
                fontSize="1.5rem"
                lineHeight="2.0625rem"
                fontWeight="500"
                marginBottom="0.75rem"
              >
                {t('name_rule_description')}
              </StyledText>
              {formik.errors.newRobotName && (
                <StyledText
                  fontSize="1.375rem"
                  lineHeight="1.875rem"
                  fontWeight="500"
                  color={COLORS.errorText}
                >
                  {formik.errors.newRobotName}
                </StyledText>
              )}
            </Flex>

            <Flex width="100%" position={POSITION_FIXED} left="0" bottom="0">
              <CustomKeyboard
                onChange={e => e != null && setName(e)}
                keyboardRef={keyboardRef}
              />
            </Flex>
          </Flex>
        </>
      )}
    </>
  )
}
