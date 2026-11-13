import { useState } from "react";

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  return (
    <>
      <h1>Login</h1>
      <p>
        Username: <input value={username} onChange={(e) => setUsername(e.target.value)} />
      </p>
      <p>
        Password: <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </p>
      <button onClick={() => onLogin(username, password)}>Log in</button>
    </>
  );
}

export default Login;