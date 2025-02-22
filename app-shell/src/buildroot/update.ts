// start a buildroot migration by POSTing the necessary wheel files to a robot
// and restarting

import path from 'path'

import { fetch, postFile } from '../http'
import type { RobotHost } from '@opentrons/app/src/redux/robot-api/types'
import type {
  RobotModel,
  ViewableRobot,
} from '@opentrons/app/src/redux/discovery/types'

const PREMIGRATION_WHL_DIR = path.join(
  // NOTE: __dirname refers to output directory
  __dirname,
  '../build/br-premigration-wheels'
)

const PREMIGRATION_API_WHL = path.join(
  PREMIGRATION_WHL_DIR,
  'opentrons-3.10.3-py2.py3-none-any.whl'
)
const PREMIGRATION_SERVER_WHL = path.join(
  PREMIGRATION_WHL_DIR,
  'otupdate-3.10.3-py2.py3-none-any.whl'
)

const OT2_FILENAME = 'ot2-system.zip'
const SYSTEM_FILENAME = 'system-update.zip'

const getSystemFileName = (robotModel: RobotModel): string => {
  if (robotModel === 'OT-2 Standard') {
    return OT2_FILENAME
  }
  return SYSTEM_FILENAME
}

export function startPremigration(robot: RobotHost): Promise<unknown> {
  const apiUrl = `http://${robot.ip}:${robot.port}/server/update`
  const serverUrl = `http://${robot.ip}:${robot.port}/server/update/bootstrap`
  const restartUrl = `http://${robot.ip}:${robot.port}/server/restart`

  return postFile(apiUrl, 'whl', PREMIGRATION_API_WHL)
    .then(() => postFile(serverUrl, 'whl', PREMIGRATION_SERVER_WHL))
    .then(() => fetch(restartUrl, { method: 'POST' }))
}

export function uploadSystemFile(
  robot: ViewableRobot,
  urlPath: string,
  file: string
): Promise<unknown> {
  const url = `http://${robot.ip}:${robot.port}${urlPath}`

  return postFile(url, getSystemFileName(robot.robotModel), file)
}
