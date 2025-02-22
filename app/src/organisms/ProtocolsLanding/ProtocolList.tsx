import * as React from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useTranslation } from 'react-i18next'
import { css } from 'styled-components'

import {
  Box,
  Flex,
  ALIGN_CENTER,
  JUSTIFY_SPACE_BETWEEN,
  SPACING,
  DIRECTION_ROW,
  Icon,
  TYPOGRAPHY,
  BORDERS,
  POSITION_ABSOLUTE,
  COLORS,
  DIRECTION_COLUMN,
  Overlay,
} from '@opentrons/components'

import {
  getProtocolsDesktopSortKey,
  updateConfigValue,
} from '../../redux/config'
import { useSortedProtocols } from './hooks'
import { StyledText } from '../../atoms/text'
import { SecondaryButton } from '../../atoms/buttons'
import { Slideout } from '../../atoms/Slideout'
import { ChooseRobotToRunProtocolSlideout } from '../ChooseRobotToRunProtocolSlideout'
import { SendProtocolToOT3Slideout } from '../SendProtocolToOT3Slideout'
import { UploadInput } from './UploadInput'
import { ProtocolCard } from './ProtocolCard'
import { EmptyStateLinks } from './EmptyStateLinks'
import { MenuItem } from '../../atoms/MenuList/MenuItem'

import type { StoredProtocolData } from '../../redux/protocol-storage'
import type { ProtocolSort } from './hooks'
import type { Dispatch } from '../../redux/types'

const SORT_BY_BUTTON_STYLE = css`
  background-color: ${COLORS.transparent};
  cursor: pointer;
  &:hover {
    background-color: ${COLORS.medGreyHover};
  }
  &:active,
  &:focus {
    background-color: ${COLORS.medGreyEnabled};
  }
`

