import * as signalR from '@microsoft/signalr'
import { HUB_BASE_URL } from '@/config/runtime.js'
import { getToken } from '@/services/authSession.js'

const eventSubscribers = new Map()
const eventDispatchers = new Map()
const stateSubscribers = new Set()

let connection = null
let startPromise = null
let stopPromise = null
let connectionState = 'disconnected'

function getAccessToken() {
  return getToken() || ''
}

function updateState(state, error = null) {
  connectionState = state
  stateSubscribers.forEach((handler) => handler(state, error))
}

function getConnection() {
  if (connection) return connection

  connection = new signalR.HubConnectionBuilder()
    .withUrl(`${HUB_BASE_URL}/hub/cabinet`, {
      accessTokenFactory: getAccessToken,
    })
    .withAutomaticReconnect([0, 2000, 5000, 10000])
    .build()

  connection.onreconnecting((error) => updateState('reconnecting', error))
  connection.onreconnected(() => updateState('connected'))
  connection.onclose((error) => updateState('disconnected', error))

  eventDispatchers.forEach((dispatcher, eventName) => {
    connection.on(eventName, dispatcher)
  })

  return connection
}

async function stopIfIdle() {
  await Promise.resolve()
  if (eventSubscribers.size > 0 || !connection) return
  if (startPromise) {
    try {
      await startPromise
    } catch {
      return
    }
  }
  if (eventSubscribers.size > 0) return
  if (connection.state !== signalR.HubConnectionState.Disconnected) {
    stopPromise = connection.stop().finally(() => {
      stopPromise = null
    })
    try {
      await stopPromise
    } catch (error) {
      updateState('disconnected', error)
      return
    }
  }
  updateState('disconnected')
}

export function subscribe(eventName, handler) {
  if (!eventSubscribers.has(eventName)) {
    const subscribers = new Set()
    const dispatcher = (data) => {
      subscribers.forEach((subscriber) => subscriber(data))
    }

    eventSubscribers.set(eventName, subscribers)
    eventDispatchers.set(eventName, dispatcher)
    if (connection) connection.on(eventName, dispatcher)
  }

  eventSubscribers.get(eventName).add(handler)

  return () => {
    const subscribers = eventSubscribers.get(eventName)
    if (!subscribers) return

    subscribers.delete(handler)
    if (subscribers.size === 0) {
      eventSubscribers.delete(eventName)
      const dispatcher = eventDispatchers.get(eventName)
      if (connection && dispatcher) connection.off(eventName, dispatcher)
      eventDispatchers.delete(eventName)
    }

    void stopIfIdle()
  }
}

export function onStateChanged(handler) {
  stateSubscribers.add(handler)
  handler(connectionState)
  return () => stateSubscribers.delete(handler)
}

export async function start() {
  if (stopPromise) await stopPromise
  const activeConnection = getConnection()
  if (startPromise) return startPromise
  if (activeConnection.state !== signalR.HubConnectionState.Disconnected) return

  updateState('connecting')
  startPromise = activeConnection.start()
    .then(() => updateState('connected'))
    .catch((error) => {
      updateState('disconnected', error)
      throw error
    })
    .finally(() => {
      startPromise = null
    })

  return startPromise
}

export async function stop() {
  if (!connection) return
  if (stopPromise) return stopPromise
  if (startPromise) {
    try {
      await startPromise
    } catch {
      return
    }
  }
  if (connection.state !== signalR.HubConnectionState.Disconnected) {
    stopPromise = connection.stop().finally(() => {
      stopPromise = null
    })
    await stopPromise
  }
  updateState('disconnected')
}

export function getState() {
  return connectionState
}

export const cabinetHub = {
  getState,
  onStateChanged,
  start,
  stop,
  subscribe,
}
