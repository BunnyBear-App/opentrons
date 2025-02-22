import * as React from 'react'
import { useTranslation } from 'react-i18next'
import { useSelector, useDispatch } from 'react-redux'
import { Link } from 'react-router-dom'

import {
  Box,
  Flex,
  Icon,
  useInterval,
  ALIGN_CENTER,
  COLORS,
  DIRECTION_COLUMN,
  SPACING,
  TYPOGRAPHY,
} from '@opentrons/components'

import { SecondaryButton } from '../../../atoms/buttons'
import { ExternalLink } from '../../../atoms/Link/ExternalLink'
import { StyledText } from '../../../atoms/text'
import { Divider } from '../../../atoms/structure'

import {
  fetchStatus,
  fetchWifiList,
  getCanDisconnect,
  getNetworkInterfaces,
  getWifiList,
} from '../../../redux/networking'

import { useIsOT3, useIsRobotBusy } from '../hooks'
import { DisconnectModal } from './ConnectNetwork/DisconnectModal'
import { SelectNetwork } from './SelectNetwork'

import type { State, Dispatch } from '../../../redux/types'
import { Portal } from '../../../App/portal'
interface NetworkingProps {
  robotName: string
  updateRobotStatus: (isRobotBusy: boolean) => void
}

const HELP_CENTER_URL =
  'https://support.opentrons.com/s/article/Get-started-Connect-to-your-OT-2-over-USB'
const STATUS_REFRESH_MS = 5000
const LIST_REFRESH_MS = 10000