interface ProtocolListProps {
  storedProtocols: StoredProtocolData[]
}
export function ProtocolList(props: ProtocolListProps): JSX.Element | null {
  const [
    showImportProtocolSlideout,
    setShowImportProtocolSlideout,
  ] = React.useState<boolean>(false)
  const [
    showChooseRobotToRunProtocolSlideout,
    setShowChooseRobotToRunProtocolSlideout,
  ] = React.useState<boolean>(false)
  const [
    showSendProtocolToOT3Slideout,
    setShowSendProtocolToOT3Slideout,
  ] = React.useState<boolean>(false)
  const sortBy = useSelector(getProtocolsDesktopSortKey) ?? 'alphabetical'
  const [showSortByMenu, setShowSortByMenu] = React.useState<boolean>(false)
  const toggleSetShowSortByMenu = (): void => setShowSortByMenu(!showSortByMenu)
  const { t } = useTranslation('protocol_info')
  const { storedProtocols } = props
  const [
    selectedProtocol,
    setSelectedProtocol,
  ] = React.useState<StoredProtocolData | null>(null)

  const sortedStoredProtocols = useSortedProtocols(sortBy, storedProtocols)

  const dispatch = useDispatch<Dispatch>()

  const handleClickOutside: React.MouseEventHandler<HTMLDivElement> = e => {
    e.preventDefault()
    setShowSortByMenu(false)
  }

  const handleProtocolsSortKey = (sortKey: ProtocolSort): void => {
    dispatch(updateConfigValue('protocols.protocolsStoredSortKey', sortKey))
    setShowSortByMenu(false)
  }

  const sortByLabelType: {
    [key in ProtocolSort]: {
      label: string
    }
  } = {
    alphabetical: {
      label: t('shared:alphabetical'),
    },
    recent: {
      label: t('most_recent_updates'),
    },
    reverse: {
      label: t('shared:reverse'),
    },
    oldest: {
      label: t('oldest_updates'),
    },
  }

  const handleRunProtocol = (storedProtocol: StoredProtocolData): void => {
    setSelectedProtocol(storedProtocol)
    setShowChooseRobotToRunProtocolSlideout(true)
  }

  const handleSendProtocolToOT3 = (
    storedProtocol: StoredProtocolData
  ): void => {
    setSelectedProtocol(storedProtocol)
    setShowSendProtocolToOT3Slideout(true)
  }

  return (
    <Box padding={SPACING.spacing4}>
      {selectedProtocol != null ? (
        <>
          <ChooseRobotToRunProtocolSlideout
            onCloseClick={() => setShowChooseRobotToRunProtocolSlideout(false)}
            showSlideout={showChooseRobotToRunProtocolSlideout}
            storedProtocolData={selectedProtocol}
          />
          <SendProtocolToOT3Slideout
            isExpanded={showSendProtocolToOT3Slideout}
            onCloseClick={() => setShowSendProtocolToOT3Slideout(false)}
            storedProtocolData={selectedProtocol}
          />
        </>
      ) : null}
      <Flex
        alignItems={ALIGN_CENTER}
        justifyContent={JUSTIFY_SPACE_BETWEEN}
        marginBottom={SPACING.spacing5}
      >
        <StyledText as="h1">{t('protocols')}</StyledText>
        <Flex flexDirection={DIRECTION_ROW}>
          <Flex
            flexDirection={DIRECTION_ROW}
            alignItems={ALIGN_CENTER}
            marginRight={SPACING.spacing4}
          >
            <StyledText
              as="p"
              fontWeight={TYPOGRAPHY.fontWeightSemiBold}
              color={COLORS.darkGreyEnabled}
            >
              {t('shared:sort_by')}
            </StyledText>
            <Flex
              flexDirection={DIRECTION_ROW}
              alignItems={ALIGN_CENTER}
              borderRadius={BORDERS.radiusSoftCorners}
              marginLeft={SPACING.spacing3}
              css={SORT_BY_BUTTON_STYLE}
              onClick={toggleSetShowSortByMenu}
              data-testid="ProtocolList_SortByMenu"
            >
              <StyledText
                as="p"
                fontWeight={TYPOGRAPHY.fontWeightSemiBold}
                paddingLeft={SPACING.spacing3}
                paddingRight={SPACING.spacing2}
                paddingY={SPACING.spacing2}
                data-testid="sortBy-label"
              >
                {sortByLabelType[sortBy].label}
              </StyledText>
              <Icon
                paddingRight={SPACING.spacing3}
                height={TYPOGRAPHY.lineHeight16}
                name={showSortByMenu ? 'chevron-up' : 'chevron-down'}
              />
            </Flex>
          </Flex>
          {showSortByMenu && (
            <Flex
              zIndex={2}
              borderRadius={BORDERS.radiusSoftCorners}
              boxShadow="0px 1px 3px rgba(0, 0, 0, 0.2)"
              position={POSITION_ABSOLUTE}
              backgroundColor={COLORS.white}
              top="3.25rem"
              right="7rem"
              flexDirection={DIRECTION_COLUMN}
            >
              <MenuItem onClick={() => handleProtocolsSortKey('alphabetical')}>
                {t('shared:alphabetical')}
              </MenuItem>
              <MenuItem onClick={() => handleProtocolsSortKey('recent')}>
                {t('most_recent_updates')}
              </MenuItem>
              <MenuItem onClick={() => handleProtocolsSortKey('reverse')}>
                {t('shared:reverse')}
              </MenuItem>
              <MenuItem onClick={() => handleProtocolsSortKey('oldest')}>
                {t('oldest_updates')}
              </MenuItem>
            </Flex>
          )}
          {showSortByMenu ? (
            <Overlay
              onClick={handleClickOutside}
              backgroundColor={COLORS.transparent}
            />
          ) : null}
          <SecondaryButton onClick={() => setShowImportProtocolSlideout(true)}>
            {t('import')}
          </SecondaryButton>
        </Flex>
      </Flex>
      <Flex
        flexDirection="column"
        gridGap={SPACING.spacing3}
        marginBottom={SPACING.spacingXXL}
      >
        {sortedStoredProtocols.map(storedProtocol => (
          <ProtocolCard
            key={storedProtocol.protocolKey}
            handleRunProtocol={handleRunProtocol}
            handleSendProtocolToOT3={handleSendProtocolToOT3}
            storedProtocolData={storedProtocol}
          />
        ))}
      </Flex>
      <EmptyStateLinks title={t('create_or_download')} />
      <Slideout
        title={t('import_new_protocol')}
        isExpanded={showImportProtocolSlideout}
        onCloseClick={() => setShowImportProtocolSlideout(false)}
      >
        <Box marginTop={SPACING.spacing4}>
          <UploadInput onUpload={() => setShowImportProtocolSlideout(false)} />
        </Box>
      </Slideout>
    </Box>
  )
}
