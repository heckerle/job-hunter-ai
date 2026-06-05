'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

export default function Home() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedStates, setSelectedStates] = useState([])
  const [minSalary, setMinSalary] = useState('')

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs`)
      .then(res => res.json())
      .then(data => {
        setJobs(data)
        setLoading(false)
      })
  }, [])

  const stateOptions = [...new Set(jobs.map(j => j.state).filter(Boolean))].sort()

  const filtered = jobs.filter(j => {
    if (selectedStates.length > 0 && !selectedStates.includes(j.state)) return false
    if (minSalary && j.salary_min && j.salary_min < Number(minSalary)) return false
    return true
  })

  function toggleState(state) {
    setSelectedStates(prev =>
      prev.includes(state) ? prev.filter(s => s !== state) : [...prev, state]
    )
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">Job Hunter AI</h1>
            <p className="text-gray-400 mt-1">Your AI-powered job search pipeline</p>
          </div>
          <Link href="/matches"
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium transition">
            View My Matches →
          </Link>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Total Jobs</p>
            <p className="text-3xl font-bold text-white mt-1">{jobs.length}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Sources</p>
            <p className="text-3xl font-bold text-white mt-1">1</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-gray-400 text-sm">Last Updated</p>
            <p className="text-lg font-bold text-white mt-1">Today</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          {stateOptions.length > 0 && (
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs text-gray-500 uppercase">State</span>
              {stateOptions.map(state => (
                <button
                  key={state}
                  onClick={() => toggleState(state)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                    selectedStates.includes(state)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  {state}
                </button>
              ))}
              {selectedStates.length > 0 && (
                <button onClick={() => setSelectedStates([])} className="text-xs text-gray-500 hover:text-white ml-1">
                  clear
                </button>
              )}
            </div>
          )}

          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 uppercase">Min Salary</span>
            <input
              type="number"
              value={minSalary}
              onChange={e => setMinSalary(e.target.value)}
              placeholder="e.g. 80000"
              className="bg-gray-800 text-white text-sm px-3 py-1 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500 w-36"
            />
            {minSalary && (
              <button onClick={() => setMinSalary('')} className="text-xs text-gray-500 hover:text-white">
                clear
              </button>
            )}
          </div>
        </div>

        <h2 className="text-xl font-semibold text-white mb-4">
          Active Jobs {!loading && <span className="text-gray-500 font-normal text-base">({filtered.length})</span>}
        </h2>

        {loading ? (
          <p className="text-gray-400">Loading jobs...</p>
        ) : (
          <div className="grid gap-4">
            {filtered.map(job => (
              <div key={job.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-lg font-semibold text-white">{job.title}</h2>
                    <p className="text-blue-400">{job.company}</p>
                    <p className="text-gray-400 text-sm mt-1">{job.location}</p>
                  </div>
                  {job.salary_min && (
                    <p className="text-green-400 font-medium">
                      ${job.salary_min.toLocaleString()} — ${job.salary_max.toLocaleString()}
                    </p>
                  )}
                </div>
                <div className="mt-4 flex gap-2">
                  <a href={job.url} target="_blank"
                    className="text-xs bg-blue-900 text-blue-300 px-3 py-1 rounded-full hover:bg-blue-800">
                    View posting →
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
