import { useState } from "react";
import Login from "./components/login";
import RegisterForm from "./components/registerform";
import PackageSearch from "./components/packagesearch";
import PackageDetails from "./components/packagedetails";

const API_URL = "http://127.0.0.1:8001";

function App() {
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [pkg, setPkg] = useState(null);

  // errors come as a plain string, but the validation (422) ones come as a list
  function showError(data) {
    if (data.detail === "Invalid or expired token") {
      setToken("");
    }
    if (typeof data.detail === "string") {
      setMessage(data.detail);
    } else {
      setMessage(data.detail[0].loc[1] + ": " + data.detail[0].msg);
    }
  }

  // login gives back the access token, every other request sends it in the "token" header
  function login(username, password) {
    // runs post method from /login endpoint, the username and password go in the body
    fetch(API_URL + "/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username, password: password }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.detail) {
          showError(data);
        } else {
          setMessage("");
          setToken(data.access_token);
        }
      });
  }

  function logout() {
    setToken("");
    setPkg(null);
    setMessage("");
  }

  // E1 registers a new package, it is pending unless the status says otherwise
  function addPackage(name, destination, weight, arrivalDate, status) {
    // runs post method from /packages endpoint, the package details go in the body
    fetch(API_URL + "/packages", {
      method: "POST",
      headers: { "Content-Type": "application/json", token: token },
      body: JSON.stringify({
        name: name,
        destination: destination,
        weight: Number(weight),
        arrival_date: arrivalDate,
        status: status,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.detail) {
          showError(data);
        } else {
          setMessage("Package registered with ID " + data.id);
        }
      });
  }

  // E2 gets one package, saved in pkg for the Package details section
  function showPackage(id) {
    // runs get method from /packages/{id} endpoint
    fetch(API_URL + "/packages/" + id, { headers: { token: token } })
      .then((response) => response.json())
      .then((data) => {
        if (data.detail) {
          setPkg(null);
          showError(data);
        } else {
          setMessage("");
          setPkg(data);
        }
      });
  }

  if (token === "") {
    return (
      <>
        <p><b>{message}</b></p>
        <Login onLogin={login} />
      </>
    );
  }

  return (
    <>
      <h1>Warehouse Dispatch</h1>
      <button onClick={logout}>Log out</button>
      <p><b>{message}</b></p>
      <RegisterForm onAdd={addPackage} />
      <PackageSearch onSearch={showPackage} />
      <PackageDetails pkg={pkg} />
    </>
  );
}

export default App;