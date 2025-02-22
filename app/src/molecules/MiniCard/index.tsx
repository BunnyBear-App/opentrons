import * as React from 'react'
import { css } from 'styled-components'
import { SPACING, Flex, COLORS, BORDERS } from '@opentrons/components'

import type { StyleProps } from '@opentrons/components'

interface MiniCardProps extends StyleProps {
  onClick: () => void
  isSelected: boolean
  children: React.ReactNode
  isError?: boolean
}
const unselectedOptionStyles = css`
  background-color: ${COLORS.white};
  border: 1px solid ${COLORS.medGreyEnabled};
  border-radius: ${BORDERS.radiusSoftCorners};
  padding: ${SPACING.spacing3};
  width: 100%;
  cursor: pointer;

  &:hover {
    border: 1px solid ${COLORS.medGreyHover};
  }
`
const selectedOptionStyles = css`
  ${unselectedOptionStyles}
  border: 1px solid ${COLORS.blueEnabled};
  background-color: ${COLORS.lightBlue};

  &:hover {
    border: 1px solid ${COLORS.blueEnabled};
    background-color: ${COLORS.lightBlue};
  }
`

const errorOptionStyles = css`
  ${selectedOptionStyles}
  border: 1px solid ${COLORS.errorEnabled};
  background-color: ${COLORS.errorBackgroundLight};

  &:hover {
    border: 1px solid ${COLORS.errorEnabled};
    background-color: ${COLORS.errorBackgroundLight};
  }
`

export function MiniCard(props: MiniCardProps): JSX.Element {
  const { children, onClick, isSelected, isError = false } = props

  const selectedWrapperStyles = isError
    ? errorOptionStyles
    : selectedOptionStyles
  const wrapperStyles = isSelected
    ? selectedWrapperStyles
    : unselectedOptionStyles

  return (
    <Flex onClick={onClick} css={wrapperStyles}>
      {children}
    </Flex>
  )
}
