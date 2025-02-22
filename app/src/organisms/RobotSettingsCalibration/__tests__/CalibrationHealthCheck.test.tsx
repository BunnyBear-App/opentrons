import * as React from 'react'
import { fireEvent, waitFor } from '@testing-library/react'

import { renderWithProviders } from '@opentrons/components'

import { i18n } from '../../../i18n'
import { useTrackEvent } from '../../../redux/analytics'
import {
  mockPipetteOffsetCalibration1,
  mockPipetteOffsetCalibration2,
} from '../../../redux/calibration/pipette-offset/__fixtures__'
import {
  mockTipLengthCalibration1,
  mockTipLengthCalibration2,
} from '../../../redux/calibration/tip-length/__fixtures__'
import { mockAttachedPipette } from '../../../redux/pipettes/__fixtures__'
import {
  useAttachedPipettes,
  useAttachedPipetteCalibrations,
  useRunStatuses,
} from '../../../organisms/Devices/hooks'

import { CalibrationHealthCheck } from '../CalibrationHealthCheck'

import type {
  AttachedPipettesByMount,
  PipetteCalibrationsByMount,
} from '../../../redux/pipettes/types'

jest.mock('../../../redux/analytics')
jest.mock('../../../redux/config')
jest.mock('../../../redux/pipettes')
jest.mock('../../../organisms/Devices/hooks')

const mockAttachedPipettes: AttachedPipettesByMount = {
  left: mockAttachedPipette,
  right: mockAttachedPipette,
} as any
const mockAttachedPipetteCalibrations: PipetteCalibrationsByMount = {
  left: {
    offset: mockPipetteOffsetCalibration1,
    tipLength: mockTipLengthCalibration1,
  },
  right: {
    offset: mockPipetteOffsetCalibration2,
    tipLength: mockTipLengthCalibration2,
  },
} as any
const mockUseTrackEvent = useTrackEvent as jest.MockedFunction<
  typeof useTrackEvent
>
const mockUseAttachedPipettes = useAttachedPipettes as jest.MockedFunction<
  typeof useAttachedPipettes
>
const mockUseAttachedPipetteCalibrations = useAttachedPipetteCalibrations as jest.MockedFunction<
  typeof useAttachedPipetteCalibrations
>
const mockUseRunStatuses = useRunStatuses as jest.MockedFunction<
  typeof useRunStatuses
>

const RUN_STATUSES = {
  isRunRunning: false,
  isRunStill: false,
  isRunTerminal: false,
  isRunIdle: false,
}

let mockTrackEvent: jest.Mock
const mockDispatchRequests = jest.fn()

const render = (
  props?: Partial<React.ComponentProps<typeof CalibrationHealthCheck>>
) => {
  return renderWithProviders(
    <CalibrationHealthCheck
      buttonDisabledReason={null}
      dispatchRequests={mockDispatchRequests}
      isPending={false}
      robotName="otie"
      {...props}
    />,
    {
      i18nInstance: i18n,
    }
  )
}

describe('CalibrationHealthCheck', () => {
  beforeEach(() => {
    mockTrackEvent = jest.fn()
    mockUseTrackEvent.mockReturnValue(mockTrackEvent)
    mockUseAttachedPipettes.mockReturnValue(mockAttachedPipettes)
    mockUseRunStatuses.mockReturnValue(RUN_STATUSES)
  })

  afterEach(() => {
    jest.resetAllMocks()
  })

  it('renders a title and description - Calibration Health Check section', () => {
    const [{ getByText }] = render()
    getByText('Calibration Health Check')
    getByText(
      'Check the accuracy of key calibration points without recalibrating the robot.'
    )
  })

  it('renders a Check health button', () => {
    const [{ getByRole }] = render()
    const button = getByRole('button', { name: 'Check health' })
    expect(button).not.toBeDisabled()
    fireEvent.click(button)
    expect(mockTrackEvent).toHaveBeenCalledWith({
      name: 'calibrationHealthCheckButtonClicked',
      properties: {},
    })
  })

  it('Health check button is disabled when a button disabled reason is provided', () => {
    const [{ getByRole }] = render({
      buttonDisabledReason: 'otie is unreachable',
    })
    const button = getByRole('button', { name: 'Check health' })
    expect(button).toBeDisabled()
  })

  it('Health check button is disabled when a robot is running', () => {
    mockUseRunStatuses.mockReturnValue({
      ...RUN_STATUSES,
      isRunRunning: true,
    })
    const [{ getByRole }] = render()
    const button = getByRole('button', { name: 'Check health' })
    expect(button).toBeDisabled()
  })

  it('Health check button is disabled when pipette are not set', () => {
    mockUseAttachedPipettes.mockReturnValue({ left: null, right: null })
    const [{ getByRole }] = render()
    const button = getByRole('button', { name: 'Check health' })
    expect(button).toBeDisabled()
  })

  it('Health check button shows Tooltip when pipette are not set', async () => {
    mockUseAttachedPipettes.mockReturnValue({ left: null, right: null })
    const [{ getByRole, findByText }] = render()
    const button = getByRole('button', { name: 'Check health' })
    fireEvent.mouseMove(button)
    await waitFor(() => {
      findByText(
        'Fully calibrate your robot before checking calibration health'
      )
    })
  })

  it('health check button should be disabled if there is a running protocol', () => {
    mockUseAttachedPipettes.mockReturnValue(mockAttachedPipettes)
    mockUseAttachedPipetteCalibrations.mockReturnValue(
      mockAttachedPipetteCalibrations
    )
    mockUseRunStatuses.mockReturnValue({
      ...RUN_STATUSES,
      isRunRunning: true,
    })
    const [{ getByRole }] = render()
    const button = getByRole('button', { name: 'Check health' })
    expect(button).toBeDisabled()
  })
})
