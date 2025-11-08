import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getToken, getCurrentUser, type UserResponse } from '@/lib/api'


interface User {
  username: string;
  email: string;
}

interface AuthPageProps {
  onAuthSuccess: (user: UserResponse) => void;
}

export default function AuthPage({ onAuthSuccess }: AuthPageProps) {
  const navigate = useNavigate();

  const googleLogin = () => {
    window.location.href = "http://localhost:8000/api/login"; // Adjust to backend OAuth login URL
  };

  useEffect(() => {
    // On mount, check if user is already logged in by calling backend
    fetch("http://localhost:8000/api/me", {
      method: "GET",
      credentials: "include",
    })
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json();
          onAuthSuccess(data.user);
          navigate("/symptoms");
        }
      })
      .catch(() => {
        // Not logged in
      });
  }, [onAuthSuccess, navigate]);

  return (
    <div>
      <h2>Please log in</h2>
      <button onClick={googleLogin}>Login with Google</button>
    </div>
  );
}