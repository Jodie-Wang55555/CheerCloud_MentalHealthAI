import { useEffect, useRef, useState } from "react";
import "./newPrompt.css";
import Upload from "../upload/Upload";
import { IKImage } from "imagekitio-react";
import { callCheerCloudAI } from "../../lib/gemini";
import Markdown from "react-markdown";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigationType } from "react-router-dom";

const NewPrompt = ({ data }) => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const [img, setImg] = useState({
    isLoading: false,
    error: "",
    dbData: {},
    aiData: {},
  });

  const endRef = useRef(null);
  const formRef = useRef(null);

  useEffect(() => {
    endRef.current.scrollIntoView({ behavior: "smooth" });
  }, [data, question, answer, img.dbData]);

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => {
      return fetch(`${import.meta.env.VITE_API_URL}/api/chats/${data._id}`, {
        method: "PUT",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: question.length ? question : undefined,
          answer,
          img: img.dbData?.filePath || undefined,
        }),
      }).then((res) => res.json());
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient
        .invalidateQueries({ queryKey: ["chat", data._id] })
        .then(() => {
          formRef.current.reset();
          setQuestion("");
          setAnswer("");
          setImg({
            isLoading: false,
            error: "",
            dbData: {},
            aiData: {},
          });
        });
    },
    onError: (err) => {
      console.log(err);
    },
  });

  const add = async (text, isInitial) => {
    if (!isInitial) setQuestion(text);

    try {
      // Call AI (no streaming)
      const responseText = await callCheerCloudAI(text);
      
      // UI layer typewriter effect
      setAnswer("");
      for (let i = 0; i < responseText.length; i++) {
        await new Promise((resolve) => setTimeout(resolve, 20));
        setAnswer(responseText.slice(0, i + 1));
      }
      
      console.log("✅ Rendering Complete");
      mutation.mutate();
    } catch (err) {
      console.error("❌ AI Call Error:", err);
      
      // User-friendly error message displayed in chat history
      let friendlyMessage = "Sorry, I'm having trouble responding right now. 💜";
      
      if (err.message && err.message.includes("quota")) {
        friendlyMessage = "I've reached my daily chat limit. Please try again tomorrow, or contact support for more help. 💜";
      } else if (err.message && err.message.includes("network")) {
        friendlyMessage = "Connection issue detected. Please check your internet and try again. 💜";
      }
      
      // Set error message as answer and save to chat history
      setAnswer(friendlyMessage);
      mutation.mutate();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const text = e.target.text.value;
    if (!text) {
      return;
    }

    add(text, false);
  };

  // IN PRODUCTION WE DON'T NEED IT
  const hasRun = useRef(false);
  useEffect(() => {
    if (!hasRun.current) {
      if (data?.history?.length === 1) {
        add(data.history[0]?.parts[0]?.text, true);
      }
    }
    hasRun.current = true;
  }, []);

  return (
    <>
      {/* ADD NEW CHAT */}
      {img.isLoading && <div className="">Loading...</div>}
      {img.dbData?.filePath && (
        <IKImage
          urlEndpoint={import.meta.env.VITE_IMAGE_KIT_ENDPOINT}
          path={img.dbData?.filePath}
          width="300"
          transformation={[{ width: "380" }]}
        />
      )}
      <div className="endChat" ref={endRef}></div>
      <form className="newForm" onSubmit={handleSubmit} ref={formRef}>
        <Upload setImg={setImg} />
        <input id="file" type="file" multiple={false} hidden />
        <input type="text" name="text" placeholder="Ask me anything..." autoComplete="new-password"  />
        <button>
          <img src="/arrow1.png" alt="" />
        </button>
      </form>
    </>
  );
};

export default NewPrompt;
