import * as React from 'react'
import { usePipettesQuery } from '@opentrons/react-api-client'
import { PrimaryButton } from '../../atoms/buttons'
import { SmallButton } from '../../atoms/buttons/ODD/SmallButton'

interface CheckPipetteButtonProps {
  proceedButtonText: string
  setPending: React.Dispatch<React.SetStateAction<boolean>>
  proceed: () => void
  isDisabled: boolean
  isOnDevice: boolean | null
}
export const CheckPipetteButton = (
  props: CheckPipetteButtonProps
): JSX.Element => {
  const {
    proceedButtonText,
    proceed,
    setPending,
    isDisabled,
    isOnDevice,
  } = props
  const { status, refetch } = usePipettesQuery()

  React.useEffect(() => {
    //  if requestStatus is error then the error modal will be in the results page
    if (status === 'success' || status === 'error') {
      proceed()
      setPending(false)
    } else if (status === 'loading') {
      setPending(true)
    }
  }, [proceed, status, setPending])

  return isOnDevice != null && isOnDevice ? (
    <SmallButton
      disabled={isDisabled}
      buttonText={proceedButtonText}
      buttonType="default"
      onClick={() => {
        refetch()
          .then(() => {})
          .catch(() => {})
      }}
    />
  ) : (
    <PrimaryButton
      disabled={isDisabled}
      onClick={() => {
        refetch()
          .then(() => {})
          .catch(() => {})
      }}
    >
      {proceedButtonText}
    </PrimaryButton>
  )
}
