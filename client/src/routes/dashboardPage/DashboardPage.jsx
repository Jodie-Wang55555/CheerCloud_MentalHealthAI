import { useMutation, useQueryClient } from '@tanstack/react-query'
import './dashboardPage.css'
import { useNavigate } from 'react-router-dom'

const DashboardPage = () => {

  const queryClient = useQueryClient()

  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: (text)=>{
      return fetch(`${import.meta.env.VITE_API_URL}/api/chats`, {
        method: "POST",
        credentials:"include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      }).then((res) => res.json());
    },
    onSuccess: (id) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["userchats"] })
      navigate(`/dashboard/chats/${id}`)
    },
  })

  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = e.target.text.value;
    if (!text) return;

    mutation.mutate(text);
  }
  return (
    <div className='dashboardPage'>
      <div className="texts">
        <div className="logo">
          <img src="/logo.png" alt="" />
          <h1>CheerCloud</h1>
        </div>
        <div className="options">
          <div className="option" onClick={() => mutation.mutate("I'd like to start a mental wellness check")}>
            <img src="/chat.png" alt="Mental Wellness" />
            <h3>Mental Wellness Check</h3>
            <p>Share your feelings and get personalized support to improve your mental well-being.</p>
          </div>

          <div className="option" onClick={() => mutation.mutate("Can you guide me through a relaxation exercise?")}>
            <img src="/image.png" alt="Relaxation" />
            <h3>Guided Relaxation</h3>
            <p>Practice mindfulness with calming exercises designed to reduce stress and anxiety.</p>
          </div>

          <div className="option" onClick={() => mutation.mutate("Give me a daily affirmation")}>
            <img src="/code.png" alt="Affirmations" />
            <h3>Daily Affirmations</h3>
            <p>Start your day with positive, uplifting messages to boost your confidence and mood.</p>
          </div>
        </div>
      </div>
      <div className="formContainer">
        <form onSubmit={handleSubmit}>
          <input type="text" name="text" placeholder='Ask me anything...' autoComplete="new-password"  />
          <button>
            <img src="/arrow1.png" alt="" />
          </button>
        </form>
      </div>
    </div>
  )
}

export default DashboardPage