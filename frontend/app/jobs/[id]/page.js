'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import ReactMarkdown from 'react-markdown'

const recommendationColors = {
  strong_match: 'bg-green-900 text-green-300',
  good_match: 'bg-blue-900 text-blue-300',
  weak_match: 'bg-yellow-900 text-yellow-300',
  poor_match: 'bg-red-900 text-red-300'
}

export default function JobDetail() {
  const { id } = useParams()
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`http://localhost:8000/jobs/${id}`)
      .then(res => res.json())
      .then(data => {
        setJob(data)
        setLoading(false)
      })
  }, [id])

  if (loading) return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <p className="text-gray-400">Loading job details...</p>
    </main>
  )

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <Link href="/matches" className="text-gray-400 text-sm hover:text-white mb-6 block">
          ← Back to matches
        </Link>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">{job.title}</h1>
              <p className="text-blue-400 text-lg font-medium">{job.company}</p>
              <p className="text-gray-400 mt-1">{job.location}</p>
            </div>
            {job.salary_min && (
              <p className="text-green-400 font-medium">
                ${job.salary_min.toLocaleString()} — ${job.salary_max.toLocaleString()}
              </p>
            )}
          </div>

          <a href={job.url} target="_blank"
            className="inline-block bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg transition text-sm">
            View Job Posting →
          </a>
        </div>

        {job.briefing && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 mb-6">
            <h2 className="text-lg font-semibold text-white mb-4">Company Intelligence</h2>
            <div className="text-gray-300 leading-relaxed text-sm prose prose-invert max-w-none">
                <ReactMarkdown>{job.briefing}</ReactMarkdown>
            </div>
          </div>
        )}

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8">
          <h2 className="text-lg font-semibold text-white mb-2">Full Job Description</h2>
          <p className="text-gray-400 text-sm leading-relaxed">{job.description}</p>
        </div>
      </div>
    </main>
  )
}
