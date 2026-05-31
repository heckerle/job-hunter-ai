'use client'

import { useEffect, useState } from 'react'

export default function Home() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/jobs')
      .then(res => res.json())
      .then(data => {
        setJobs(data)
        setLoading(false)
      })
  }, [])

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold text-blue-400 mb-2">Job Hunter AI</h1>
      <p className="text-gray-400 mb-8">Your AI-powered job search pipeline</p>

      {loading ? (
        <p className="text-gray-400">Loading jobs...</p>
      ) : (
        <div className="grid gap-4">
          {jobs.map(job => (
            <div key={job.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-semibold text-white">{job.title}</h2>
                  <p className="text-blue-400">{job.company}</p>
                  <p className="text-gray-400 text-sm mt-1">{job.location}</p>
                </div>
                {job.salary_min && (
                  <div className="text-right">
                    <p className="text-green-400 font-medium">
                      ${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
              <div className="mt-4 flex gap-2">
                <span className="text-xs bg-gray-800 text-gray-300 px-3 py-1 rounded-full">
                  {job.status}
                </span>
                <a href={job.url} target="_blank" className="text-xs bg-blue-900 text-blue-300 px-3 py-1 rounded-full hover:bg-blue-800">
                  View posting →
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
