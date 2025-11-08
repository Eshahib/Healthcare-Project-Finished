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
          console.log("this runs");
          navigate("/symptoms");
        }
      })
      .catch(() => {
        // Not logged in
      });
  }, [onAuthSuccess, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-tr from-purple-600 to-blue-500 flex flex-col justify-center items-center px-4">
      <div className="bg-white rounded-xl shadow-lg p-12 max-w-md w-full text-center">
        <h1 className="text-4xl font-bold mb-6 text-gray-900">Welcome to Symptom Checker</h1>
        <p className="text-gray-600 mb-8">
          Please log in with your Google account to continue.
        </p>
        <button
          onClick={googleLogin}
          className="w-full bg-gradient-to-r from-purple-600 to-blue-500 text-white font-semibold py-3 rounded-lg shadow-md hover:brightness-110 transition"
        >
          Login with Google
        </button>
      </div>
      <footer className="mt-12 text-white opacity-75">
        &copy; 2025 Your Company Name. All rights reserved.
      </footer>
    </div>
  );
}