export function RobotSettingsNetworking({
  robotName,
  updateRobotStatus,
}: NetworkingProps): JSX.Element {
  const { t } = useTranslation('device_settings')
  const wifiList = useSelector((state: State) => getWifiList(state, robotName))
  const dispatch = useDispatch<Dispatch>()
  const isRobotBusy = useIsRobotBusy({ poll: true })
  const isOT3 = useIsOT3(robotName)

  const [showDisconnectModal, setShowDisconnectModal] = React.useState<boolean>(
    false
  )

  const canDisconnect = useSelector((state: State) =>
    getCanDisconnect(state, robotName)
  )

  // TODO(bh, 2023-1-18): get the real OT-3 USB connection info
  const isOT3ConnectedViaUSB = false

  const { wifi, ethernet } = useSelector((state: State) =>
    getNetworkInterfaces(state, robotName)
  )
  const activeNetwork = wifiList?.find(network => network.active)

  const ssid = activeNetwork?.ssid ?? null

  useInterval(() => dispatch(fetchStatus(robotName)), STATUS_REFRESH_MS, true)
  useInterval(() => dispatch(fetchWifiList(robotName)), LIST_REFRESH_MS, true)

  React.useEffect(() => {
    updateRobotStatus(isRobotBusy)
  }, [isRobotBusy, updateRobotStatus])

  return (
    <>
      <Portal>
        {showDisconnectModal ? (
          <DisconnectModal
            onCancel={() => setShowDisconnectModal(false)}
            robotName={robotName}
          />
        ) : null}
      </Portal>
      <Flex flexDirection={DIRECTION_COLUMN} gridGap={SPACING.spacing4}>
        <Flex alignItems={ALIGN_CENTER}>
          {wifi?.ipAddress != null ? (
            <Icon
              size="1.25rem"
              name="ot-check"
              color={COLORS.successEnabled}
              marginRight={SPACING.spacing3}
              data-testid="RobotSettings_Networking_check_circle"
            />
          ) : (
            <Box height={SPACING.spacing4} width="1.75rem"></Box>
          )}
          <Icon
            size="1.25rem"
            name="wifi"
            marginRight={wifi?.ipAddress != null ? '0.5rem' : '0.75rem'}
            data-testid="RobotSettings_Networking_wifi_icon"
          />
          <StyledText as="h3" fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
            {t('wifi')}
            {ssid != null && ` - ${ssid}`}
          </StyledText>
        </Flex>
        <Box paddingLeft="3.75rem">
          {wifi?.ipAddress != null ? (
            <>
              <Flex marginBottom={SPACING.spacing5}>
                <Flex marginRight={SPACING.spacing3}>
                  <SelectNetwork
                    robotName={robotName}
                    isRobotBusy={isRobotBusy}
                  />
                </Flex>
                {canDisconnect && !isRobotBusy ? (
                  <SecondaryButton onClick={() => setShowDisconnectModal(true)}>
                    {t('disconnect_from_wifi')}
                  </SecondaryButton>
                ) : null}
              </Flex>
              <Flex gridGap={SPACING.spacing4}>
                <Flex
                  flexDirection={DIRECTION_COLUMN}
                  gridGap={SPACING.spacing2}
                >
                  <StyledText css={TYPOGRAPHY.pSemiBold}>
                    {t('wireless_ip')}
                  </StyledText>
                  <StyledText as="p" color={COLORS.darkGrey}>
                    {wifi?.ipAddress}
                  </StyledText>
                </Flex>
                <Flex
                  flexDirection={DIRECTION_COLUMN}
                  gridGap={SPACING.spacing2}
                >
                  <StyledText css={TYPOGRAPHY.pSemiBold}>
                    {t('wireless_subnet_mask')}
                  </StyledText>
                  <StyledText as="p" color={COLORS.darkGrey}>
                    {wifi?.subnetMask}
                  </StyledText>
                </Flex>

                <Flex
                  flexDirection={DIRECTION_COLUMN}
                  gridGap={SPACING.spacing2}
                >
                  <StyledText css={TYPOGRAPHY.pSemiBold}>
                    {t('wireless_mac_address')}
                  </StyledText>
                  <StyledText as="p" color={COLORS.darkGrey}>
                    {wifi?.macAddress}
                  </StyledText>
                </Flex>
              </Flex>
            </>
          ) : (
            <Flex flexDirection={DIRECTION_COLUMN}>
              <SelectNetwork robotName={robotName} isRobotBusy={isRobotBusy} />
            </Flex>
          )}
        </Box>
        <Divider />
        <Flex alignItems={ALIGN_CENTER}>
          {ethernet?.ipAddress != null ? (
            <Icon
              size="1.25rem"
              name="ot-check"
              color={COLORS.successEnabled}
              marginRight={SPACING.spacing3}
              data-testid="RobotSettings_Networking_check_circle"
            />
          ) : (
            <Box height={SPACING.spacing4} width="1.75rem"></Box>
          )}
          <Icon
            size="1.25rem"
            name={isOT3 ? 'ethernet' : 'usb'}
            marginRight="0.75rem"
            data-testid="RobotSettings_Networking_usb_icon"
          />
          <StyledText as="h3" fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
            {isOT3 ? t('ethernet') : t('wired_usb')}
          </StyledText>
        </Flex>
        <Box paddingLeft="3.75rem">
          <Flex gridGap={SPACING.spacing4}>
            {ethernet?.ipAddress != null ? (
              <>
                <Flex
                  flexDirection={DIRECTION_COLUMN}
                  gridGap={SPACING.spacing2}
                >
                  <StyledText css={TYPOGRAPHY.pSemiBold}>
                    {t('wired_ip')}
                  </StyledText>
                  <StyledText as="p" color={COLORS.darkGrey}>
                    {ethernet?.ipAddress}
                  </StyledText>
                </Flex>
                <Flex
                  flexDirection={DIRECTION_COLUMN}
                  gridGap={SPACING.spacing2}
                >
                  <StyledText css={TYPOGRAPHY.pSemiBold}>
                    {t('wired_subnet_mask')}
                  </StyledText>
                  <StyledText as="p" color={COLORS.darkGrey}>
                    {ethernet?.subnetMask}
                  </StyledText>
                </Flex>
                <Flex
                  flexDirection={DIRECTION_COLUMN}
                  gridGap={SPACING.spacing2}
                >
                  <StyledText css={TYPOGRAPHY.pSemiBold}>
                    {t('wired_mac_address')}
                  </StyledText>
                  <StyledText as="p" color={COLORS.darkGrey}>
                    {ethernet?.macAddress}
                  </StyledText>
                </Flex>
              </>
            ) : (
              <StyledText as="p" color={COLORS.darkGrey}>
                {isOT3
                  ? t('not_connected_via_ethernet')
                  : t('not_connected_via_wired_usb')}
              </StyledText>
            )}
          </Flex>
          {isOT3 ? null : (
            <Flex flexDirection={DIRECTION_COLUMN} marginTop={SPACING.spacing4}>
              <ExternalLink href={HELP_CENTER_URL} id="WiredUSB_description">
                {t('wired_usb_description')}
              </ExternalLink>
              <StyledText
                as="p"
                marginTop={SPACING.spacing4}
                marginBottom={SPACING.spacing3}
              >
                {t('usb_to_ethernet_description')}
              </StyledText>
              <Link to="/app-settings/advanced" css={TYPOGRAPHY.linkPSemiBold}>
                {t('go_to_advanced_settings')}
              </Link>
            </Flex>
          )}
        </Box>
        {isOT3 ? (
          <>
            <Divider />
            <Flex alignItems={ALIGN_CENTER}>
              {isOT3ConnectedViaUSB ? (
                <Icon
                  size="1.25rem"
                  name="ot-check"
                  color={COLORS.successEnabled}
                  marginRight={SPACING.spacing3}
                  data-testid="RobotSettings_Networking_check_circle"
                />
              ) : (
                <Box height={SPACING.spacing4} width="1.75rem"></Box>
              )}
              <Icon
                size="1.25rem"
                name="usb"
                marginRight="0.75rem"
                data-testid="RobotSettings_Networking_wifi_icon"
              />
              <StyledText as="h3" fontWeight={TYPOGRAPHY.fontWeightSemiBold}>
                {t('usb')}
              </StyledText>
            </Flex>
            <Box paddingLeft="3.75rem">
              <StyledText as="p" color={COLORS.darkGrey}>
                {isOT3ConnectedViaUSB
                  ? t('directly_connected_to_this_computer')
                  : t('not_connected_via_usb')}
              </StyledText>
            </Box>
          </>
        ) : null}
      </Flex>
    </>
  )
}
