import * as React from 'react'
import Keyboard from 'react-simple-keyboard'

interface NumpadProps {
  onChange: (input: string) => void
  keyboardRef: React.MutableRefObject<null>
}

export function Numpad({ onChange, keyboardRef }: NumpadProps): JSX.Element {
  const keyboardNumpad = {
    layout: {
      default: ['7 8 9', '4 5 6', '1 2 3', '0 . {backspace}'],
    },
  }
  return (
    /*
     *  autoUseTouchEvents: for OT-3 on-device app
     *  useButtonTag: this is for testing purpose that each key renders as a button
     */
    <Keyboard
      keyboardRef={r => (keyboardRef.current = r)}
      onChange={onChange}
      layoutName="default"
      autoUseTouchEvents={true}
      useButtonTag={true}
      {...keyboardNumpad}
    />
  )
}
