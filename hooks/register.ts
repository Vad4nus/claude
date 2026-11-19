import type { Register } from 'claude-code'

// Gives a session whose main model is weaker than Opus (Sonnet, Haiku) an Opus advisor.
// An Opus or Fable session gets none: the advisor must be at least as capable as the main model.
// A user-set advisorModel (settings or /advisor) always wins.
const ADVISOR = 'opus'
const AT_LEAST_ADVISOR = /opus|fable|mythos/i

let isReadingModel = false

export const register: Register = on => {
  on('settings.read', async ($, e, next) => {
    const result = await next(e)
    if (result.deny !== undefined || e.source !== undefined || isReadingModel) return result
    const settings = result.value
    if (settings.advisorModel !== undefined) return result
    // ponytail: the engine re-merges settings only when settings or plugins change, so a
    // /model switch after that keeps the advisor decision of the model at the last merge.
    isReadingModel = true
    try {
      const model = await $.session.model()
      return AT_LEAST_ADVISOR.test(model) ? result : { value: { ...settings, advisorModel: ADVISOR } }
    } finally {
      isReadingModel = false
    }
  }).catch(($, e, next) => next(e))
}
