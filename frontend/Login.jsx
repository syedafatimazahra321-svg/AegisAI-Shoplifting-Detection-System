import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();

  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPass, setShowPass] = useState(false);

  // Updated handleSubmit with debugging logs and strict validation guards
  const handleSubmit = () => {
    console.log("Button clicked");
    console.log("Username:", username);
    console.log("Password:", password);

    if (mode === "login") {
      if (username.trim() === "admin" && password.trim() === "admin123") {
        console.log("Navigating...");
        navigate("/dashboard");
      } else {
        alert("Wrong username/password");
      }
    }

    if (mode === "signup") {
      if (!username || !password || !confirmPassword) {
        alert("Fill all fields");
        return;
      }

      if (password !== confirmPassword) {
        alert("Passwords don't match");
        return;
      }

      alert("Signup successful");
      setMode("login");
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">

        {/* Logo */}
        <div className="brand">
          <div className="shield">🛡</div>

          <div>
            <span>AegisAI</span>
            <p className="subtitle">
              Enterprise Anti-Theft Surveillance Portal
            </p>
          </div>
        </div>

        <h2>{mode === "login" ? "Login" : "Sign Up"}</h2>

        {/* Username */}
        <div className="input-box">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>

        {/* Password */}
        <div className="input-box">
          <input
            type={showPass ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <span onClick={() => setShowPass(!showPass)}>👁</span>
        </div>

        {/* Signup extra */}
        {mode === "signup" && (
          <div className="input-box">
            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
        )}

        {/* Updated Button to fix any execution/binding bugs */}
        <button onClick={() => handleSubmit()}>
          {mode === "login" ? "LOGIN" : "SIGN UP"}
        </button>

        {mode === "login" ? (
          <>
            <div className="forgot">Forgot Password?</div>

            <div className="switch-mode">
              Don’t have an account?
              <span onClick={() => setMode("signup")}> Sign Up</span>
            </div>
          </>
        ) : (
          <div className="switch-mode">
            Already have an account?
            <span onClick={() => setMode("login")}> Login</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default Login;