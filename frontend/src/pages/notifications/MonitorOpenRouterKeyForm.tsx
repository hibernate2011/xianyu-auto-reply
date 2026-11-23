import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { clearMonitorOpenRouterKey, getMonitorOpenRouterKeyStatus, saveMonitorOpenRouterKey } from '@/api/notifications'
import { useUIStore } from '@/store/uiStore'
import { getApiErrorMessage } from '@/utils/request'

export function MonitorOpenRouterKeyForm() {
  const addToast = useUIStore((state) => state.addToast)
  const [apiKey, setApiKey] = useState('')
  const [configured, setConfigured] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    const load = async () => {
      try {
        const result = await getMonitorOpenRouterKeyStatus()
        if (active && result.success && result.data) setConfigured(result.data.configured)
      } catch {
        if (active) setConfigured(null)
      } finally {
        if (active) setLoading(false)
      }
    }
    void load()
    return () => { active = false }
  }, [])

  const updateKey = async (value: string | null) => {
    setSaving(true)
    try {
      const result = value === null
        ? await clearMonitorOpenRouterKey()
        : await saveMonitorOpenRouterKey(value)
      if (!result.success || !result.data) {
        addToast({ type: 'error', message: result.message || '更新 OpenRouter 密钥失败' })
        return
      }
      setConfigured(result.data.configured)
      setApiKey('')
      addToast({ type: 'success', message: value === null ? '个人 OpenRouter 密钥已移除' : 'OpenRouter 密钥已保存' })
    } catch (error) {
      addToast({ type: 'error', message: getApiErrorMessage(error, '更新 OpenRouter 密钥失败') })
    } finally {
      setSaving(false)
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const value = apiKey.trim()
    if (value && !loading && !saving) void updateKey(value)
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
      <label htmlFor="monitor-openrouter-key" className="input-label">商品监控 OpenRouter API Key</label>
      <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">
        个人密钥用于你名下所有开启 AI 商品购买推荐的监控任务。未设置个人密钥时，使用调度服务已配置的默认密钥。
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <input
          id="monitor-openrouter-key"
          className="input-ios w-full sm:max-w-sm"
          type="password"
          autoComplete="new-password"
          maxLength={512}
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder={configured ? '输入新密钥以替换' : '输入 OpenRouter API Key'}
          disabled={loading || saving}
        />
        <button type="submit" className="btn-ios-primary" disabled={loading || saving || !apiKey.trim()}>
          保存密钥
        </button>
        {configured && (
          <button type="button" className="btn-ios-secondary" onClick={() => void updateKey(null)} disabled={saving}>
            移除个人密钥
          </button>
        )}
        <span className="text-sm text-slate-500 dark:text-slate-400" role="status">
          {loading ? '读取中…' : configured === null ? '密钥状态暂不可用' : configured ? '已保存个人密钥' : '未设置个人密钥'}
        </span>
      </div>
    </form>
  )
}
