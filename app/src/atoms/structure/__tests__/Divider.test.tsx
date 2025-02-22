import * as React from 'react'
import { renderWithProviders, SPACING, COLORS } from '@opentrons/components'
import { Divider } from '../index'

const render = (props: React.ComponentProps<typeof Divider>) => {
  return renderWithProviders(<Divider {...props} />)[0]
}

describe('Divider', () => {
  let props: React.ComponentProps<typeof Divider>

  beforeEach(() => {
    props = {
      width: '80%',
    }
  })

  it('renders divider', () => {
    const { getByTestId } = render(props)
    const divider = getByTestId('divider')
    expect(divider).toHaveStyle(
      `borderBottom: 1px solid ${String(COLORS.medGreyEnabled)}`
    )
    expect(divider).toHaveStyle('width: 80%')
    expect(divider).toHaveStyle(`margin-top: ${String(SPACING.spacing2)}`)
    expect(divider).toHaveStyle(`margin-bottom: ${String(SPACING.spacing2)}`)
  })

  it('renders divider with additional props', () => {
    props = {
      ...props,
      width: '100%',
      color: COLORS.blueEnabled,
      marginY: 0,
      paddingX: SPACING.spacing2,
    }
    const { getByTestId } = render(props)
    const divider = getByTestId('divider')
    expect(divider).toHaveStyle(`color: ${String(COLORS.blueEnabled)}`)
    expect(divider).toHaveStyle('width: 100%')
    expect(divider).toHaveStyle('margin-top: 0')
    expect(divider).toHaveStyle('margin-bottom: 0')
    expect(divider).toHaveStyle('padding-left: 0.25rem')
    expect(divider).toHaveStyle('padding-right: 0.25rem')
  })
})
