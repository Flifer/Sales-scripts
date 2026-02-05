import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const API_URL = 'https://6984b3a9885008c00db21573.mockapi.io/script'
const LOCAL_STORAGE_KEY = 'sales-script-draft-v1'
const AUTH_STORAGE_KEY = 'sales-script-role'
const PAGE_SIZE = 100

const OPERATOR_PASSWORD = '123'
const ADMIN_PASSWORD = '456'

const makeId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

const createEmptyResponse = () => ({
  id: makeId(),
  text: '',
  nextId: null,
})

const fallbackSeed = []

const isStepCandidate = (item) =>
  item && typeof item === 'object' && ('operator' in item || 'responses' in item)

const extractStepsArray = (data) => {
  if (Array.isArray(data)) {
    return data.filter(isStepCandidate)
  }
  if (!data || typeof data !== 'object') return []
  if (Array.isArray(data.steps)) return data.steps.filter(isStepCandidate)
  if (Array.isArray(data.script)) return data.script.filter(isStepCandidate)
  if (Array.isArray(data.items)) return data.items.filter(isStepCandidate)
  if (Array.isArray(data.data)) return data.data.filter(isStepCandidate)
  if (isStepCandidate(data)) return [data]
  const values = Object.values(data).filter(isStepCandidate)
  return values
}

const extractRemoteIds = (data) => {
  const steps = extractStepsArray(data)
  return steps.map((item) => item?.id).filter(Boolean)
}

const countItems = (data) => {
  if (Array.isArray(data)) return data.length
  if (!data || typeof data !== 'object') return 0
  const steps = extractStepsArray(data)
  return steps.length
}

const fetchAllRemoteIds = async () => {
  const ids = new Set()
  let page = 1

  while (true) {
    const response = await fetch(`${API_URL}?page=${page}&limit=${PAGE_SIZE}`)
    if (!response.ok) {
      throw new Error(`LOAD ${response.status}`)
    }
    const data = await response.json()
    extractRemoteIds(data).forEach((id) => ids.add(id))

    if (!Array.isArray(data)) {
      break
    }

    const itemsCount = countItems(data)
    if (itemsCount < PAGE_SIZE) {
      break
    }

    page += 1
  }

  return Array.from(ids)
}

const fetchAllSteps = async () => {
  const items = []
  let page = 1

  while (true) {
    const response = await fetch(`${API_URL}?page=${page}&limit=${PAGE_SIZE}`)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const data = await response.json()
    const pageItems = extractStepsArray(data)
    if (pageItems.length > 0) {
      items.push(...pageItems)
    }

    if (!Array.isArray(data)) {
      break
    }

    const itemsCount = countItems(data)
    if (itemsCount < PAGE_SIZE) {
      break
    }

    page += 1
  }

  return items
}

const normalizeSeedData = (data) => {
  const extracted = extractStepsArray(data)
  return extracted.length > 0 ? extracted : fallbackSeed
}

const normalizeLocalSteps = (data) => {
  if (!Array.isArray(data)) return null

  const normalized = data.map((step) => {
    const responses = Array.isArray(step?.responses) ? step.responses : []
    const preparedResponses = responses.map((response) => ({
      id: response?.id ?? makeId(),
      text: response?.text ?? '',
      nextId: response?.nextId ?? null,
    }))

    return {
      id: step?.id ?? makeId(),
      operator: step?.operator ?? '',
      responses: preparedResponses.length > 0 ? preparedResponses : [createEmptyResponse()],
    }
  })

  return normalized
}

const readLocalSteps = () => {
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    const stepsRaw = Array.isArray(parsed?.steps) ? parsed.steps : parsed
    const steps = normalizeLocalSteps(stepsRaw)
    if (!steps) return null
    return {
      steps,
      savedPayload: typeof parsed?.savedPayload === 'string' ? parsed.savedPayload : '',
    }
  } catch {
    return null
  }
}

