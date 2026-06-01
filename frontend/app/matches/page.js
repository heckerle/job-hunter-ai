'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

const recommendationColors = {
  strong_match: 'bg-green-900 text-green-300',
  good_match: 'bg-blue-900 text-blue-300',
  weak_match: 'bg-yellow-900 text-yellow-300',
  poor_match: 'bg-red-900 text-red-300'
}

let cachedMatches = null
let cachedScroll = 0

export default function Matches() {
  const [matches, setMatches] = useState(cachedMatches || [])
  const [loading, setLoading] = useState(!cachedMatches)
  const router = useRouter()

  useEffect(() => {
    if (cachedMatches) {
      window.scrollTo(0, cachedScroll)
      return
    }
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs`)
      .then(res => res.json())
      .then(data => {
        cachedMatches = data
        setMatches(data)
        setLoading(false)
      })
  }, [])

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <Link href="/" className="text-gray-400 text-sm hover:text-white mb-6 block">← Back</Link>
      <h1 className="text-3xl font-bold text-blue-400 mb-2">Top Matches</h1>
      <p className="text-gray-400 mb-8">AI-ranked jobs based on your resume</p>

      {loading ? (
        <div className="text-gray-400">
          <p>Analyzing your resume against all jobs...</p>
          <p className="text-sm mt-2">This takes about 30 seconds</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {matches.map((job, i) => (
            <div key={job.id} onClick={() => {
              cachedScroll = window.scrollY
              router.push(`/jobs/${job.id}`)
            }}
              className="bg-gray-900 border border-gray-800 rounded-xl p-6 cursor-pointer hover:border-gray-600 transition">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-gray-500 text-sm">#{i + 1}</span>
                    <h2 className="text-lg font-semibold text-white">{job.title}</h2>
                  </div>
                  <p className="text-blue-400 font-medium">{job.company}</p>
                  <p className="text-gray-400 text-sm mt-1">{job.location}</p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-white">{job.match_score}%</div>
                  <span className={`text-xs px-3 py-1 rounded-full mt-1 inline-block ${recommendationColors[job.recommendation]}`}>
                    {job.recommendation.replace('_', ' ')}
                  </span>
                </div>
              </div>

              {job.salary_min && (
                <p className="text-green-400 text-sm mb-4">
                  ${job.salary_min.toLocaleString()} — ${job.salary_max.toLocaleString()}
                </p>
              )}

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-xs text-gray-500 uppercase mb-2">Strengths</p>
                  <ul className="space-y-1">
                    {job.match_reasons.map((r, i) => (
                      <li key={i} className="text-sm text-gray-300 flex gap-2">
                        <span className="text-green-400 mt-0.5">✓</span>{r}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase mb-2">Gaps</p>
                  <ul className="space-y-1">
                    {job.gaps.map((g, i) => (
                      <li key={i} className="text-sm text-gray-300 flex gap-2">
                        <span className="text-red-400 mt-0.5">✗</span>{g}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <a href={job.url} target="_blank" onClick={e => e.stopPropagation()}
                className="inline-block text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition">
                View Job Posting →
              </a>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
