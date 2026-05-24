/**
 * HOJ 算法系统 API 封装
 * 用于从 Open436 前端直接获取 HOJ 用户数据
 */
import axios from 'axios'

const hojApiBase = import.meta.env.VITE_HOJ_API_BASE || ''

export async function getHojUserStats(username) {
  if (!username) return null
  try {
    const token = localStorage.getItem('token')
    const headers = token ? { Authorization: token } : {}

    const [homeRes, heatRes] = await Promise.all([
      axios.get(`${hojApiBase}/api/get-user-home-info`, {
        params: { username },
        headers,
        timeout: 8000
      }).catch(() => ({ data: null })),
      axios.get(`${hojApiBase}/api/get-user-calendar-heatmap`, {
        params: { username },
        headers,
        timeout: 8000
      }).catch(() => ({ data: null }))
    ])

    let acCount = 0, submitCount = 0, rating = 0, streak = 0

    if (homeRes.data?.status === 200 && homeRes.data.data) {
      const d = homeRes.data.data
      acCount = d.solvedList?.length || 0
      submitCount = d.total || 0
      rating = d.rating || 0
    }

    if (heatRes.data?.status === 200 && heatRes.data.data?.dataList) {
      streak = calculateStreak(heatRes.data.data.dataList)
    }

    return { acCount, submitCount, rating, streak }
  } catch (e) {
    console.error('获取 HOJ 用户数据失败:', e)
    return null
  }
}

function calculateStreak(dataList) {
  if (!dataList || dataList.length === 0) return 0
  const dateMap = new Map()
  dataList.forEach(item => {
    if (item.date && item.count > 0) {
      dateMap.set(item.date, item.count)
    }
  })
  if (dateMap.size === 0) return 0

  const today = new Date()
  const fmt = (d) => d.toISOString().split('T')[0]

  let streak = 0
  let checkDate = new Date(today)

  // 如果今天没有提交，从昨天开始算
  if (!dateMap.has(fmt(checkDate))) {
    checkDate.setDate(checkDate.getDate() - 1)
  }

  while (dateMap.has(fmt(checkDate))) {
    streak++
    checkDate.setDate(checkDate.getDate() - 1)
  }

  return streak
}