const writeLocalSteps = (steps, savedPayload) => {
  try {
    localStorage.setItem(
      LOCAL_STORAGE_KEY,
      JSON.stringify({
        steps,
        savedPayload: savedPayload ?? '',
        updatedAt: new Date().toISOString(),
      }),
    )
  } catch {
    // ignore localStorage write errors
  }
}

const createStepsFromSeed = (seedData) => {
  const ids = seedData.map(() => makeId())
  return seedData.map((step, index) => ({
    id: ids[index],
    operator: step.operator ?? '',
    responses: (step.responses ?? []).map((response) => ({
      id: makeId(),
      text: response.text ?? '',
      nextId:
        response.nextIndex === null || response.nextIndex === undefined
          ? null
          : ids[response.nextIndex] ?? null,
    })),
  }))
}

const buildPayload = (steps) => {
  const indexById = new Map()
  steps.forEach((step, index) => indexById.set(step.id, index))

  return steps.map((step) => ({
    operator: step.operator ?? '',
    responses: step.responses.map((response) => ({
      text: response.text ?? '',
      nextIndex: response.nextId ? (indexById.get(response.nextId) ?? null) : null,
    })),
  }))
}

const initialSteps = createStepsFromSeed(fallbackSeed)

function App() {
  const [role, setRole] = useState(() => localStorage.getItem(AUTH_STORAGE_KEY))
  const [passwordInput, setPasswordInput] = useState('')
  const [authError, setAuthError] = useState('')
  const [steps, setSteps] = useState(initialSteps)
  const [activeTab, setActiveTab] = useState('script')
  const [currentStepId, setCurrentStepId] = useState(initialSteps[0]?.id ?? null)
  const [history, setHistory] = useState([])
  const [syncStatus, setSyncStatus] = useState({
    state: 'idle',
    message: 'Локальные данные',
  })
  const [hasChanges, setHasChanges] = useState(false)

  const isHydratedRef = useRef(false)
  const savingRef = useRef(false)
  const lastSavedRef = useRef('')

  useEffect(() => {
    if (role === 'operator' && activeTab === 'settings') {
      setActiveTab('script')
    }
  }, [role, activeTab])

  useEffect(() => {
    let isActive = true
    const localDraft = readLocalSteps()
    const localSteps = localDraft?.steps ?? null
    const localSavedPayload = localDraft?.savedPayload ?? ''
    const localPayload = localSteps ? JSON.stringify(buildPayload(localSteps)) : ''

    const applySteps = (loadedSteps, { dirty, status, savedPayload }) => {
      if (!isActive) return
      if (typeof savedPayload === 'string') {
        lastSavedRef.current = savedPayload
      }
      setSteps(loadedSteps)
      setCurrentStepId(loadedSteps[0]?.id ?? null)
      setHistory([])
      setHasChanges(dirty)
      setSyncStatus(status)
    }

    const loadScript = async () => {
      setSyncStatus({ state: 'loading', message: 'Загрузка сценария...' })
      try {
        const data = await fetchAllSteps()
        const normalized = normalizeSeedData(data)
        const loadedSteps = createStepsFromSeed(normalized)
        const apiPayload = JSON.stringify(buildPayload(loadedSteps))
        const hasApiSteps = loadedSteps.length > 0

        const localDirty = localSavedPayload ? localPayload !== localSavedPayload : false

        if (!hasApiSteps) {
          if (localSteps && localDirty) {
            applySteps(localSteps, {
              dirty: true,
              status: { state: 'dirty', message: 'Есть несохраненные изменения (локально)' },
              savedPayload: localSavedPayload,
            })
            return
          }

          applySteps(loadedSteps, {
            dirty: false,
            status: { state: 'idle', message: 'Сценарий пуст (данные из API)' },
            savedPayload: apiPayload,
          })
          return
        }

        if (localSteps && localDirty) {
          applySteps(localSteps, {
            dirty: true,
            status: { state: 'dirty', message: 'Есть несохраненные изменения (локально)' },
            savedPayload: localSavedPayload,
          })
          return
        }

        applySteps(loadedSteps, {
          dirty: false,
          status: { state: 'idle', message: 'Сценарий загружен' },
          savedPayload: apiPayload,
        })
      } catch (error) {
        if (localSteps) {
          const dirty = localSavedPayload ? localPayload !== localSavedPayload : true
          applySteps(localSteps, {
            dirty,
            status: {
              state: 'error',
              message: 'API недоступно. Используется локальный черновик.',
            },
            savedPayload: localSavedPayload,
          })
        } else {
          const fallbackPayload = JSON.stringify(buildPayload(initialSteps))
          applySteps(initialSteps, {
            dirty: false,
            status: {
              state: 'error',
              message: 'Не удалось загрузить. Используются локальные данные.',
            },
            savedPayload: fallbackPayload,
          })
        }
      } finally {
        if (isActive) {
          isHydratedRef.current = true
        }
      }
    }

    loadScript()

    return () => {
      isActive = false
    }
  }, [])

  useEffect(() => {
    if (!isHydratedRef.current) return
    const payloadString = JSON.stringify(buildPayload(steps))
    const dirty = payloadString !== lastSavedRef.current
    setHasChanges(dirty)
    if (dirty) {
      setSyncStatus((prev) => {
        if (prev.state === 'saving' || prev.state === 'loading') return prev
        if (prev.state === 'dirty') return prev
        return { state: 'dirty', message: 'Есть несохраненные изменения' }
      })
    }
  }, [steps])

  useEffect(() => {
    if (!isHydratedRef.current) return
    writeLocalSteps(steps, lastSavedRef.current)
  }, [steps])

  useEffect(() => {
    if (currentStepId && !steps.some((step) => step.id === currentStepId)) {
      setCurrentStepId(steps[0]?.id ?? null)
      setHistory([])
    }
  }, [steps, currentStepId])

  useEffect(() => {
    setHistory((prev) => {
      const filtered = prev.filter((entry) => steps.some((step) => step.id === entry.stepId))
      return filtered.length === prev.length ? prev : filtered
    })
  }, [steps])

  const stepsById = useMemo(() => {
    const map = new Map()
    steps.forEach((step) => map.set(step.id, step))
    return map
  }, [steps])

  const currentStep = currentStepId ? stepsById.get(currentStepId) : null
  const isFinished = currentStepId === null

  const getStepLabel = (id) => {
    if (!id) return 'Завершение'
    const index = steps.findIndex((step) => step.id === id)
    if (index === -1) return 'Не найдено'
    return `Шаг ${index + 1}`
  }

  const saveScript = async (stepsToSave) => {
    if (savingRef.current) return

    const payload = buildPayload(stepsToSave)
    const payloadString = JSON.stringify(payload)
    if (payloadString === lastSavedRef.current) return

    savingRef.current = true
    setSyncStatus({ state: 'saving', message: 'Сохранение...' })

    try {
      const existingIds = await fetchAllRemoteIds()

      for (const id of existingIds) {
        const response = await fetch(`${API_URL}/${id}`, { method: 'DELETE' })
        if (!response.ok) {
          throw new Error(`DELETE ${id} failed`)
        }
      }

      for (const stepPayload of payload) {
        const response = await fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(stepPayload),
        })
        if (!response.ok) {
          throw new Error('POST failed')
        }
      }

      lastSavedRef.current = payloadString
      writeLocalSteps(stepsToSave, payloadString)
      setHasChanges(false)
      setSyncStatus({ state: 'saved', message: 'Сохранено' })
    } catch (error) {
      setSyncStatus({ state: 'error', message: 'Ошибка синхронизации' })
    } finally {
      savingRef.current = false
    }
  }

  const handleStepText = (stepId, value) => {
    setSteps((prev) =>
      prev.map((step) => (step.id === stepId ? { ...step, operator: value } : step)),
    )
  }

  const handleResponseText = (stepId, responseId, value) => {
    setSteps((prev) =>
      prev.map((step) => {
        if (step.id !== stepId) return step
        return {
          ...step,
          responses: step.responses.map((response) =>
            response.id === responseId ? { ...response, text: value } : response,
          ),
        }
      }),
    )
  }

  const handleResponseNext = (stepId, responseId, value) => {
    setSteps((prev) =>
      prev.map((step) => {
        if (step.id !== stepId) return step
        return {
          ...step,
          responses: step.responses.map((response) =>
            response.id === responseId
              ? { ...response, nextId: value === '' ? null : value }
              : response,
          ),
        }
      }),
    )
  }

  const addStep = () => {
    const newStepId = makeId()
    setSteps((prev) => [
      ...prev,
      {
        id: newStepId,
        operator: '',
        responses: [createEmptyResponse()],
      },
    ])
    if (!currentStepId) {
      setCurrentStepId(newStepId)
    }
  }

  const removeStep = (stepId) => {
    setSteps((prev) => {
      const filtered = prev.filter((step) => step.id !== stepId)
      return filtered.map((step) => ({
        ...step,
        responses: step.responses.map((response) =>
          response.nextId === stepId ? { ...response, nextId: null } : response,
        ),
      }))
    })
  }

  const addResponse = (stepId) => {
    setSteps((prev) =>
      prev.map((step) =>
        step.id === stepId
          ? { ...step, responses: [...step.responses, createEmptyResponse()] }
          : step,
      ),
    )
  }

  const removeResponse = (stepId, responseId) => {
    setSteps((prev) =>
      prev.map((step) => {
        if (step.id !== stepId) return step
        const filtered = step.responses.filter((response) => response.id !== responseId)
        return {
          ...step,
          responses: filtered.length > 0 ? filtered : [createEmptyResponse()],
        }
      }),
    )
  }

  const handleResponseSelect = (response) => {
    if (!currentStep) return
    setHistory((prev) => [...prev, { stepId: currentStep.id, responseId: response.id }])
    setCurrentStepId(response.nextId ?? null)
  }

  const handleBack = () => {
    setHistory((prev) => {
      if (prev.length === 0) return prev
      const last = prev[prev.length - 1]
      const updated = prev.slice(0, -1)
      setCurrentStepId(last.stepId)
      return updated
    })
  }

  const resetScript = () => {
    setHistory([])
    setCurrentStepId(steps[0]?.id ?? null)
  }

  const currentStepIndex = currentStep ? steps.findIndex((step) => step.id === currentStep.id) : -1

  const handleLogin = (event) => {
    event.preventDefault()
    setAuthError('')
    const trimmed = passwordInput.trim()
    if (trimmed === ADMIN_PASSWORD) {
      localStorage.setItem(AUTH_STORAGE_KEY, 'admin')
      setRole('admin')
      setPasswordInput('')
      return
    }
    if (trimmed === OPERATOR_PASSWORD) {
      localStorage.setItem(AUTH_STORAGE_KEY, 'operator')
      setRole('operator')
      setPasswordInput('')
      return
    }
    setAuthError('Неверный пароль')
  }

  const handleLogout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    setRole(null)
    setPasswordInput('')
    setAuthError('')
    setActiveTab('script')
  }

  if (!role) {
    return (
      <div className="app auth">
        <div className="auth-card">
          <p className="eyebrow">Защищенный доступ</p>
          <h1 className="app-title">Вход в сценарий</h1>
          <p className="app-subtitle">
            Введите пароль оператора или администратора, чтобы открыть приложение.
          </p>
          <form className="auth-form" onSubmit={handleLogin}>
            <label className="field">
              <span>Пароль</span>
              <input
                type="password"
                placeholder="Введите пароль"
                value={passwordInput}
                onChange={(event) => setPasswordInput(event.target.value)}
              />
            </label>
            {authError ? <p className="auth-error">{authError}</p> : null}
            <button className="btn btn-primary" type="submit">
              Войти
            </button>
          </form>
          <div className="auth-hint">
            <p>Роль определяется по введенному паролю.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-main">
          <p className="eyebrow">Сценарий звонка</p>
          <h1 className="app-title">Конструктор скриптов для отдела продаж</h1>
          <p className="app-subtitle">
            Соберите диалог по шагам и используйте его во время звонка. Оператор выбирает ответ
            клиента и сразу видит следующую реплику.
          </p>
        </div>
        <div className="top-controls">
          <div className="top-meta">
            <div className="role-pill">
              Роль: {role === 'admin' ? 'Администратор' : 'Оператор'}
            </div>
          </div>
          <button className="btn btn-outline" onClick={handleLogout}>
            Выйти
          </button>
          <div className={`sync-status ${syncStatus.state}`}>Стутус: {syncStatus.message}</div>
        </div>
      </header>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'script' ? 'active' : ''}`}
          onClick={() => setActiveTab('script')}
        >
          Скрипт
        </button>
        <button
          className={`tab ${activeTab === 'settings' ? 'active' : ''} ${
            role !== 'admin' ? 'disabled' : ''
          }`}
          onClick={() => role === 'admin' && setActiveTab('settings')}
        >
          Настройки
        </button>
      </div>

      {activeTab === 'settings' ? (
        <main className="main settings">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Настройка шагов</h2>
                <p className="panel-subtitle">
                  Укажите реплику оператора и варианты ответов клиента.
                </p>
              </div>
              <div className="panel-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => void saveScript(steps)}
                  disabled={!hasChanges || syncStatus.state === 'saving' || syncStatus.state === 'loading'}
                >
                  Сохранить изменения
                </button>
                <button className="btn btn-outline" onClick={addStep}>
                  Добавить шаг
                </button>
              </div>
            </div>

            {steps.length === 0 ? (
              <div className="empty-state">
                <p>Сценарий пуст. Создайте первый шаг, чтобы начать работу.</p>
                <button className="btn btn-primary" onClick={addStep}>
                  Создать шаг
                </button>
              </div>
            ) : (
              <div className="steps-list">
                {steps.map((step, index) => (
                  <div
                    className="step-card"
                    key={step.id}
                    style={{ animationDelay: `${index * 0.05}s` }}
                  >
                    <div className="step-header">
                      <div>
                        <p className="step-label">Шаг {index + 1}</p>
                        <p className="step-caption">ID: {step.id.slice(0, 6)}</p>
                      </div>
                      <button
                        className="btn btn-ghost"
                        onClick={() => removeStep(step.id)}
                        disabled={steps.length === 1}
                      >
                        Удалить шаг
                      </button>
                    </div>

                    <label className="field">
                      <span>Реплика оператора</span>
                      <textarea
                        rows={3}
                        placeholder="Введите текст, который говорит оператор"
                        value={step.operator}
                        onChange={(event) => handleStepText(step.id, event.target.value)}
                      />
                    </label>

                    <div className="responses">
                      <div className="responses-header">
                        <p>Ответы клиента</p>
                        <button className="btn btn-ghost" onClick={() => addResponse(step.id)}>
                          + Ответ
                        </button>
                      </div>
                      <div className="responses-list">
                        {step.responses.map((response, responseIndex) => (
                          <div
                            className="response-row"
                            key={response.id}
                            style={{ animationDelay: `${responseIndex * 0.04}s` }}
                          >
                            <input
                              type="text"
                              placeholder="Текст ответа клиента"
                              value={response.text}
                              onChange={(event) =>
                                handleResponseText(step.id, response.id, event.target.value)
                              }
                            />
                            <select
                              value={response.nextId ?? ''}
                              onChange={(event) =>
                                handleResponseNext(step.id, response.id, event.target.value)
                              }
                            >
                              <option value="">Завершить разговор</option>
                              {steps.map((option, optionIndex) => (
                                <option key={option.id} value={option.id}>
                                  Шаг {optionIndex + 1}
                                </option>
                              ))}
                            </select>
                            <button
                              className="btn btn-icon"
                              onClick={() => removeResponse(step.id, response.id)}
                              aria-label="Удалить ответ"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <aside className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Логика сценария</h2>
                <p className="panel-subtitle">Быстрый просмотр переходов между шагами.</p>
              </div>
            </div>
            <div className="preview">
              {steps.map((step, index) => (
                <div className="preview-step" key={step.id}>
                  <div className="preview-title">
                    <span>Шаг {index + 1}</span>
                    <span className="preview-pill">{step.responses.length} ответов</span>
                  </div>
                  <p className="preview-text">{step.operator || 'Реплика пока не указана'}</p>
                  <div className="preview-responses">
                    {step.responses.map((response) => (
                      <div className="preview-response" key={response.id}>
                        <span>{response.text || 'Ответ не указан'}</span>
                        <span className="preview-next">{getStepLabel(response.nextId)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </aside>
        </main>
      ) : (
        <main className="main script">
          <section className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Рабочий экран</h2>
                <p className="panel-subtitle">
                  Нажмите на ответ клиента — система покажет следующую реплику.
                </p>
              </div>
              <div className="panel-actions">
                <button className="btn btn-outline" onClick={resetScript}>
                  Начать сначала
                </button>
                <button className="btn btn-ghost" onClick={handleBack} disabled={history.length === 0}>
                  Назад
                </button>
              </div>
            </div>

            {!steps.length ? (
              <div className="empty-state">
                <p>Сценарий пуст. Добавьте шаги во вкладке «Настройки».</p>
                <button className="btn btn-primary" onClick={() => setActiveTab('settings')}>
                  Открыть настройки
                </button>
              </div>
            ) : isFinished ? (
              <div className="end-state">
                <p className="eyebrow">Сценарий завершен</p>
                <h3>Разговор окончен</h3>
                <p>Можно начать следующий звонок или вернуться в настройки.</p>
                <button className="btn btn-primary" onClick={resetScript}>
                  Новый звонок
                </button>
              </div>
            ) : (
              <div className="script-stage">
                <div className="script-card">
                  <p className="eyebrow">Текущая реплика</p>
                  <h3>{currentStep?.operator || 'Реплика не указана'}</h3>
                  <p className="script-meta">
                    {currentStepIndex >= 0 ? `Шаг ${currentStepIndex + 1}` : 'Сценарий'} ·{' '}
                    {currentStep?.responses.length ?? 0} вариантов ответа
                  </p>
                </div>

                <div className="response-grid">
                  {currentStep?.responses.map((response, index) => (
                    <button
                      key={response.id}
                      className="response-btn"
                      style={{ animationDelay: `${index * 0.04}s` }}
                      onClick={() => handleResponseSelect(response)}
                    >
                      <span className="response-text">{response.text || 'Ответ не указан'}</span>
                      <span className="response-next">{getStepLabel(response.nextId)}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </section>

          <aside className="panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">История звонка</h2>
                <p className="panel-subtitle">Выбранные ответы клиента по ходу разговора.</p>
              </div>
              <span className="badge">{history.length}</span>
            </div>
            {history.length === 0 ? (
              <div className="empty-mini">Пока нет выбранных ответов.</div>
            ) : (
              <div className="history">
                {history.map((entry, index) => {
                  const step = stepsById.get(entry.stepId)
                  const response = step?.responses.find((item) => item.id === entry.responseId)
                  return (
                    <div className="history-item" key={`${entry.stepId}-${entry.responseId}-${index}`}>
                      <div>
                        <p className="history-step">{getStepLabel(entry.stepId)}</p>
                        <p className="history-operator">{step?.operator || 'Реплика не указана'}</p>
                      </div>
                      <p className="history-response">{response?.text || 'Ответ не указан'}</p>
                    </div>
                  )
                })}
              </div>
            )}
          </aside>
        </main>
      )}
    </div>
  )
}

export default App
