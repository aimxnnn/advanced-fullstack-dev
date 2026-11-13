import { useState } from "react";

function RegisterForm({ onAdd }) {
  const [name, setName] = useState("");
  const [destination, setDestination] = useState("");
  const [weight, setWeight] = useState("");
  const [arrivalDate, setArrivalDate] = useState("");
  const [status, setStatus] = useState("pending");

  return (
    <>
      <h2>Register a package</h2>
      <p>
        Name: <input value={name} onChange={(e) => setName(e.target.value)} />
      </p>
      <p>
        Destination: <input value={destination} onChange={(e) => setDestination(e.target.value)} />
      </p>
      <p>
        Weight (kg): <input value={weight} onChange={(e) => setWeight(e.target.value)} />
      </p>
      <p>
        Arrival date: <input type="date" value={arrivalDate} onChange={(e) => setArrivalDate(e.target.value)} />
      </p>
      <p>
        Status: <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="pending">pending</option>
          <option value="dispatched">dispatched</option>
        </select>
      </p>
      <button onClick={() => onAdd(name, destination, weight, arrivalDate, status)}>Register package</button>
    </>
  );
}

export default RegisterForm;