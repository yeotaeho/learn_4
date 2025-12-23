'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface TrainingData {
  instruction: string
  input: string
  output: string
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showTraining, setShowTraining] = useState(false)
  const [trainingData, setTrainingData] = useState<TrainingData[]>([
    { instruction: '', input: '', output: '' }
  ])
  const [isTraining, setIsTraining] = useState(false)
  const [trainingStatus, setTrainingStatus] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.yeotaeho.kr'
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          history: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      })

      if (!response.ok) {
        throw new Error('API 요청 실패')
      }

      const data = await response.json()
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: '죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddTrainingData = () => {
    setTrainingData([...trainingData, { instruction: '', input: '', output: '' }])
  }

  const handleRemoveTrainingData = (index: number) => {
    if (trainingData.length > 1) {
      setTrainingData(trainingData.filter((_, i) => i !== index))
    }
  }

  const handleTrainingDataChange = (index: number, field: keyof TrainingData, value: string) => {
    const newData = [...trainingData]
    newData[index][field] = value
    setTrainingData(newData)
  }

  const handleStartTraining = async () => {
    // 빈 데이터 필터링
    const validData = trainingData.filter(
      (data) => data.instruction.trim() && data.output.trim()
    )

    if (validData.length === 0) {
      alert('최소 하나의 학습 데이터가 필요합니다.')
      return
    }

    setIsTraining(true)
    setTrainingStatus('학습을 시작합니다...')

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.yeotaeho.kr'
      const response = await fetch(`${apiUrl}/api/qlora/train`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          training_data: validData,
          output_dir: './adapters/chat_training',
          num_epochs: 3,
          per_device_train_batch_size: 4,
          gradient_accumulation_steps: 4,
          learning_rate: 2e-4,
          warmup_steps: 100,
          logging_steps: 10,
          save_steps: 500,
          max_seq_length: 2048,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'API 요청 실패' }))
        throw new Error(errorData.detail || '학습 시작 실패')
      }

      const data = await response.json()
      setTrainingStatus(`✅ ${data.message}`)

      // 성공 메시지 표시 후 3초 뒤 닫기
      setTimeout(() => {
        setShowTraining(false)
        setTrainingStatus('')
        setTrainingData([{ instruction: '', input: '', output: '' }])
      }, 3000)
    } catch (error) {
      console.error('Training error:', error)
      setTrainingStatus(`❌ 오류: ${error instanceof Error ? error.message : '알 수 없는 오류'}`)
    } finally {
      setIsTraining(false)
    }
  }

  return (
    <div
      style={{
        width: '100%',
        maxWidth: '800px',
        height: '90vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '20px',
          backgroundColor: '#667eea',
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ fontWeight: 'bold', fontSize: '20px' }}>
          🤖 LangChain RAG Chatbot
        </div>
        <button
          onClick={() => setShowTraining(!showTraining)}
          style={{
            padding: '8px 16px',
            backgroundColor: showTraining ? '#5568d3' : 'rgba(255, 255, 255, 0.2)',
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'background-color 0.2s',
          }}
          onMouseOver={(e) => {
            if (!showTraining) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'
          }}
          onMouseOut={(e) => {
            if (!showTraining) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
          }}
        >
          📚 {showTraining ? '학습 닫기' : 'QLoRA 학습'}
        </button>
      </div>

      {/* Training Panel */}
      {showTraining && (
        <div
          style={{
            padding: '20px',
            backgroundColor: '#f8f9fa',
            borderBottom: '2px solid #e0e0e0',
            maxHeight: '300px',
            overflowY: 'auto',
          }}
        >
          <div style={{ marginBottom: '16px', fontWeight: 'bold', color: '#333' }}>
            QLoRA 파인튜닝 데이터 입력
          </div>

          {trainingData.map((data, index) => (
            <div
              key={index}
              style={{
                marginBottom: '16px',
                padding: '16px',
                backgroundColor: 'white',
                borderRadius: '8px',
                border: '1px solid #e0e0e0',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ fontWeight: 'bold', color: '#667eea' }}>
                  학습 데이터 #{index + 1}
                </div>
                {trainingData.length > 1 && (
                  <button
                    onClick={() => handleRemoveTrainingData(index)}
                    style={{
                      padding: '4px 12px',
                      backgroundColor: '#ff4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    삭제
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <input
                  type="text"
                  placeholder="지시사항 (필수) 예: 질문에 답하세요"
                  value={data.instruction}
                  onChange={(e) => handleTrainingDataChange(index, 'instruction', e.target.value)}
                  disabled={isTraining}
                  style={{
                    padding: '8px 12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    fontSize: '14px',
                  }}
                />
                <input
                  type="text"
                  placeholder="입력 (선택사항) 예: LangChain이란?"
                  value={data.input}
                  onChange={(e) => handleTrainingDataChange(index, 'input', e.target.value)}
                  disabled={isTraining}
                  style={{
                    padding: '8px 12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    fontSize: '14px',
                  }}
                />
                <textarea
                  placeholder="출력 (필수) 예: LangChain은 LLM 애플리케이션 개발을 위한 프레임워크입니다."
                  value={data.output}
                  onChange={(e) => handleTrainingDataChange(index, 'output', e.target.value)}
                  disabled={isTraining}
                  rows={2}
                  style={{
                    padding: '8px 12px',
                    border: '1px solid #e0e0e0',
                    borderRadius: '6px',
                    fontSize: '14px',
                    resize: 'vertical',
                  }}
                />
              </div>
            </div>
          ))}

          <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
            <button
              onClick={handleAddTrainingData}
              disabled={isTraining}
              style={{
                padding: '10px 20px',
                backgroundColor: isTraining ? '#ccc' : '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: 'bold',
                cursor: isTraining ? 'not-allowed' : 'pointer',
              }}
            >
              + 데이터 추가
            </button>
            <button
              onClick={handleStartTraining}
              disabled={isTraining || trainingData.every((d) => !d.instruction.trim() || !d.output.trim())}
              style={{
                padding: '10px 20px',
                backgroundColor:
                  isTraining || trainingData.every((d) => !d.instruction.trim() || !d.output.trim())
                    ? '#ccc'
                    : '#667eea',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: 'bold',
                cursor:
                  isTraining || trainingData.every((d) => !d.instruction.trim() || !d.output.trim())
                    ? 'not-allowed'
                    : 'pointer',
                flex: 1,
              }}
            >
              {isTraining ? '학습 중...' : '🚀 학습 시작'}
            </button>
          </div>

          {trainingStatus && (
            <div
              style={{
                marginTop: '12px',
                padding: '12px',
                backgroundColor: trainingStatus.includes('✅') ? '#d4edda' : '#f8d7da',
                color: trainingStatus.includes('✅') ? '#155724' : '#721c24',
                borderRadius: '6px',
                fontSize: '14px',
              }}
            >
              {trainingStatus}
            </div>
          )}
        </div>
      )}

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              textAlign: 'center',
              color: '#666',
              marginTop: '40px',
            }}
          >
            <p style={{ fontSize: '18px', marginBottom: '10px' }}>
              안녕하세요! RAG 방식의 챗봇입니다. 🚀
            </p>
            <p style={{ fontSize: '14px', color: '#999' }}>
              질문을 입력하면 벡터 데이터베이스에서 관련 정보를 검색하여 답변합니다.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: message.role === 'user' ? '#667eea' : '#f0f0f0',
                color: message.role === 'user' ? 'white' : '#333',
                wordWrap: 'break-word',
                whiteSpace: 'pre-wrap',
              }}
            >
              {message.content}
            </div>
          </div>
        ))}

        {isLoading && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-start',
            }}
          >
            <div
              style={{
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: '#f0f0f0',
                color: '#666',
              }}
            >
              생각 중...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        style={{
          padding: '20px',
          borderTop: '1px solid #e0e0e0',
          display: 'flex',
          gap: '10px',
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지를 입력하세요..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '12px 16px',
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            fontSize: '16px',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          style={{
            padding: '12px 24px',
            backgroundColor: isLoading || !input.trim() ? '#ccc' : '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
          }}
        >
          전송
        </button>
      </form>
    </div>
  )
}


