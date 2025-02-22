import * as React from 'react'
import { renderWithProviders } from '@opentrons/components'
import { i18n } from '../../../i18n'
import { StepMeter } from '..'

const render = (props: React.ComponentProps<typeof StepMeter>) => {
  return renderWithProviders(<StepMeter {...props} />, {
    i18nInstance: i18n,
  })[0]
}

describe('StepMeter', () => {
  let props: React.ComponentProps<typeof StepMeter>

  beforeEach(() => {
    props = {
      totalSteps: 5,
      currentStep: 0,
    }
  })
  afterEach(() => {
    jest.resetAllMocks()
  })

  it('renders StepMeterBar at 0% width', () => {
    const { getByTestId } = render(props)
    getByTestId('StepMeter_StepMeterContainer')
    const bar = getByTestId('StepMeter_StepMeterBar')
    expect(bar).toHaveStyle('width: 0%')
  })

  it('renders StepMeterBar at 40% width', () => {
    props = {
      ...props,
      currentStep: 2,
    }
    const { getByTestId } = render(props)
    getByTestId('StepMeter_StepMeterContainer')
    const bar = getByTestId('StepMeter_StepMeterBar')
    expect(bar).toHaveStyle('width: 40%')
  })

  //  this case should never happen
  it('renders StepMeterBar at 100% width when currentStep is above totalStep', () => {
    props = {
      ...props,
      currentStep: 6,
    }
    const { getByTestId } = render(props)
    getByTestId('StepMeter_StepMeterContainer')
    const bar = getByTestId('StepMeter_StepMeterBar')
    expect(bar).toHaveStyle('width: 100%')
  })

  // desktop app container height 0.25rem odd app container height 0.75rem
  it('renders StepMeterContainer is varied when OnDevice option is true', () => {
    props = {
      ...props,
      currentStep: 2,
      OnDevice: true,
    }
    const { getByTestId } = render(props)
    const bar = getByTestId('StepMeter_StepMeterContainer')
    expect(bar).toHaveStyle('height : 0.75rem')
  })
})
